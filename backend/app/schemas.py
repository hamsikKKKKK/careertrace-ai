from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

class EvidenceInput(Input):
    type: Literal['user_note', 'meeting_note'] = 'user_note'
    source_url: str = Field(default='', max_length=2000)
    excerpt: str = Field(min_length=1, max_length=10000)
    author: str = Field(default='', max_length=200)
    @field_validator('source_url')
    @classmethod
    def safe_url(cls, value):
        if value:
            u = urlsplit(value)
            if u.scheme not in ('http', 'https') or not u.hostname or u.username:
                raise ValueError('http 또는 https 근거 URL만 가능합니다.')
        return value

class ExperienceInput(Input):
    title: str = Field(min_length=1, max_length=200)
    category: Literal['팀 프로젝트', '개인 프로젝트', '공모전', '대외활동', '아르바이트', '인턴', '기타'] = '팀 프로젝트'
    period: str = Field(default='', max_length=100)
    situation: str = Field(default='', max_length=5000)
    task: str = Field(default='', max_length=5000)
    action: str = Field(default='', max_length=5000)
    result: str = Field(default='', max_length=5000)
    lessons: str = Field(default='', max_length=5000)
    skills: list[str] = Field(default_factory=list, max_length=20)
    confirmed: bool = False
    source_batch_id: str | None = None
    source_candidate_id: str | None = None
    evidence: list[EvidenceInput] = Field(default_factory=list, max_length=20)

class GithubInput(Input):
    url: str = Field(default='', max_length=2000)
    sample: bool = False

class NoteInput(Input):
    text: str = Field(min_length=1, max_length=20000)

class ApplicationInput(Input):
    company_name: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=5000)
    job_description: str = Field(default='', max_length=10000)
    character_limit: int | None = Field(default=None, ge=1, le=10000)

class DraftInput(Input):
    application_id: str
    experience_id: str

class DraftEdit(Input):
    content: str = Field(min_length=1, max_length=20000)
