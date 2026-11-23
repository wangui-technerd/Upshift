"""Reproduce the manually researched listing snapshot, not a live vacancy scraper.

Summaries are paraphrases; missing facts remain unknown. No Firestore writes.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from listing_expansion import extend

ROOT = Path(__file__).resolve().parents[1]
COLLECTED = '2026-11-13'
ROWS = []


def add(company, title, location, sector, level, url, summary, skills=(), eligibility='',
        deadline=None, status='listed_on_source', source_type='employer', notes='', primary=None):
    ROWS.append(dict(company=company, title=title, location=location, sector=sector,
                     career_level=level, source_url=url, description=summary, skills=list(skills),
                     eligibility=[eligibility] if eligibility else [], deadline=deadline,
                     availability_status=status, source_type=source_type, research_notes=notes,
                     primary_source_url=primary))


W = 'https://work.ke/jobs/'
S = 'https://jobs.smartrecruiters.com/'
add('Aga Khan University', 'Intern - Human Resource', 'Nairobi, Kenya', 'Human resources', 'internship',
    W+'intern-human-resource-aga-khan-university-29053e',
    'Human-resource internship identified on the university careers feed; full duties and eligibility need direct-source review.',
    source_type='aggregator', status='needs_primary_review')
add('UN-Habitat', 'Intern - Data analytics', 'Nairobi, Kenya', 'Data', 'internship',
    W+'intern-data-analytics-united-nations-united-nations-human-settlements-programme-834d0e',
    'Support HR data preparation, workflow automation and Power BI reporting during a six-month unpaid internship.',
    ['Power BI','Data management','Microsoft Office'],
    'Graduate students, final-year undergraduates or graduates; Power BI proficiency and English required.',
    '2026-11-26T07:59:00+03:00', source_type='aggregator', status='needs_primary_review',
    notes='Deadline timezone reported by secondary source; verify on official advert.',
    primary='https://careers.un.org/jobSearchDescription/287931?language=en')
add('Valley Hospital', 'IT Intern', 'Nakuru, Kenya', 'IT operations', 'internship',
    W+'it-intern-valley-hospital-cb77e6',
    'Assist with hospital IT support, equipment setup, backups, user accounts and connectivity troubleshooting.',
    ['Networking','Excel','Google Workspace','Troubleshooting'],
    'Pursuing or recently completed an IT diploma or degree.', source_type='aggregator', status='needs_primary_review')
add('UNHCR', 'Administrative Intern', 'Nairobi, Kenya', 'Administration', 'internship',
    W+'administrative-intern-unhcr-87a692',
    'Administration internship offering experience in office management and support services.', [],
    'Current student or graduate within two years; at least two years of undergraduate study completed.',
    '2026-11-24T23:59:00+03:00', source_type='aggregator', status='needs_primary_review')
add('KKCO East Africa', 'Business Development Internship', 'Nairobi, Kenya', 'Business development', 'internship',
    W+'business-development-internship-kkco-east-africa-171c94',
    'Support client prospecting, market research, proposals and business-development records.',
    ['Research','CRM','Proposal writing'], 'Relevant business-related degree; proposal and CRM familiarity requested.',
    '2026-11-16T23:59:00+03:00', source_type='aggregator', status='needs_primary_review')
add('Frisco Engineers', 'Sales Engineers - Intern', 'Nairobi, Kenya', 'Engineering sales', 'internship',
    W+'sales-engineers-intern-frisco-engineers-4d5ad9',
    'Six-month placement supporting technical quotations, client visits and engineering equipment sales.',
    ['Excel','Communication','Numerical skills'], 'Relevant engineering degree, second-class upper or better; field visits required.',
    source_type='aggregator', status='needs_primary_review')
add('Sun King', 'Customer Support Intern - Regional Service Centers', 'Nairobi, Kenya', 'Customer service', 'internship',
    W+'customer-support-intern-regional-service-centers-sun-king-0eeae7',
    'Support aftersales requests, basic product troubleshooting, repair tracking and customer updates.',
    ['Communication','Customer service','CRM'], 'Relevant degree and 1–2 years in customer service or related work.',
    source_type='aggregator', status='needs_primary_review')
add('Busara Center for Behavioral Economics', 'Research, Advisory and Practice Intern', 'Nairobi, Kenya - Hybrid', 'Research', 'internship',
    W+'research-advisory-and-practice-intern-busara-center-for-behavioral-economics-a93766',
    'Assist behavioural-research projects, qualitative data analysis, reporting and knowledge sharing.',
    ['Research','Data analysis','Project management'], 'Final-semester undergraduate or master’s student in a relevant field.',
    source_type='aggregator', status='needs_primary_review',
    primary='https://jobs.lever.co/BusaraCenter/b09e2c42-17e0-4083-ab27-8872a95e3f1c')
add('Regen Organics', 'Accounting Intern', 'Nairobi, Kenya', 'Finance', 'internship',
    W+'accounting-intern-regen-organics-4e998b',
    'Help with reconciliations, accounting checks, journal accuracy and financial reporting.',
    ['Excel','Accounting','Financial reporting'], 'Studying or completed accounting, finance or a related discipline.',
    source_type='aggregator', status='needs_primary_review', notes='Advert attributed to recruitment agency Shortlist.')
add('Tatu City', 'Associate Financial Analyst - Intern', 'Tatu City, Kiambu, Kenya', 'Finance', 'internship',
    W+'associate-financial-analyst-intern-tatu-city-e5cf43',
    'Support financial models, property-development analysis and management presentations.',
    ['Excel','Financial modelling','Valuation'], 'Relevant quantitative or finance degree; 1–3 years of financial-analysis experience.',
    source_type='aggregator', status='needs_primary_review')
add('Greenwheels Electric Mobility', 'Customer Acquisition Intern', 'Nairobi, Kenya', 'Sales', 'internship',
    W+'customer-acquisition-intern-greenwheels-electric-mobility-3eea3a',
    'Contact prospective drivers, explain lease-to-own arrangements and maintain acquisition records.',
    ['Communication','Google Sheets','CRM'], 'Certificate, diploma or degree; confident telephone communication.',
    source_type='aggregator', status='needs_primary_review')
add('Jumba', 'Sales Intern (Telesales)', 'Nairobi, Kenya', 'Sales', 'internship',
    W+'sales-intern-telesales-jumba-819250',
    'Build customer relationships, execute sales plans and record feedback in sales systems.',
    ['Excel','Google Workspace','Communication'], 'At least three months of sales, customer-support or related experience.',
    source_type='aggregator', status='needs_primary_review')
add('Partech Partners', 'Partech Africa - Investment Analyst Intern - January 2027', 'Nairobi, Kenya', 'Investment', 'internship',
    W+'partech-africa-investment-analyst-intern-january-2027-partech-partners-1c6725',
    'Support startup screening, investment research, due diligence and investment memoranda.',
    ['Research','Writing','Financial analysis'], 'Master’s student in business/engineering; prior relevant investment or consulting experience.',
    source_type='aggregator', status='needs_primary_review')
add('Jubilee Insurance Kenya', 'Sales Intern', 'Multiple Kenyan towns', 'Sales', 'internship',
    W+'sales-intern-jubilee-insurance-kenya-28e12b',
    'Distribute life-insurance products, attend training and develop client relationships.',
    ['Digital skills','Sales'], 'Age 21+; certificate/diploma/degree and KCSE C-minus or better.',
    '2026-11-30T23:59:00+03:00', source_type='aggregator', status='needs_primary_review')
add('UNODC', 'Intern - Monitoring and Evaluation', 'Nairobi, Kenya', 'Research', 'internship',
    W+'intern-monitoring-and-evaluation-united-nations-united-nations-office-on-drugs-and-crime-768a08',
    'Six-month unpaid placement supporting programme data, results tracking, evaluation and reporting.',
    ['Data management','Research','Reporting'], deadline='2026-11-22T07:59:00+03:00',
    source_type='aggregator', status='needs_primary_review', notes='Eligibility and closing timezone need original-advert review.')
add('Tatu City', 'Financial Reporting Intern', 'Tatu City, Kiambu, Kenya', 'Finance', 'internship',
    W+'financial-reporting-intern-tatu-city-9582db',
    'Assist management reporting, budgeting, forecasts and financial-data reconciliation.',
    ['Excel','PowerPoint','ERP','Financial reporting'], 'Relevant degree, CPA/ACCA in progress and 0–2 years of related experience.',
    source_type='aggregator', status='needs_primary_review')
add('Tatu City', 'Electrical BIM Intern', 'Tatu City, Kiambu, Kenya', 'Engineering', 'internship',
    W+'electrical-bim-intern-tatu-city-5aeecc',
    'Help model electrical systems, prepare drawings and coordinate BIM designs.',
    ['Revit','AutoCAD','Electrical engineering'], 'Electrical-engineering undergraduate or recent graduate.',
    source_type='aggregator', status='needs_primary_review')
add('Senga', 'Software Engineer (Junior)', 'Nairobi, Kenya - On-site', 'Software', 'junior_with_experience',
    'https://senga.co/careers/software-engineer-junior',
    'Develop logistics web/mobile systems and APIs using the employer’s engineering stack.',
    ['Ruby on Rails','React','Git','Testing','Data structures','Algorithms'],
    'Relevant degree; advert normally asks three post-university years but considers exceptional early-career applicants.')
add('Senga', 'Intern, Operations', 'Nairobi, Kenya', 'Operations', 'internship',
    'https://senga.co/careers/intern-operations',
    'Provide operational and administrative support across a logistics startup.',
    ['Communication','Organisation'], 'Students or recent graduates; full-time availability required, incompatible with active class schedules.')
add('Senga', 'Customer Service Operations Associate', 'Nairobi, Kenya', 'Operations', 'early_career_with_experience',
    'https://senga.co/careers/customer-service-operations-associate',
    'Coordinate shipments, service customer accounts and maintain operational records.',
    ['Communication','Logistics','Organisation'], 'Degree-level education; advert has inconsistent experience wording, including a two-year minimum.',
    notes='Experience wording conflicts between the qualifications and must-have sections; do not simplify to zero experience.')
add('SALIX Data Africa Limited', 'AI and Automation Developer', 'Nairobi, Kenya', 'AI', 'experienced',
    S+'SALIXDataAfricaLimited/744000160916269-ai-and-automation-developer',
    'Build AI applications, business automations and enterprise integrations.',
    ['Python','APIs','Git','Testing','LLMs'], 'Three or more years developing production software; not an internship.')
add('SALIX Data Africa Limited', 'Software Engineer (PHP/Laravel)', 'Nairobi, Kenya', 'Software', 'experienced',
    S+'SALIXDataAfricaLimited/744000158522675-software-engineer-php-laravel-',
    'Develop web applications, REST APIs and relational-database services.',
    ['PHP','Laravel','SQL','REST APIs','Git','Testing'], 'Three to five years of professional PHP/Laravel development.')
add('Canonical', 'Graduate Software Engineer, Open Source and Linux, Canonical Ubuntu', 'Remote - Worldwide', 'Software', 'graduate',
    'https://canonical.com/careers/8249005/graduate-software-engineer-open-source-and-linux-canonical-ubuntu-remote',
    'Contribute to Linux and open-source engineering teams across the software stack.',
    ['Linux','Python','Go','Rust','C++','JavaScript'],
    'STEM degree with programming; application specifically targets first-degree completion in 2025 or 2026.',
    notes='Language alternatives are not all compulsory. International travel required; worldwide label does not guarantee local work eligibility.')
add('Canonical', 'Graduate Customer Success Manager', 'Remote - Worldwide', 'Customer success', 'graduate',
    'https://canonical.com/careers/6103331/graduate-customer-success-manager-remote',
    'Graduate customer-success opportunity supporting technology customers.', [],
    'About to graduate, recently graduated or no more than two years of work experience; international travel required.')
add('Canonical', 'Junior Ubuntu Software Engineer', 'Remote - Worldwide', 'Software', 'junior',
    W+'junior-ubuntu-software-engineer-canonical-b46363',
    'Contribute code, packaging, debugging and documentation to Ubuntu engineering.',
    ['Python','Rust','Go','C++','Testing'], source_type='aggregator', status='needs_primary_review',
    notes='Listed languages are alternatives, not a requirement to know every language.')
add('KEPRO', 'Data Analyst Intern (M&E & Impact Analytics)', 'Nairobi, Kenya', 'Data', 'internship',
    'https://kepro.zohorecruit.com/jobs/Careers/794151000002371023/Data-Analyst-Intern-M-E-Impact-Analytics-',
    'Data-analysis internship associated with monitoring, evaluation and impact measurement.', [],
    'Recent graduate within two years; relevant quantitative degree.', status='needs_primary_review',
    notes='Official URL resolves but body was unreadable; metadata from indexed official result, not full-advert verification.')
add('Alliance of Bioversity International and CIAT', 'INTERN - PABRA (RFP301446)', 'Nairobi, Kenya', 'Data', 'internship',
    'https://bioversityinternational.zohorecruit.eu/jobs/Careers/11911000016739803/RFP301446-INTERN-PABRA',
    'Support programme monitoring, data management, analysis, visualisation and reporting.', [],
    status='needs_primary_review', notes='Official page body unreadable; indexed official summary only. Detailed eligibility not retrieved.')
add('Riana Group', 'Junior Software Developer', 'Nairobi, Kenya', 'Software', 'junior_with_experience',
    W+'junior-software-developer-riana-group-c526d4',
    'Build and maintain web applications, database features and secure code.',
    ['Laravel','React','Next.js','C#','MySQL','MongoDB'], 'Relevant computing degree and at least two years of development experience.',
    source_type='aggregator', status='needs_primary_review')
add('Bidhaa Sasa', 'Junior Software Developer', 'Nairobi, Kenya', 'Software', 'junior',
    W+'junior-software-developer-bidhaa-sasa-a40f63',
    'Develop Salesforce applications and integrations with AWS and external systems.',
    ['Salesforce','AWS','Apex','Kotlin','Python','JavaScript'], source_type='aggregator', status='needs_primary_review',
    notes='Full minimum eligibility needs original recruitment-advert confirmation.')
add('UNEP', 'Data Analytics and Artificial Intelligence Intern', 'Nairobi, Kenya', 'Data', 'internship',
    'https://careers.un.org/jobSearchDescription/276836?language=en',
    'Historical UNEP data-analytics and AI internship; retained for prototype research only.', [],
    deadline='2026-05-18', status='archived', notes='Official indexed page says opening is no longer available.')
add('UN-Habitat', 'Knowledge Hub - Backend Web Developer Intern', 'Nairobi, Kenya - Hybrid', 'Software', 'internship',
    'https://careers.un.org/jobSearchDescription/271201?language=en',
    'Historical backend-web-development internship; full requirements were not retrievable.', [],
    deadline='2026-02-16', status='archived', notes='Official indexed page says opening is no longer available.')
add('UN-Habitat', 'Intern - Data analytics', 'Nairobi, Kenya - In-person', 'Data', 'internship',
    'https://careers.un.org/jobSearchDescription/271477?language=en',
    'Historical data-analytics internship, distinct from the November 2026 requisition.', [],
    deadline='2026-02-08', status='archived', notes='Official indexed page says opening is no longer available.')
add('Grab', 'Intern, Software Engineer Mobile', 'Petaling Jaya, Malaysia - On-site', 'Software', 'internship',
    S+'Grab/744000139433819-intern-software-engineer-mobile',
    'Historical software internship involving development, reviews and technical documentation.',
    ['Python','Go','Java','Kotlin','Swift','C++'], 'Pursuing a relevant computing degree; languages listed as alternatives.',
    status='archived', notes='Current employer page explicitly says expired; skills from indexed earlier advert.')
add('Nexthink', 'Software Engineer (Intern)', 'Madrid, Spain', 'Software', 'internship',
    S+'nexthink/744000159632929-software-engineer-intern',
    'Six-month engineering internship combining Java development, testing and AI-related work.',
    ['Java','Testing','AI'], notes='Kenyan applicant eligibility and work authorisation not verified.')
add('Kensington', 'BI/Data Analyst Intern', 'Toronto, Ontario, Canada', 'Data', 'internship',
    'https://job-boards.greenhouse.io/kensingtontours/jobs/5289223007',
    'Support analytics dashboards, SQL extraction and business-performance reporting.',
    ['SQL','Excel','Power BI','Python','Microsoft Fabric'], 'Students; coursework and project exposure accepted.',
    notes='Work authorisation not verified; some tools are exposure or learning opportunities, not mandatory mastery.')
add('Cermati.com', 'Software Engineer Intern', 'Location not confirmed in retrieved text', 'Software', 'internship',
    S+'Cermaticom/744000144011039-software-engineer-intern',
    'Contribute engineering projects, scripts, APIs and data-platform improvements with mentorship.',
    ['Python','Java','SQL','Airflow','BigQuery'], 'Third/final-year student or recent graduate; Bahasa and English communication.',
    notes='Some technologies are nice-to-have; location and international eligibility require review.')
add('NCS', '[Uni - Jan till Jun 2027] GenAI Software Engineer Intern', 'Location not confirmed in retrieved text', 'AI', 'internship',
    S+'NCS3/6000000001307002--uni-jan-till-jun-2027-genai-software-engineer-intern',
    'Help build AI engineering agents, automated testing and developer-platform prototypes.',
    ['LLMs','Testing','APIs','Documentation'], notes='Eligibility and location need full application review; dates in title are placement period, not closing date.')
add('NCS', '[Uni - Jan till Jun 2027] Software Engineering Intern (Low Code)', 'Location not confirmed in retrieved text', 'Software', 'internship',
    S+'NCS3/6000000001276848--uni-jan-till-jun-2027-software-engineering-intern-low-code-',
    'Assist low-code application development, systems integration, testing and documentation.',
    ['OutSystems','Testing','APIs','Java','JavaScript'], 'Pursuing a computing-related discipline; low-code experience advantageous, not mandatory.',
    notes='Programming-language exposure is preferred; location and work authorisation unverified.')
add('Western Digital', 'Summer 2027 Intern - Software Engineering', 'Multiple United States locations', 'Software', 'internship',
    S+'WesternDigital/744000138727213-summer-2027-software-engineering-internship',
    'Early-career recruitment pool spanning software tools, applications, analytics and firmware.',
    ['Python','C++','Java','SQL','JavaScript','Testing'], 'Pursuing a relevant bachelor’s or master’s degree; language choices are alternatives.',
    notes='Employer says this includes anticipated hiring; immediate vacancy or interview not guaranteed. US work eligibility unverified.')
add('Viget', 'Software Developer Intern (2027)', 'Location not confirmed in retrieved text', 'Software', 'internship',
    'https://jobs.lever.co/viget/b18cc87d-fca2-485a-a0f2-ad6197db63f2',
    'Internship involving web applications and application, JavaScript or UI development.',
    ['JavaScript'], status='needs_primary_review', notes='Indexed employer result only; direct page returned 403. Location and eligibility not established.')
add('Harley’s Limited', 'Data Analyst and Coordinator Intern', 'Nairobi, Kenya', 'Data', 'internship',
    'https://harleysltd.com/jobs/',
    'Analyse commercial data, prepare dashboards and support operational reporting.',
    ['Python','R','SQL','Power BI','Tableau','Statistics'], 'Relevant degree and at least one year of related experience; some tools are advantageous.',
    deadline='2026-10-17', status='archived', notes='Employer careers page contains multiple adverts; relevant section explicitly expired on 17 October 2026.')
add('IUCN', 'Intern - IT Department, Regional Office, Nairobi', 'Nairobi, Kenya', 'IT operations', 'internship',
    'https://hrms.iucn.org/iresy/index.cfm?event=vac.show.pdf&lang=en&vacId=11634',
    'Support regional IT systems, networks, cybersecurity and service delivery.',
    ['Networking','Cybersecurity','AWS','Microsoft 365'], deadline='2026-03-30', status='archived',
    notes='Official PDF has a March 2026 deadline; retained as an archived source.')
add('GAIN', 'Intern, Monitoring and Evaluation / Data Analysis', 'Nairobi, Kenya', 'Data', 'internship',
    'https://jobs.gainhealth.org/vacancies/1217/download/JD_Intern_Monitoring_Evaluation_Data_Analysis_KE_Final.pdf',
    'Monitoring, evaluation and data-analysis internship documented in an employer job-description PDF.', [],
    status='availability_unverified', notes='Static job-description PDF is not evidence of an open application window.')


ORIGINAL_COUNT = len(ROWS)
extend(add)
for row in ROWS[ORIGINAL_COUNT:]:
    row['research_batch'] = 'student-focused-expansion-2026-11-13'
    row['reviewed_date'] = COLLECTED
    if row['company'] == 'Cellulant Corporation':
        row['career_level'] = 'graduate_trainee'
    elif row['company'] == 'Capital Markets Authority':
        row['career_level'] = 'student_attachment'
    elif row['company'] == 'Kobby Technologies Ltd':
        row['career_level'] = 'internship_programme'


def main():
    out = ROOT/'data/listings'
    out.mkdir(parents=True, exist_ok=True)
    for row in ROWS:
        row['id'] = 'sourced-' + hashlib.sha256(row['source_url'].encode()).hexdigest()[:16]
        row['collected_date'] = COLLECTED
        row['is_fictional'] = False
        row['application_url'] = None  # No unverified direct application endpoint.
        row['arrangement'] = row['career_level'].replace('_', ' ').title()
        row['responsibilities'] = []  # Concise scope is in description, not invented bullet points.
        row['requirements'] = []
        row['skill_interpretation'] = 'Source-mentioned tags; may include alternatives or preferred tools. Not all are mandatory.'
        row['eligibility_status'] = 'unconfirmed'
        row['ready_for_live_application'] = False
    assert ORIGINAL_COUNT == 43
    assert len(ROWS) == 62
    assert len({r['id'] for r in ROWS}) == len(ROWS)
    assert len({r['source_url'] for r in ROWS}) == len(ROWS)
    (out/'real_opportunities.json').write_text(json.dumps(ROWS, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    candidates = [r for r in ROWS[ORIGINAL_COUNT:]
                  if r['availability_status'] == 'needs_primary_review']
    (out/'student_expansion_candidates.json').write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assets = ROOT/'app/src/main/assets'
    assets.mkdir(parents=True, exist_ok=True)
    (assets/'opportunities.json').write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    fields = ['id','title','company','location','sector','career_level','availability_status','deadline',
              'skills','eligibility','source_type','source_url','primary_source_url','research_notes','collected_date']
    with (out/'real_opportunities.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        for row in ROWS:
            writer.writerow({**row,'skills':'; '.join(row['skills']),'eligibility':' '.join(row['eligibility'])})
    statuses = Counter(r['availability_status'] for r in ROWS)
    lines = ['# Real opportunity research catalogue', '',
             f'Collected {COLLECTED}: {len(ROWS)} distinct real postings. This is a research snapshot, not a verified live vacancy feed.', '',
             '## Coverage and verification', '',
             '51 Kenya-based or explicitly Kenya-eligible records, 3 worldwide-remote records and 8 international/location-unconfirmed records.',
             'Titles, employers and source links are retained. Descriptions are short paraphrases. Missing facts remain empty or null.',
             'Employer pages and secondary summaries are distinguished by source_type. A visible advert does not prove recruitment remains open.', '',
             'Status counts: '+', '.join(f'{k}: {v}' for k,v in sorted(statuses.items()))+'.', '',
             '## Files', '',
             '- real_opportunities.json: structured records using the app’s basic role field names plus research metadata.',
             '- real_opportunities.csv: compact review sheet with source links and eligibility cautions.', '',
             '- student_expansion_candidates.json: 10 new student/graduate candidate records pending employer verification; not a live feed.',
             '- EXPANSION_REVIEW.md: addition counts, source conflicts and rejected leads.', '',
             '## Before importing into the app', '',
             'No Firestore write has been performed. Review secondary-source records against their linked originals.',
             'The Android app bundles the 10 expansion candidates, displays source/date/availability notes, and hides archived, unresolved and past-deadline adverts.',
             'Cloud records with the same IDs override bundled entries, including withdrawal/archive changes. Unsourced legacy records are excluded.',
             'application_url is deliberately null. source_url is an advert/reference page, not a verified application submission endpoint.',
             'Skills are source-mentioned tags, including alternatives and preferred skills; they are not a universal list of mandatory requirements.',
             'Many tags extend beyond the app’s current learning library; that mapping needs expansion before a complete growth path is promised.',
             'Do not use these records as proof of model quality or as relevance labels. Do not assume a worldwide/foreign role permits Kenyan applicants.', '',
             '## Source index', '', '| # | Employer | Role | Status | Source |', '| --- | --- | --- | --- | --- |']
    for i,row in enumerate(ROWS,1):
        lines.append(f"| {i} | {row['company']} | {row['title']} | {row['availability_status']} | [Advert]({row['source_url']}) |")
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'records':len(ROWS),'statuses':statuses,'with_skill_tags':sum(bool(r['skills']) for r in ROWS)},indent=2))


if __name__ == '__main__':
    main()
