import os
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sqlalchemy import select
from .database import database
from .models import Experience, Evidence, SourceBatch, JobApplication, ExperienceMatch, Draft, DraftEvidenceLink
from .schemas import ExperienceInput, GithubInput, NoteInput, ApplicationInput, DraftInput, DraftEdit
from .engine import skills_for, organize_note, candidates_for, analyze_question, match_experiences, build_draft
from .github import fetch_repository, sample_repository

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')

def row(obj):
    return {col.name:getattr(obj,col.name) for col in obj.__table__.columns}

def experience_json(obj):
    return row(obj) | {'evidence':[row(e) for e in obj.evidence]}

def application_json(obj):
    return row(obj) | {'matches':[m.detail for m in obj.matches]}

def require(session, model, id):
    obj = session.get(model,id)
    if obj is None:
        raise HTTPException(404, '저장된 항목을 찾을 수 없습니다.')
    return obj

def draft_json(session, obj):
    application = require(session, JobApplication, obj.application_id)
    return row(obj) | {'links':[row(link) | {'evidence':row(require(session,Evidence,link.evidence_id))} for link in obj.links],
                      'application':application_json(application)}

def create_app(database_url=None):
    # Windows registry MIME associations may label JS as text/plain.
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('text/css', '.css')
    engine, sessions = database(database_url or os.getenv('DATABASE_URL'))
    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()
    app = FastAPI(title='CareerTrace AI · 규칙 기반 데모', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],
                       allow_methods=['GET','POST','PUT'], allow_headers=['Content-Type'])
    def db():
        with sessions() as session:
            yield session

    @app.get('/api/health')
    def health():
        return {'status':'ok','analysis_mode':'demo','llm_enabled':False}

    @app.get('/api/experiences')
    def experiences(session=Depends(db)):
        return [experience_json(e) for e in session.scalars(select(Experience).order_by(Experience.created_at.desc()))]

    @app.get('/api/experiences/{id}')
    def get_experience(id: str, session=Depends(db)):
        return experience_json(require(session,Experience,id))

    def apply_experience(data, exp, session):
        values = data.model_dump(exclude={'confirmed','evidence','source_batch_id','source_candidate_id'})
        for key,value in values.items():
            setattr(exp,key,value)
        exp.skills = list(dict.fromkeys(data.skills + skills_for(' '.join([data.title,data.situation,data.task,data.action,data.result]))))[:20]
        if data.confirmed and not data.action:
            raise HTTPException(422, '본인이 수행한 행동을 입력한 뒤 확인해 주세요.')
        exp.verification_status = 'user_confirmed' if data.confirmed else 'needs_confirmation'

    @app.post('/api/experiences', status_code=201)
    def add_experience(data: ExperienceInput, session=Depends(db)):
        exp = Experience(is_sample=False)
        apply_experience(data, exp, session)
        sources = []
        if bool(data.source_batch_id) != bool(data.source_candidate_id):
            raise HTTPException(422, '분석 결과와 경험 후보를 함께 선택해 주세요.')
        if data.source_batch_id:
            batch = require(session,SourceBatch,data.source_batch_id)
            candidate = next((c for c in batch.payload['candidates'] if c['id']==data.source_candidate_id),None)
            if not candidate:
                raise HTTPException(404, '선택한 분석 결과에 없는 경험 후보입니다.')
            sources = candidate['evidence']
            exp.is_sample = batch.payload['is_sample']
        exp.evidence = [Evidence(**item) for item in sources] + [Evidence(**e.model_dump()) for e in data.evidence]
        session.add(exp)
        session.commit()
        return experience_json(exp)

    @app.put('/api/experiences/{id}')
    def edit_experience(id: str, data: ExperienceInput, session=Depends(db)):
        exp = require(session,Experience,id)
        apply_experience(data, exp, session)
        # Existing immutable source evidence stays attached. New notes are appended.
        exp.evidence.extend(Evidence(**e.model_dump()) for e in data.evidence)
        session.commit()
        return experience_json(exp)

    @app.post('/api/notes/organize')
    def organize(data: NoteInput):
        return organize_note(data.text)

    @app.post('/api/github/analyze')
    def github(data: GithubInput, session=Depends(db)):
        source = sample_repository() if data.sample else fetch_repository(data.url)
        payload = source | {'candidates':candidates_for(source), 'mode':'demo'}
        batch = SourceBatch(payload=payload)
        session.add(batch)
        session.commit()
        return payload | {'batch_id':batch.id}

    @app.post('/api/applications', status_code=201)
    def add_application(data: ApplicationInput, session=Depends(db)):
        obj = JobApplication(**data.model_dump(), analysis=analyze_question(data.question,data.job_description))
        candidates = list(session.scalars(select(Experience).order_by(Experience.created_at.desc())))
        obj.matches = [ExperienceMatch(experience_id=m['experience_id'],detail=m) for m in match_experiences(obj,candidates)]
        session.add(obj)
        session.commit()
        return application_json(obj)

    @app.get('/api/applications')
    def applications(session=Depends(db)):
        return [application_json(a) for a in session.scalars(select(JobApplication).order_by(JobApplication.created_at.desc()))]

    @app.get('/api/drafts')
    def drafts(session=Depends(db)):
        return [draft_json(session,d) for d in session.scalars(select(Draft).order_by(Draft.created_at.desc()))]

    @app.get('/api/drafts/{id}')
    def get_draft(id: str, session=Depends(db)):
        return draft_json(session,require(session,Draft,id))

    @app.post('/api/drafts', status_code=201)
    def add_draft(data: DraftInput, session=Depends(db)):
        application = require(session,JobApplication,data.application_id)
        exp = require(session,Experience,data.experience_id)
        if exp.verification_status != 'user_confirmed':
            raise HTTPException(409, '경험 상세에서 본인 활동과 작성 내용을 먼저 확인해 주세요.')
        content, statements, warnings = build_draft(exp,application.character_limit)
        if not content:
            raise HTTPException(422, '글자 수 제한 안에 담을 문장이 없습니다. 경험 문장을 줄이거나 제한을 늘려 주세요.')
        draft = Draft(application_id=application.id,experience_id=exp.id,content=content,
                      character_count=len(content),is_sample=exp.is_sample,warnings=warnings)
        draft.links = [DraftEvidenceLink(evidence_id=e.id,claim_text=s) for s in statements for e in exp.evidence]
        session.add(draft)
        session.commit()
        return draft_json(session,draft)

    @app.put('/api/drafts/{id}')
    def edit_draft(id: str, data: DraftEdit, session=Depends(db)):
        draft = require(session,Draft,id)
        application = require(session,JobApplication,draft.application_id)
        if application.character_limit and len(data.content)>application.character_limit:
            raise HTTPException(422, f'글자 수 제한 {application.character_limit}자를 초과했습니다. 공백·줄바꿈 포함 기준입니다.')
        changed = data.content != draft.content
        draft.content = data.content
        draft.character_count = len(data.content)
        # Conservatively invalidate ALL links on edits: substring matches can change claim meaning.
        if changed:
            draft.links = []
            draft.warnings = list(dict.fromkeys(draft.warnings + ['편집된 초안입니다. 자동 근거 연결을 해제했습니다. 원본 경험 자료와 대조해 주세요.']))
        draft.verification_status = 'needs_review'
        session.commit()
        return draft_json(session,draft)

    dist = ROOT / 'frontend' / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist,html=True),name='frontend')
    return app
