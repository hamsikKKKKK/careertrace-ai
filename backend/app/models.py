from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def uid():
    return str(uuid4())

def now():
    return datetime.now(timezone.utc).isoformat()

class Base(DeclarativeBase):
    pass

class Experience(Base):
    __tablename__ = 'experiences'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str]
    category: Mapped[str]
    period: Mapped[str] = mapped_column(default='')
    situation: Mapped[str] = mapped_column(Text, default='')
    task: Mapped[str] = mapped_column(Text, default='')
    action: Mapped[str] = mapped_column(Text, default='')
    result: Mapped[str] = mapped_column(Text, default='')
    lessons: Mapped[str] = mapped_column(Text, default='')
    skills: Mapped[list] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(default='needs_confirmation')
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(default=now)
    evidence: Mapped[list['Evidence']] = relationship(cascade='all, delete-orphan', lazy='selectin')

class Evidence(Base):
    __tablename__ = 'evidence'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    experience_id: Mapped[str] = mapped_column(ForeignKey('experiences.id'))
    type: Mapped[str]
    source_url: Mapped[str] = mapped_column(default='')
    excerpt: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(default='')
    verification_status: Mapped[str] = mapped_column(default='linked')
    created_at: Mapped[str] = mapped_column(default=now)

class SourceBatch(Base):
    __tablename__ = 'source_batches'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    payload: Mapped[dict] = mapped_column(JSON)

class JobApplication(Base):
    __tablename__ = 'applications'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    company_name: Mapped[str]
    job_title: Mapped[str]
    question: Mapped[str] = mapped_column(Text)
    job_description: Mapped[str] = mapped_column(Text, default='')
    character_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analysis: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
    matches: Mapped[list['ExperienceMatch']] = relationship(cascade='all, delete-orphan', lazy='selectin')

class ExperienceMatch(Base):
    __tablename__ = 'matches'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    application_id: Mapped[str] = mapped_column(ForeignKey('applications.id'))
    experience_id: Mapped[str] = mapped_column(ForeignKey('experiences.id'))
    detail: Mapped[dict] = mapped_column(JSON)

class Draft(Base):
    __tablename__ = 'drafts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    application_id: Mapped[str] = mapped_column(ForeignKey('applications.id'))
    experience_id: Mapped[str] = mapped_column(ForeignKey('experiences.id'))
    content: Mapped[str] = mapped_column(Text)
    character_count: Mapped[int]
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(default='needs_review')
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(default=now)
    links: Mapped[list['DraftEvidenceLink']] = relationship(cascade='all, delete-orphan', lazy='selectin')

class DraftEvidenceLink(Base):
    __tablename__ = 'draft_links'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    draft_id: Mapped[str] = mapped_column(ForeignKey('drafts.id'))
    evidence_id: Mapped[str] = mapped_column(ForeignKey('evidence.id'))
    claim_text: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(default='linked')
