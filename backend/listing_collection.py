"""Selected-source collection. Structured JSON-LD now; model extraction can be added later."""
import ipaddress
import json
import os
import socket
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import httpx
from pydantic import ValidationError
from .errors import Problem
from .listing_models import VacancyInput, https_url
from .listing_service import identity, stamp

AGENT = 'UpShiftVacancyBot'
MAX_BYTES = 1_000_000


class FetchFailure(Exception):
    def __init__(self, code): self.code = code


class SourceFetcher:
    def __init__(self, hosts=None, client=None, resolver=None):
        self.hosts = set(hosts if hosts is not None else
                         filter(None, (h.strip().lower() for h in os.getenv('UPSHIFT_SOURCE_HOSTS', '').split(','))))
        self.client = client
        self.resolver = resolver or socket.getaddrinfo

    def validate(self, url):
        url = https_url(url)
        host = urlsplit(url).hostname
        if host not in self.hosts:
            raise FetchFailure('host_not_allowlisted')
        try:
            addresses = self.resolver(host, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise FetchFailure('non_public_address')
        except OSError:
            raise FetchFailure('dns_unavailable')
        return url

    def _read(self, client, url):
        self.validate(url)
        try:
            with client.stream('GET', url) as response:
                # Redirects need operator review; never follow into another destination.
                if 300 <= response.status_code < 400: raise FetchFailure('redirect_requires_review')
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_BYTES: raise FetchFailure('response_too_large')
                return response.status_code, data.decode('utf-8', errors='replace')
        except httpx.HTTPError:
            raise FetchFailure('network_error')

    def fetch(self, url):
        url = self.validate(url)
        def fetch_with(client):
            parts = urlsplit(url)
            robot_url = f'https://{parts.netloc}/robots.txt'
            status, robots = self._read(client, robot_url)
            if status != 404:
                if status != 200: raise FetchFailure('robots_unavailable')
                parser = RobotFileParser()
                parser.parse(robots.splitlines())
                if not parser.can_fetch(AGENT, url): raise FetchFailure('robots_disallowed')
                delay = parser.crawl_delay(AGENT)
                # One-shot runner cannot honour long crawling delays; require a suitable adapter.
                if delay and delay > 0: raise FetchFailure('crawl_delay_requires_adapter')
            return self._read(client, url)
        if self.client is not None: return fetch_with(self.client)
        with httpx.Client(timeout=10, follow_redirects=False, trust_env=False,
                          headers={'User-Agent': AGENT + '/0.1'}) as client:
            return fetch_with(client)


class StructuredHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capture = False
        self.current = []
        self.scripts = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.capture = dict(attrs).get('type', '').split(';')[0].lower() == 'application/ld+json'
            self.current = []
    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.scripts.append(''.join(self.current)); self.capture = False
    def handle_data(self, data):
        if self.capture: self.current.append(data)
        self.text.append(data)


def plain(value):
    if not isinstance(value, str): return ''
    parser = StructuredHTML()
    parser.feed(value)
    return ' '.join(unescape(' '.join(parser.text)).split())


def extract_jsonld(content, page_url):
    """Return validated early-career drafts and a count of records requiring another adapter."""
    parser = StructuredHTML()
    parser.feed(content)
    blobs = parser.scripts or [content]
    jobs, skipped = [], 0
    def walk(node, depth=0):
        if depth > 20: return
        if isinstance(node, list):
            for item in node[:250]: walk(item, depth+1)
        elif isinstance(node, dict):
            kind = node.get('@type', [])
            if kind == 'JobPosting' or (isinstance(kind, list) and 'JobPosting' in kind): jobs.append(node)
            else:
                for value in node.values(): walk(value, depth+1)
    for blob in blobs[:100]:
        try: walk(json.loads(blob))
        except (ValueError, RecursionError): skipped += 1
    results = []
    for job in jobs[:100]:
        if len(jobs) > 1 and not job.get('url'):
            skipped += 1; continue
        title = plain(job.get('title'))
        lower = title.lower()
        level = ('student_attachment' if 'attach' in lower else 'internship' if 'intern' in lower else
                 'graduate_trainee' if 'graduate' in lower or 'trainee' in lower else
                 'entry_level' if 'junior' in lower or 'entry' in lower else None)
        if level is None:
            skipped += 1; continue
        location = job.get('jobLocation', {})
        if isinstance(location, list): location = location[0] if location else {}
        address = location.get('address', {}) if isinstance(location, dict) else {}
        if isinstance(address, str): place = address
        elif isinstance(address, dict):
            place = ', '.join(str(address[k]) for k in ('addressLocality', 'addressRegion', 'addressCountry') if address.get(k))
        else: place = ''
        if not place and job.get('jobLocationType') == 'TELECOMMUTE':
            place = 'Remote; country eligibility requires review'
        skills = job.get('skills', [])
        if isinstance(skills, str): skills = [s.strip() for s in skills.split(',') if s.strip()]
        eligibility = plain(job.get('qualifications'))
        requirements = plain(job.get('experienceRequirements'))
        responsibilities = plain(job.get('responsibilities'))
        try:
            results.append(VacancyInput(
                title=title, location=place or 'Location requires review', description=plain(job.get('description')),
                source_url=urljoin(page_url, job.get('url') or page_url), career_level=level,
                skills=skills, eligibility=[eligibility] if eligibility else [],
                requirements=[requirements] if requirements else [],
                responsibilities=[responsibilities] if responsibilities else [],
                deadline=job['validThrough'][:10] if isinstance(job.get('validThrough'), str) else None))
        except (ValueError, TypeError, ValidationError): skipped += 1
    return results, skipped


class SourceCollector:
    def __init__(self, service, fetcher=None):
        self.service, self.store = service, service.store
        self.fetcher = fetcher or SourceFetcher()

    def save_source(self, company_id, body):
        self.service.company(company_id)
        try: self.fetcher.validate(body.url)
        except FetchFailure as exc: raise Problem(422, 'invalid_source', exc.code)
        source_id = identity(company_id, body.url)
        row = dict(body.model_dump(), id=source_id, company_id=company_id, updated_at=stamp())
        return self.store.transact([], lambda _: ({('vacancy_sources', source_id): row}, row))

    def collect(self, source_id):
        source = self.store.get('vacancy_sources', source_id)
        if not source: raise Problem(404, 'source_not_found', 'Source not found.')
        company = self.service.company(source['company_id'])
        if not source['enabled'] or company['status'] != 'approved':
            raise Problem(409, 'source_disabled', 'Enable the source and approve the company first.')
        report = dict(id=source_id, checked_at=stamp(), result='needs_adapter', drafts=0, skipped=0)
        try:
            status, content = self.fetcher.fetch(source['url'])
            if status in (404, 410):
                # Only this exact source advert is affected. Absence from a directory is not proof of closure.
                self.service.mark_unavailable(identity(company['id'], source['url']), f'Source returned HTTP {status}; review required.')
                report['result'] = 'unavailable'
            elif status != 200:
                report['result'] = f'http_{status}'
            else:
                drafts, skipped = extract_jsonld(content, source['url'])
                for body in drafts:
                    fingerprint = identity(json.dumps(body.model_dump(mode='json'), sort_keys=True))
                    self.service.submit(company['id'], company['owner_uid'], body, origin='collected',
                                        source_id=source_id, source_fingerprint=fingerprint)
                report.update(result='collected' if drafts else 'needs_adapter', drafts=len(drafts), skipped=skipped)
        except FetchFailure as exc:
            report['result'] = exc.code
        # Keep operator configuration intact if it changed during this run.
        key = ('vacancy_sources', source_id)
        def change(rows):
            return {key: {**rows[key], 'last_run': report}}, report
        return self.store.transact([key], change)

    def run(self):
        reports, cursor = [], ''
        while True:
            page = self.store.list('vacancy_sources', after=cursor, limit=100)
            for source in page['items']:
                if source['enabled']:
                    try: reports.append(self.collect(source['id']))
                    except Problem as exc: reports.append({'id': source['id'], 'result': exc.code})
            cursor = page['next_cursor']
            if not cursor: break
        return {'sources': reports, 'expired': self.service.expire()}
