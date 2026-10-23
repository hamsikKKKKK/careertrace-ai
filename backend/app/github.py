import os
import re
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException

def repository_name(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc.lower() != 'github.com' or u.query or u.fragment:
        raise HTTPException(422, 'https://github.com/소유자/저장소 형식의 공개 저장소 URL을 입력해 주세요.')
    path = u.path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if not re.fullmatch(r'/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', path):
        raise HTTPException(422, '저장소 기본 URL을 입력해 주세요. 이슈·커밋 상세 URL은 지원하지 않습니다.')
    return path.lstrip('/')

def fetch_repository(url, client=None):
    name = repository_name(url)
    headers = {'Accept':'application/vnd.github+json', 'X-GitHub-Api-Version':'2022-11-28', 'User-Agent':'CareerTrace-local'}
    token = os.getenv('GITHUB_TOKEN', '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    owned = client is None
    client = client or httpx.Client(timeout=20, follow_redirects=False)
    def get(path, params=None):
        try:
            response = client.get(f'https://api.github.com/repos/{name}{path}', headers=headers, params=params)
        except httpx.RequestError:
            raise HTTPException(502, 'GitHub에 연결하지 못했습니다. 네트워크를 확인하고 다시 시도해 주세요.')
        if response.status_code in (403,429):
            raise HTTPException(429, 'GitHub 호출 제한 또는 접근 제한입니다. 잠시 후 다시 시도하거나 GITHUB_TOKEN을 설정해 주세요.')
        if response.status_code == 404:
            raise HTTPException(404, '공개 저장소를 찾을 수 없습니다. URL과 공개 여부를 확인해 주세요.')
        if response.status_code == 409 and path == '/commits':
            return []
        if response.status_code != 200:
            raise HTTPException(502, f'GitHub 조회 실패(상태 {response.status_code}). 저장소 이동 여부도 확인해 주세요.')
        return response.json()
    try:
        repo = get('')
        if repo.get('private'):
            raise HTTPException(422, 'MVP는 공개 저장소만 지원합니다.')
        activities = []
        commits = get('/commits', {'per_page':20})
        prs = get('/pulls', {'state':'all','sort':'updated','direction':'desc','per_page':10})
        issues = get('/issues', {'state':'all','sort':'updated','direction':'desc','per_page':20})
        for c in commits:
            activities.append(dict(type='github_commit', source_url=c['html_url'],
                excerpt=c['commit']['message'][:10000], author=(c.get('author') or {}).get('login') or c['commit']['author'].get('name','미상')))
        for kind, items in [('github_pr',prs),('github_issue',[i for i in issues if 'pull_request' not in i])]:
            for item in items:
                activities.append(dict(type=kind, source_url=item['html_url'],
                    excerpt=(item['title'] + '\n' + (item.get('body') or ''))[:10000],
                    author=(item.get('user') or {}).get('login','미상')))
        groups = [[a for a in activities if a['type']==kind] for kind in ['github_commit','github_pr','github_issue']]
        ordered = [group[i] for i in range(max(map(len,groups), default=0)) for group in groups if i < len(group)]
        return dict(repository=repo['full_name'], url=repo['html_url'], activities=ordered, is_sample=False,
                    notice='최근 커밋 최대 20개·PR 10개·이슈 조회 20개(PR 제외). 전체 이력이나 개인 기여도 분석이 아닙니다.')
    finally:
        if owned:
            client.close()

def sample_repository():
    return dict(repository='샘플 / 캠퍼스 일정 관리', url='', is_sample=True,
        notice='가상 시연 자료입니다. 실제 GitHub 저장소·성과가 아닙니다.',
        activities=[dict(type='user_note', source_url='', author='샘플 작성자', excerpt=text) for text in [
            'fix: API 오류 처리 개선\n[가상 샘플] 일정 조회 오류를 조사하고 예외 처리 로직을 수정한 활동 기록입니다.',
            'docs: 팀 API 명세 정리\n[가상 샘플] 팀 회의에서 API 요청·응답 형식을 문서로 정리한 활동 기록입니다.',
            'test: 일정 생성 테스트 추가\n[가상 샘플] 일정 생성 기능에 입력값 검증 테스트를 추가한 기록입니다.']])
