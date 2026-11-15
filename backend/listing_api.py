from fastapi import APIRouter, Depends, Query
from pydantic import Field
from .errors import Problem
from .listing_models import CompanyInput, VacancyInput, ReviewInput, SourceInput, StrictBody
from .listing_service import ListingService
from .listing_collection import SourceCollector


class CompanyDecision(StrictBody):
    approved: bool = Field(strict=True)


def listing_router(store, actor, admin, collector=None):
    router = APIRouter(prefix='/listings', tags=['Vacancies and partners'])
    service = ListingService(store)
    collector = collector or SourceCollector(service)

    @router.post('/companies', status_code=201)
    def register(body: CompanyInput, claims=Depends(actor)):
        return service.register(claims['uid'], body)

    @router.get('/companies/mine')
    def my_companies(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                     limit: int = Query(default=50, ge=1, le=100), claims=Depends(actor)):
        return store.list('partner_companies', owner=claims['uid'], after=after, limit=limit)

    @router.get('/companies')
    def companies(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                  limit: int = Query(default=50, ge=1, le=100), claims=Depends(actor)):
        page = store.list('companies', after=after, limit=limit)
        page['items'] = [row for row in page['items'] if row['status'] == 'approved']
        return page

    @router.post('/companies/{company_id}/vacancies', status_code=201)
    def submit(company_id: str, body: VacancyInput, claims=Depends(actor)):
        return service.submit(company_id, claims['uid'], body)

    @router.get('/submissions/mine')
    def mine(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
             limit: int = Query(default=50, ge=1, le=100), claims=Depends(actor)):
        return store.list('listing_submissions', owner=claims['uid'], after=after, limit=limit)

    @router.post('/submissions/{listing_id}/withdraw')
    def withdraw(listing_id: str, claims=Depends(actor)):
        return service.withdraw(listing_id, claims['uid'])

    @router.get('/vacancies')
    def vacancies(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                  limit: int = Query(default=50, ge=1, le=100), claims=Depends(actor)):
        from .listing_service import listing_day
        today = listing_day().isoformat()
        page = store.list('opportunities', after=after, limit=limit)
        def visible(row):
            company = store.get('partner_companies', row.get('company_id', '_'))
            return (row.get('availability_status') == 'published' and company and company['status'] == 'approved'
                    and (not row.get('deadline') or row['deadline'][:10] >= today))
        page['items'] = [row for row in page['items'] if visible(row)]
        return page

    @router.get('/admin/companies')
    def review_companies(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                         limit: int = Query(default=50, ge=1, le=100), claims=Depends(admin)):
        return store.list('partner_companies', after=after, limit=limit)

    @router.post('/admin/companies/{company_id}/review')
    def review_company(company_id: str, body: CompanyDecision, claims=Depends(admin)):
        return service.approve_company(company_id, claims['uid'], body.approved)

    @router.get('/admin/submissions')
    def submissions(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                    limit: int = Query(default=50, ge=1, le=100), claims=Depends(admin)):
        return store.list('listing_submissions', after=after, limit=limit)

    @router.put('/admin/submissions/{listing_id}')
    def edit(listing_id: str, body: VacancyInput, claims=Depends(admin)):
        row = store.get('listing_submissions', listing_id)
        if not row: raise Problem(404, 'listing_not_found', 'Submission not found.')
        if body.source_url != row['payload']['source_url']:
            raise Problem(409, 'source_changed', 'Submit a new vacancy when changing its canonical source URL.')
        return service.submit(row['company_id'], row['owner_uid'], body,
                              origin=row['origin'], source_id=row.get('source_id'), actor_uid=claims['uid'])

    @router.post('/admin/submissions/{listing_id}/review')
    def review(listing_id: str, body: ReviewInput, claims=Depends(admin)):
        return service.review(listing_id, claims['uid'], body)

    @router.post('/admin/companies/{company_id}/sources', status_code=201)
    def source(company_id: str, body: SourceInput, claims=Depends(admin)):
        return collector.save_source(company_id, body)

    @router.get('/admin/sources')
    def sources(after: str = Query(default='', pattern=r'^[a-zA-Z0-9_-]{0,100}$'),
                limit: int = Query(default=50, ge=1, le=100), claims=Depends(admin)):
        return store.list('vacancy_sources', after=after, limit=limit)

    @router.post('/admin/sources/{source_id}/collect')
    def collect(source_id: str, claims=Depends(admin)):
        return collector.collect(source_id)

    @router.post('/admin/expire')
    def expire(claims=Depends(admin)):
        return {'expired': service.expire()}

    return router
