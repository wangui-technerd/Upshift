from datetime import date
from typing import Literal
from urllib.parse import urlsplit, urlunsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator


def https_url(value):
    value = value.strip()
    p = urlsplit(value)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Use an HTTPS URL without credentials or a custom port.')
    # Fragments and campaign tracking do not identify a separate vacancy.
    from urllib.parse import parse_qsl, urlencode
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in ('gh_src', 'source')]
    return urlunsplit(('https', p.netloc.lower(), p.path or '/', urlencode(sorted(query)), ''))


class StrictBody(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class CompanyInput(StrictBody):
    name: str = Field(min_length=2, max_length=160)
    website: str = Field(max_length=2048)
    description: str = Field(default='', max_length=3000)
    offerings: list[Literal['vacancies', 'training', 'mentorship']] = Field(default_factory=lambda: ['vacancies'], min_length=1, max_length=3)

    @field_validator('website')
    @classmethod
    def website_url(cls, value): return https_url(value)


class VacancyInput(StrictBody):
    title: str = Field(min_length=3, max_length=200)
    location: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=20, max_length=20000)
    source_url: str = Field(max_length=2048)
    application_url: str | None = Field(default=None, max_length=2048)
    career_level: Literal['student_attachment', 'internship', 'graduate_trainee', 'entry_level']
    arrangement: str = Field(default='', max_length=160)
    skills: list[str] = Field(default_factory=list, max_length=40)
    responsibilities: list[str] = Field(default_factory=list, max_length=30)
    requirements: list[str] = Field(default_factory=list, max_length=30)
    eligibility: list[str] = Field(default_factory=list, max_length=30)
    deadline: date | None = None
    minimum_experience_months: int | None = Field(default=None, ge=0, le=1200, strict=True)

    @field_validator('source_url')
    @classmethod
    def canonical_source(cls, value):
        return https_url(value)

    @field_validator('application_url')
    @classmethod
    def application_destination(cls, value):
        if not value:
            return None
        https_url(value)
        return value

    @field_validator('skills', 'responsibilities', 'requirements', 'eligibility')
    @classmethod
    def text_lists(cls, values):
        if any(not s.strip() or len(s) > 2000 for s in values):
            raise ValueError('List entries must contain 1–2000 characters.')
        return list(dict.fromkeys(s.strip() for s in values))


class ReviewInput(StrictBody):
    revision: int = Field(ge=1, strict=True)
    decision: Literal['publish', 'reject', 'close']
    note: str = Field(min_length=5, max_length=2000)


class SourceInput(StrictBody):
    url: str = Field(max_length=2048)
    enabled: bool = False
    # Structured advert extraction works now; free-text/AI extraction is a future adapter.
    extractor: Literal['jsonld'] = 'jsonld'

    @field_validator('url')
    @classmethod
    def source_url(cls, value): return https_url(value)
