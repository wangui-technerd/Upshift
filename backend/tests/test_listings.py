import json
import unittest
from datetime import date, timedelta
import httpx
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.errors import Problem
from backend.listing_store import MemoryStore
from backend.listing_service import ListingService, identity
from backend.listing_models import CompanyInput, SourceInput, VacancyInput
from backend.listing_collection import SourceCollector, SourceFetcher, FetchFailure, extract_jsonld


class Claims:
    configured = True
    def verify_claims(self, token):
        if token not in ('partner', 'other', 'admin'): raise Problem(401, 'unauthorized', 'Invalid token.')
        return {'uid': token, 'upshift_admin': token == 'admin'}
    def verify(self, token): return self.verify_claims(token)['uid']


def advert(**overrides):
    return dict(title='Software developer intern', location='Nairobi, Kenya',
                description='Build and test software with an engineering mentor.',
                source_url='https://careers.example.org/job/one', career_level='internship',
                eligibility=['Continuing computing student or recent graduate.'], skills=['Python', 'Git'], **overrides)


class ListingApiTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.client = TestClient(create_app(token_verifier=Claims(), listing_store=self.store))
        self.addCleanup(self.client.close)
        self.company = self.call('post', '/companies', {'name': 'Test company', 'website': 'https://example.org'}).json()

    def call(self, method, path, body=None, token='partner'):
        return getattr(self.client, method)('/listings'+path, json=body,
                headers={'Authorization': 'Bearer '+token}) if method != 'get' else self.client.get(
                '/listings'+path, headers={'Authorization': 'Bearer '+token})

    def approve(self):
        return self.call('post', f"/admin/companies/{self.company['id']}/review", {'approved': True}, 'admin')

    def submit(self, body=None):
        return self.call('post', f"/companies/{self.company['id']}/vacancies", body or advert())

    def publish(self, row):
        return self.call('post', f"/admin/submissions/{row['id']}/review",
                         {'revision': row['revision'], 'decision': 'publish', 'note': 'Eligibility and source reviewed.'}, 'admin')

    def test_partner_cannot_approve_or_submit_for_someone_else(self):
        self.assertEqual(self.call('post', f"/admin/companies/{self.company['id']}/review", {'approved': True}).status_code, 403)
        self.assertEqual(self.submit().status_code, 403)
        self.assertEqual(self.approve().status_code, 200)
        self.assertEqual(self.call('post', f"/companies/{self.company['id']}/vacancies", advert(), 'other').status_code, 403)
        self.assertEqual(self.call('get', '/companies/mine', token='other').json()['items'], [])

    def test_full_publish_update_and_withdraw_journey(self):
        self.approve()
        row = self.submit().json()
        self.assertEqual(self.call('get', '/vacancies').json()['items'], [])
        self.assertEqual(self.publish(row).status_code, 200)
        self.assertEqual(len(self.call('get', '/vacancies').json()['items']), 1)
        # Duplicate requests keep the same ID and do not unpublish reviewed content.
        duplicate = self.submit().json()
        self.assertEqual(duplicate['id'], row['id'])
        self.assertEqual(duplicate['status'], 'published')
        updated = advert(); updated['title'] = 'Updated internship title'
        revised = self.submit(updated).json()
        self.assertEqual(self.call('get', '/vacancies').json()['items'], [])
        self.assertEqual(self.publish(row).status_code, 409)
        self.assertEqual(self.publish(revised).status_code, 200)
        self.assertEqual(self.call('post', f"/submissions/{row['id']}/withdraw", token='other').status_code, 403)
        self.assertEqual(self.call('post', f"/submissions/{row['id']}/withdraw").status_code, 200)
        self.assertEqual(self.store.get('opportunities', row['id'])['availability_status'], 'archived')
        self.assertEqual(self.call('get', '/vacancies').json()['items'], [])

    def test_past_deadline_and_missing_eligibility_cannot_be_published(self):
        self.approve()
        body = advert(); body['deadline'] = (date.today()-timedelta(days=2)).isoformat()
        self.assertEqual(self.publish(self.submit(body).json()).status_code, 409)
        body['deadline'] = None; body['eligibility'] = []
        self.assertEqual(self.publish(self.submit(body).json()).status_code, 409)

    def test_suspension_withdraws_published_vacancies(self):
        self.approve(); row = self.submit().json(); self.publish(row)
        self.call('post', f"/admin/companies/{self.company['id']}/review", {'approved': False}, 'admin')
        self.assertEqual(self.store.get('opportunities', row['id'])['availability_status'], 'archived')
        self.assertEqual(self.submit().status_code, 403)

    def test_url_validation_extra_fields_and_tracking_dedup(self):
        self.approve()
        body = advert(); body['owner_uid'] = 'admin'
        self.assertEqual(self.submit(body).status_code, 422)
        body = advert(); body['source_url'] = 'javascript:alert(1)'
        self.assertEqual(self.submit(body).status_code, 422)
        one = self.submit().json()
        body = advert(); body['source_url'] += '?utm_source=mail#apply'
        self.assertEqual(self.submit(body).json()['id'], one['id'])

    def test_admin_can_correct_extracted_draft_and_no_private_projection(self):
        self.approve(); row = self.submit().json()
        body = advert(); body['eligibility'] = ['Confirmed graduate eligibility.']
        corrected = self.call('put', f"/admin/submissions/{row['id']}", body, 'admin')
        self.assertEqual(corrected.status_code, 200)
        self.publish(corrected.json())
        public = self.call('get', '/vacancies').json()['items'][0]
        self.assertNotIn('owner_uid', public)
        self.assertNotIn('reviewed_by', public)
        self.assertTrue(public['ready_for_live_application'])

    def test_auth_and_pagination(self):
        self.assertEqual(self.client.get('/listings/vacancies').status_code, 401)
        self.assertEqual(self.call('get', '/admin/submissions').status_code, 403)
        for i in range(3): self.call('post', '/companies', {'name': f'Company {i}', 'website': 'https://example.org'})
        first = self.call('get', '/companies/mine?limit=2').json()
        second = self.call('get', '/companies/mine?limit=2&after='+first['next_cursor']).json()
        self.assertEqual(len(first['items'])+len(second['items']), 4)
        self.assertTrue(set(r['id'] for r in first['items']).isdisjoint(r['id'] for r in second['items']))


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(); self.service = ListingService(self.store)
        self.company = self.service.register('partner', CompanyInput(name='Test employer', website='https://example.org'))
        self.service.approve_company(self.company['id'], 'admin', True)

    def html(self):
        return '<script type="application/ld+json">'+json.dumps({'@context': 'https://schema.org',
            '@type': 'JobPosting', 'title': 'Data analyst intern', 'description': '<p>Help prepare and analyse research data.</p>',
            'url': 'https://example.org/jobs/one', 'skills': 'SQL, Python',
            'qualifications': 'Final-year computing student.',
            'jobLocation': {'address': {'addressLocality': 'Nairobi', 'addressCountry': 'Kenya'}}})+'</script>'

    def test_jsonld_extraction_and_no_invented_fields(self):
        rows, skipped = extract_jsonld(self.html(), 'https://example.org/jobs/one')
        self.assertEqual(len(rows), 1); self.assertEqual(skipped, 0)
        self.assertEqual(rows[0].skills, ['SQL', 'Python'])
        self.assertIsNone(rows[0].deadline); self.assertIsNone(rows[0].application_url)
        self.assertEqual(rows[0].location, 'Nairobi, Kenya')
        self.assertEqual(extract_jsonld('<p>Unstructured careers page.</p>', 'https://example.org')[0], [])

    def test_collection_is_idempotent_and_never_auto_publishes(self):
        class Fetcher:
            validate = lambda _, url: url
            fetch = lambda _, url: (200, self.html())
        collector = SourceCollector(self.service, Fetcher())
        source = collector.save_source(self.company['id'], SourceInput(url='https://example.org/jobs/one', enabled=True))
        first = collector.collect(source['id']); collector.collect(source['id'])
        self.assertEqual(first['drafts'], 1)
        submissions = self.store.list('listing_submissions')['items']
        self.assertEqual(len(submissions), 1); self.assertEqual(submissions[0]['revision'], 1)
        self.assertEqual(self.store.list('opportunities')['items'], [])

    def test_unchanged_collection_preserves_operator_corrections(self):
        class Fetcher:
            validate = lambda _, url: url
            fetch = lambda _, url: (200, self.html())
        collector = SourceCollector(self.service, Fetcher())
        source = collector.save_source(self.company['id'], SourceInput(url='https://example.org/jobs/one', enabled=True))
        collector.collect(source['id'])
        row = self.store.list('listing_submissions')['items'][0]
        body = VacancyInput(**{**row['payload'], 'eligibility': ['Verified final-year student eligibility.']})
        corrected = self.service.submit(self.company['id'], 'partner', body,
                                       origin='collected', source_id=source['id'], actor_uid='admin')
        collector.collect(source['id'])
        after = self.store.get('listing_submissions', row['id'])
        self.assertEqual(after['payload']['eligibility'], body.eligibility)
        self.assertEqual(after['revision'], corrected['revision'])

    def test_missing_exact_advert_hides_existing_projection(self):
        body = VacancyInput(**advert()); body.source_url = 'https://example.org/jobs/one'
        row = self.service.submit(self.company['id'], 'partner', body)
        from backend.listing_models import ReviewInput
        self.service.review(row['id'], 'admin', ReviewInput(revision=1, decision='publish', note='Source reviewed.'))
        class Fetcher:
            validate = lambda _, url: url
            fetch = lambda _, url: (410, '')
        collector = SourceCollector(self.service, Fetcher())
        source = collector.save_source(self.company['id'], SourceInput(url=body.source_url, enabled=True))
        self.assertEqual(collector.collect(source['id'])['result'], 'unavailable')
        self.assertEqual(self.store.get('opportunities', row['id'])['availability_status'], 'availability_unverified')

    def test_network_guards_robots_redirects_and_size(self):
        def dns(*args, **kwargs): return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]
        import socket
        def check(handler):
            client = httpx.Client(transport=httpx.MockTransport(handler))
            self.addCleanup(client.close)
            return SourceFetcher({'example.org'}, client=client, resolver=dns)
        fetcher = check(lambda req: httpx.Response(200, text='User-agent: *\nDisallow: /'))
        with self.assertRaises(FetchFailure) as caught: fetcher.fetch('https://example.org/jobs')
        self.assertEqual(caught.exception.code, 'robots_disallowed')
        with self.assertRaises(FetchFailure): fetcher.validate('https://unapproved.example/jobs')
        private = SourceFetcher({'example.org'}, resolver=lambda *a, **k: [(2, 1, 6, '', ('127.0.0.1', 443))])
        with self.assertRaises(FetchFailure): private.validate('https://example.org/jobs')
        for response in (httpx.Response(302, headers={'location': 'http://127.0.0.1'}),
                         httpx.Response(200, content=b'x'*1_000_001)):
            fetcher = check(lambda req: httpx.Response(404) if req.url.path == '/robots.txt' else response)
            with self.assertRaises(FetchFailure): fetcher.fetch('https://example.org/jobs')


if __name__ == '__main__': unittest.main()
