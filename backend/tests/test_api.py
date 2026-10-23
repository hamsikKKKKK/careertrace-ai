import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.github import fetch_repository


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as c:
        yield c


def experience(client, **overrides):
    body = dict(title='오류 해결', category='팀 프로젝트', situation='API 오류가 발생했습니다.',
                task='오류 원인 분석을 맡았습니다.', action='로그를 확인하고 예외 처리를 수정했습니다.',
                result='동일 요청을 다시 실행해 정상 응답을 확인했습니다.', confirmed=True,
                evidence=[dict(type='user_note', excerpt='직접 확인한 작업 기록', author='본인')])
    return client.post('/api/experiences', json=body | overrides)


def application(client, **overrides):
    return client.post('/api/applications', json=dict(company_name='테스트기업', job_title='개발자',
        question='문제를 해결한 경험을 설명해주세요.', character_limit=700) | overrides).json()


def test_saved_experience_persists_across_app_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'persist.db'}"
    with TestClient(create_app(url)) as c:
        assert experience(c).status_code == 201
    with TestClient(create_app(url)) as c:
        items = c.get('/api/experiences').json()
        assert len(items) == 1
        assert items[0]['action'] == '로그를 확인하고 예외 처리를 수정했습니다.'
        assert items[0]['evidence'][0]['excerpt'] == '직접 확인한 작업 기록'


def test_unconfirmed_cannot_generate_draft(client):
    exp = experience(client, confirmed=False).json()
    app = application(client)
    response = client.post('/api/drafts', json={'application_id': app['id'], 'experience_id': exp['id']})
    assert response.status_code == 409
    assert exp['verification_status'] == 'needs_confirmation'


def test_draft_only_uses_confirmed_text_and_links_and_edit_invalidates_links(client):
    exp = experience(client).json()
    app = application(client)
    draft = client.post('/api/drafts', json={'application_id': app['id'], 'experience_id': exp['id']}).json()
    assert '로그를 확인하고 예외 처리를 수정했습니다.' in draft['content']
    assert '30%' not in draft['content']
    assert draft['links'] and draft['links'][0]['evidence_id'] == exp['evidence'][0]['id']
    assert all(x['verification_status'] == 'linked' for x in draft['links'])
    updated = client.put(f"/api/drafts/{draft['id']}", json={'content': '새로 작성한 확인되지 않은 문장입니다.'}).json()
    assert updated['links'] == []
    assert updated['verification_status'] == 'needs_review'


def test_character_limit_enforced_generation_and_edit(client):
    exp = experience(client).json()
    app = application(client, character_limit=60)
    draft = client.post('/api/drafts', json={'application_id': app['id'], 'experience_id': exp['id']}).json()
    assert 0 < len(draft['content']) <= 60
    response = client.put(f"/api/drafts/{draft['id']}", json={'content': '가' * 61})
    assert response.status_code == 422
    assert client.get(f"/api/drafts/{draft['id']}").json()['content'] == draft['content']


def test_sample_marker_survives_generation(client):
    candidates = client.post('/api/github/analyze', json={'sample': True}).json()
    assert candidates['is_sample'] is True
    candidate = candidates['candidates'][0]
    exp = experience(client, source_batch_id=candidates['batch_id'], source_candidate_id=candidate['id']).json()
    assert exp['is_sample'] is True
    app = application(client)
    draft = client.post('/api/drafts', json={'application_id': app['id'], 'experience_id': exp['id']}).json()
    assert draft['is_sample'] is True


def test_matching_empty_and_max_three(client):
    app = application(client)
    assert app['matches'] == []
    for n in range(5):
        experience(client, title=f'오류 해결 {n}')
    app = application(client)
    assert len(app['matches']) == 3
    assert all('문제 해결' in x['related_skills'] for x in app['matches'])


@pytest.mark.parametrize('url', ['http://localhost/admin', 'https://github.com.evil.org/a/b', 'https://github.com/a/b/issues', 'file:///test'])
def test_invalid_github_url_rejected(client, url):
    assert client.post('/api/github/analyze', json={'url': url}).status_code == 422


def test_foreign_candidate_not_accepted(client):
    response = experience(client, source_batch_id='missing', source_candidate_id='other')
    assert response.status_code == 404


def test_empty_text_and_dangerous_evidence_rejected(client):
    assert experience(client, title='   ').status_code == 422
    assert experience(client, evidence=[dict(type='user_note', excerpt='text', source_url='javascript:alert(1)')]).status_code == 422


def test_unknown_ids_return_404(client):
    assert client.get('/api/experiences/missing').status_code == 404
    assert client.get('/api/drafts/missing').status_code == 404


@pytest.mark.parametrize('code,expected', [(404,404),(403,429),(429,429),(500,502)])
def test_github_errors_are_actionable(code, expected):
    def handler(request):
        return httpx.Response(code, json={'message':'upstream error'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as remote:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            fetch_repository('https://github.com/test/repo', remote)
        assert exc.value.status_code == expected


def test_github_preserves_author_and_does_not_claim_ownership():
    def handler(request):
        path = request.url.path
        if path.endswith('/commits'):
            return httpx.Response(200, json=[{'sha':'abc','html_url':'https://github.com/test/repo/commit/abc',
                'author':{'login':'someone-else'},'commit':{'message':'fix: timeout','author':{'name':'Other'}}}])
        if path.endswith('/pulls') or path.endswith('/issues'):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={'full_name':'test/repo','private':False,'html_url':'https://github.com/test/repo'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as remote:
        result = fetch_repository('https://github.com/test/repo', remote)
    assert result['activities'][0]['author'] == 'someone-else'
    assert result['activities'][0]['excerpt'] == 'fix: timeout'


def test_windows_mime_mapping_cannot_break_frontend(tmp_path, monkeypatch):
    import mimetypes
    import app.main as module
    dist = tmp_path / 'frontend' / 'dist'
    dist.mkdir(parents=True)
    (dist / 'app.js').write_text('export default 1', encoding='utf-8')
    mimetypes.add_type('text/plain', '.js')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    with TestClient(create_app(f"sqlite:///{tmp_path / 'mime.db'}")) as c:
        response = c.get('/app.js')
        assert response.status_code == 200
        assert 'javascript' in response.headers['content-type']


def test_edit_recomputes_inferred_skills(client):
    exp = experience(client, title='팀 협업', situation='팀 회의', action='팀 협업').json()
    assert '협업' in exp['skills']
    result = client.put('/api/experiences/'+exp['id'], json={
        'title':'개인 기록','category':'개인 프로젝트','action':'책을 읽었습니다.', 'confirmed':True}).json()
    assert '협업' not in result['skills']
