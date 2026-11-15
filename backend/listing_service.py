"""Partner ownership, moderation and public projections in atomic transactions."""
import hashlib
from datetime import datetime, timezone, date
from uuid import uuid4
from zoneinfo import ZoneInfo
from .errors import Problem
from .listing_models import https_url


def stamp(): return datetime.now(timezone.utc).isoformat()
def listing_day(): return datetime.now(ZoneInfo('Africa/Nairobi')).date()
def identity(*parts): return hashlib.sha256('\n'.join(parts).encode()).hexdigest()[:32]


class ListingService:
    def __init__(self, store): self.store = store

    def company(self, company_id, uid=None):
        row = self.store.get('partner_companies', company_id)
        if not row: raise Problem(404, 'company_not_found', 'Company not found.')
        if uid is not None and row['owner_uid'] != uid:
            raise Problem(403, 'forbidden', 'This company belongs to another account.')
        return row

    def register(self, uid, body):
        company_id = uuid4().hex
        row = dict(body.model_dump(), id=company_id, owner_uid=uid, status='pending', created_at=stamp())
        return self.store.transact([], lambda _: ({('partner_companies', company_id): row}, row))

    def approve_company(self, company_id, admin_uid, approved):
        key = ('partner_companies', company_id)
        audit_id = uuid4().hex
        def change(rows):
            row = rows[key]
            if not row: raise Problem(404, 'company_not_found', 'Company not found.')
            row.update(status='approved' if approved else 'suspended', reviewed_by=admin_uid, reviewed_at=stamp())
            public = {k: row[k] for k in ('id', 'name', 'website', 'description', 'offerings', 'status')}
            return {key: row, ('companies', company_id): public,
                    ('listing_audit', audit_id): dict(id=audit_id, actor=admin_uid, action='company_review',
                        company_id=company_id, approved=approved, at=stamp())}, row
        result = self.store.transact([key], change)
        if not approved:
            self.expire()
        return result

    def submit(self, company_id, uid, body, *, origin='partner', source_id=None, actor_uid=None, source_fingerprint=None):
        company_key = ('partner_companies', company_id)
        listing_id = identity(company_id, https_url(body.source_url))
        key = ('listing_submissions', listing_id)
        public_key = ('opportunities', listing_id)
        audit_id = uuid4().hex
        payload = body.model_dump(mode='json')
        def change(rows):
            company = rows[company_key]
            if not company or company['owner_uid'] != uid:
                raise Problem(403, 'forbidden', 'This company belongs to another account.')
            if company['status'] != 'approved':
                raise Problem(403, 'company_not_approved', 'Company verification is required before submitting vacancies.')
            old = rows[key]
            # Repeated identical collection must not unpublish an already-reviewed advert.
            unchanged_source = (origin == 'collected' and source_fingerprint and old
                                and old.get('source_fingerprint') == source_fingerprint)
            if old and ((old['payload'] == payload and old.get('origin') == origin) or unchanged_source):
                writes = {}
                if source_fingerprint and rows[public_key] and rows[public_key].get('availability_status') == 'published':
                    writes[public_key] = {**rows[public_key], 'last_checked_at': stamp()}
                return writes, old
            row = dict(id=listing_id, company_id=company_id, company=company['name'], owner_uid=uid,
                       payload=payload, origin=origin, source_id=source_id, status='pending',
                       revision=(old or {}).get('revision', 0)+1, updated_at=stamp(),
                       created_at=(old or {}).get('created_at', stamp()),
                       source_fingerprint=source_fingerprint or (old or {}).get('source_fingerprint'))
            writes = {key: row, ('listing_audit', audit_id): dict(id=audit_id, actor=actor_uid or uid, action='submit',
                        listing_id=listing_id, revision=row['revision'], at=stamp())}
            if rows[public_key]:
                writes[public_key] = {**rows[public_key], 'availability_status': 'pending_review',
                                      'ready_for_live_application': False}
            return writes, row
        return self.store.transact([company_key, key, public_key], change)

    def review(self, listing_id, admin_uid, body):
        # Find the immutable company ID; status is checked again inside the transaction.
        initial = self.store.get('listing_submissions', listing_id)
        if not initial: raise Problem(404, 'listing_not_found', 'Submission not found.')
        key = ('listing_submissions', listing_id)
        company_key = ('partner_companies', initial['company_id'])
        public_key = ('opportunities', listing_id)
        audit_id = uuid4().hex
        def change(rows):
            row, company = rows[key], rows[company_key]
            if not row: raise Problem(404, 'listing_not_found', 'Submission not found.')
            if row['revision'] != body.revision:
                raise Problem(409, 'revision_conflict', 'The advert changed. Review the latest revision.')
            if body.decision == 'publish':
                if not company or company['status'] != 'approved':
                    raise Problem(409, 'company_not_approved', 'Verify the company before publishing.')
                deadline = row['payload'].get('deadline')
                if deadline and date.fromisoformat(deadline) < listing_day():
                    raise Problem(409, 'deadline_passed', 'A past-deadline advert cannot be published.')
                if not row['payload']['eligibility']:
                    raise Problem(409, 'eligibility_missing', 'Add eligibility requirements before publishing.')
            status = {'publish': 'published', 'reject': 'rejected', 'close': 'closed'}[body.decision]
            row.update(status=status, reviewed_by=admin_uid, review_note=body.note, reviewed_at=stamp(),
                       revision=row['revision']+1)
            writes = {key: row, ('listing_audit', audit_id): dict(id=audit_id, actor=admin_uid,
                action=body.decision, listing_id=listing_id, revision=row['revision'], note=body.note, at=stamp())}
            if status == 'published':
                writes[public_key] = dict(row['payload'], id=listing_id, company_id=company['id'],
                    company=company['name'], company_website=company['website'], company_description=company['description'],
                    company_offerings=company['offerings'], availability_status='published', collected_date=stamp()[:10],
                    last_checked_at=stamp(), source_type=row['origin'], ready_for_live_application=True,
                    is_fictional=False, revision=row['revision'], research_notes='Reviewed by an UpShift operator. Confirm details in the source advert.',
                    skill_interpretation='Source-mentioned skills may include preferred tools and alternatives.')
            elif rows[public_key]:
                writes[public_key] = {**rows[public_key], 'availability_status': 'archived',
                                     'ready_for_live_application': False, 'closed_at': stamp()}
            return writes, row
        return self.store.transact([key, company_key, public_key], change)

    def withdraw(self, listing_id, uid):
        key, public_key = ('listing_submissions', listing_id), ('opportunities', listing_id)
        audit_id = uuid4().hex
        def change(rows):
            row = rows[key]
            if not row: raise Problem(404, 'listing_not_found', 'Submission not found.')
            if row['owner_uid'] != uid: raise Problem(403, 'forbidden', 'This listing belongs to another account.')
            row.update(status='closed', revision=row['revision']+1, updated_at=stamp())
            writes = {key: row, ('listing_audit', audit_id): dict(id=audit_id, actor=uid,
                       action='withdraw', listing_id=listing_id, at=stamp())}
            if rows[public_key]:
                writes[public_key] = {**rows[public_key], 'availability_status': 'archived',
                                      'ready_for_live_application': False, 'closed_at': stamp()}
            return writes, row
        return self.store.transact([key, public_key], change)

    def mark_unavailable(self, listing_id, reason):
        key = ('opportunities', listing_id)
        def change(rows):
            row = rows[key]
            if not row: return {}, None
            row.update(availability_status='availability_unverified', ready_for_live_application=False,
                       last_checked_at=stamp(), research_notes=reason)
            return {key: row}, row
        return self.store.transact([key], change)

    def expire(self):
        count, cursor = 0, ''
        while True:
            page = self.store.list('opportunities', after=cursor, limit=100)
            for row in page['items']:
                key = ('opportunities', row['id'])
                company_key = ('partner_companies', row.get('company_id', '_'))
                def change(rows):
                    current = rows[key]
                    company = rows[company_key]
                    deadline = (current or {}).get('deadline')
                    expired = deadline and date.fromisoformat(deadline[:10]) < listing_day()
                    suspended = current and current.get('company_id') and (not company or company['status'] != 'approved')
                    if current and current.get('availability_status') == 'published' and (expired or suspended):
                        current.update(availability_status='archived', ready_for_live_application=False, closed_at=stamp())
                        return {key: current}, True
                    return {}, False
                count += bool(self.store.transact([key, company_key], change))
            cursor = page['next_cursor']
            if not cursor: return count
