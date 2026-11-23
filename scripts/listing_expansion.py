"""Additional researched adverts; called by prepare_listing_catalogue.py.

Reviewed 2026-11-13. Secondary listings are leads, not confirmed vacancies.
"""


def extend(add):
    def lead(company, title, sector, url, summary, skills=(), eligibility='',
             deadline=None, notes='', primary=None, status='needs_primary_review',
             location='Nairobi, Kenya', source_type='aggregator'):
        add(company, title, location, sector, 'internship', url, summary, skills,
            eligibility, deadline, status=status, source_type=source_type,
            notes=notes, primary=primary)

    lead('Cellulant Corporation', 'Graduate Trainee: Software Engineering - Kenya', 'Software engineering',
         'https://www.myjobmag.co.ke/job/graduate-trainee-software-engineering-kenya-cellulant-corporation',
         'Develop and test payment-related applications with engineering mentorship.',
         ['Java', 'REST APIs', 'Git', 'Software testing', 'Agile'],
         'Relevant diploma or higher; Java backend knowledge, REST experience and public code portfolio.',
         notes='Graduate trainee, not a general student attachment. Secondary boards disagree on deadlines; no deadline adopted.')
    lead('One Acre Fund', 'Junior ITSM Technician Intern', 'IT support',
         'https://www.myjobmag.co.ke/job/junior-itsm-technician-intern-one-acre-fund',
         'Handle supervised service-desk requests, troubleshooting and incident documentation.',
         ['IT support', 'Troubleshooting', 'Documentation'],
         'Source lists degree-level qualification; verify detailed programme eligibility.',
         notes='Secondary source reports 20 January 2027, but other boards disagree. Official destination returned HTTP 404; availability unresolved.',
         primary='https://oneacrefund.org/vacancies/junior-itsm-technician-intern?gh_jid=8305321',
         status='availability_unverified', location='Kakamega, Kenya')
    lead('BURN Manufacturing', 'Software QA Intern', 'Software testing',
         'https://cdn.greatkenyanjobs.com/jobs/job-detail/job-Software-QA-Intern-job-at-Burn-178046',
         'Test applications and APIs, validate database results and document defects.',
         ['SQL', 'Postman', 'Manual testing', 'Regression testing', 'Agile'],
         'Manual testing, SQL and API testing familiarity; secondary structured fields also list degree and 12 months experience.',
         notes='Employer advert returned HTTP 410 Gone. Kept as archived reference despite future deadlines on secondary boards.',
         primary='https://burnmanufacturing.applytojob.com/apply/jTqBOHqmSa/Software-QA-Intern', status='archived')
    lead('Future Kenya Ltd', 'IT Programmer & Web Developer Intern', 'Software engineering',
         'https://kenya.mimusjobs.com/job/it-programmer-web-developer-intern/',
         'Build business applications and help maintain ERP systems during mentored onboarding.',
         ['C#', '.NET', 'SQL', 'Debugging', 'Software testing'],
         'Recent computing graduate with C#, .NET and SQL knowledge; Nairobi onboarding and longer-term career commitment.',
         '2026-11-17', notes='Date is from secondary advert; confirm with employer.')
    lead('ABNO Softwares International', 'CS Engineer (Tech Intern)', 'Enterprise software',
         'https://kenya.mimusjobs.com/job/cs-engineer-tech-intern/',
         'Assist ERP configuration, data migration, issue resolution and user training.',
         ['ERP', 'Databases', 'Troubleshooting', 'Communication'],
         'Computing-related bachelor degree; database, configuration or scripting knowledge advantageous.',
         '2026-11-28', notes='Customer-success engineering role; not a pure coding internship. Date requires employer confirmation.')
    lead('Urgent Action Fund-Africa', 'ICT & Database Intern', 'IT and data',
         'https://www.corporatestaffing.co.ke/job/ict-database-intern-ngo-job-urgent-action-fund-africa/',
         'Assist user support, database quality checks and digital workplace administration.',
         ['Microsoft 365', 'Data cleaning', 'IT support', 'Data protection'],
         'Degree in computing, information systems or related discipline.', '2026-10-07',
         status='archived', notes='Published deadline has passed; reference material only.')
    lead('Zade Associates LLP', 'Information Systems Audit Intern', 'Cybersecurity and audit',
         'https://www.corporatestaffing.co.ke/job/information-systems-audit-intern-job-zade-associates-llp/',
         'Support IT control reviews, risk assessments and audit documentation.',
         ['IT controls', 'Risk assessment', 'Cybersecurity', 'Documentation'],
         'Completed relevant degree with first class or upper second; practical experience advantageous.',
         '2026-10-23', status='archived', notes='Deadline passed. Not suitable for a continuing student who has not completed their degree.')
    lead('Kenya Tradex', 'Cybersecurity Intern', 'Cybersecurity',
         'https://www.greatkenyanjobs.com/jobs/job-detail/job-Cybersecurity-Intern-job-at-Kenya-Tradex-176366/nav-15?Itemid=231',
         'Internship titled cybersecurity; published duties describe general learning and office support.',
         ['Communication', 'Research', 'Documentation'],
         'Secondary structured fields list bachelor degree and no experience requirement.',
         '2026-10-17', status='archived',
         notes='Posted and closing dates coincide; generic duties do not establish technical cybersecurity requirements. Exclude from current recommendations.')
    lead('Eezy Track Limited', 'Data Analyst-Intern', 'Data analytics',
         'https://www.brightermonday.co.ke/listings/data-analyst-intern-n9dwrz',
         'Prepare datasets, explore trends and produce dashboards for business teams.',
         ['Excel', 'SQL', 'Python', 'Data visualization', 'Data cleaning'],
         'Relevant bachelor degree; no experience or less than one year. Python is advantageous, not mandatory.',
         notes='Board specifies Kenyan applicants and rolling shortlisting; employer intake availability still needs checking.')
    lead('SENRI Ltd.', 'Business Intelligence Analyst Intern', 'Business intelligence',
         'https://ke.linkedin.com/jobs/view/business-intelligence-analyst-intern-at-senri-ltd-4273529269',
         'Assist dashboard delivery, data modelling and BI issue investigation.',
         ['Looker Studio', 'Tableau', 'SQL', 'Data modeling'],
         'Final-year student or fresh graduate; at least three months internship experience.',
         status='archived', notes='LinkedIn explicitly says no longer accepting applications. SQL and prior BI exposure are advantages.')
    lead('Amref Kenya', 'Data Management and Reporting Intern', 'Data analytics',
         'https://www.corporatestaffing.co.ke/job/data-management-reporting-intern-job-amref/',
         'Help validate programme data and improve reporting dashboards.',
         ['Qlik', 'Data quality', 'Data visualization', 'Reporting'],
         'Relevant diploma minimum, degree preferred; at least one year of related experience.',
         '2026-09-24', status='archived', notes='Deadline passed; experience requirement makes this a progression example.')
    lead('Kobby Technologies Ltd', 'Internship Programme 2026', 'Technology and business',
         'https://www.jobsinkenya.co.ke/job/internship-programme-kobby-technologies/',
         'Six-month placements in development, networking, data centres, IT support and business departments.',
         ['Oracle', 'Microsoft technologies', 'Networking'],
         'Students or recent graduates in relevant fields; department-specific eligibility varies.',
         '2026-11-25', notes='Start 14 December 2026 per advert. One programme record, not nine invented vacancies. Skill tags describe technical tracks only.')
    lead('HUSHNET LTD', 'IT Support & Product Solutions Intern', 'IT support',
         'https://manuel.co.ke/jobs/7f0c79cf-2ea5-44c2-905c-433683fa852b',
         'Support client systems, research technology products and prepare technical documentation.',
         ['Networking', 'Microsoft 365', 'Troubleshooting', 'Documentation'],
         'Recent relevant diploma or degree; basic networking and computer systems knowledge.',
         '2026-11-30', notes='Six-month paid internship according to reproduced CampusBiz advert; employer confirmation pending.')
    lead('PZ Cussons East Africa Ltd', 'Graduate Intern - Marketing', 'Marketing',
         'https://pzcussons.wd3.myworkdayjobs.com/en-US/CareersPZCussons/job/Nairobi/Graduate-Intern---Marketing_JR003030',
         'Graduate marketing internship indexed on the employer hiring system.',
         eligibility='Detailed eligibility unreadable; do not infer requirements from the title.',
         deadline='2026-11-06', status='archived', source_type='employer',
         notes='Employer search index states end date 6 November 2026; page body unreadable. Secondary boards show contradictory later dates.')
    lead('Sucafina', 'Trade Assistant Intern', 'Trading and supply chain',
         'https://www.atomcareer.co.ke/jobs/agriculture/trading-assistant-intern/',
         'Learn coffee trade operations through desk support and mentoring over six months.',
         eligibility='Secondary board labels bachelor degree and zero to two years; confirm full employer requirements.',
         notes='Secondary publisher attributed to Jobs for Humanity. Multiple boards disagree on closing date; left unknown.')
    lead('CorpsAfrica', 'Digital Communications Intern', 'Digital communications',
         'https://campusbiz.co.ke/careers/vacancy/986084-corpsafrica-digital-communications-internship/',
         'Create digital visuals and support social content for nonprofit communications.',
         ['Canva', 'Graphic design', 'Social media', 'Content creation'],
         'Remote from one of eleven operating countries including Kenya; full-time paid placement.',
         notes='Secondary deadline 17 November 2026 conflicts with employer endpoint returning HTTP 410 Gone; availability unresolved.',
         primary='https://corpsafrica.applytojob.com/apply/Kn57UcuPQ0/Digital-Communications-Intern',
         status='availability_unverified', location='Remote, Kenya eligible among eleven operating countries')
    lead('Haki Yetu Charitable Trust', 'Procurement Intern', 'Procurement',
         'https://www.myjobmag.co.ke/job/procurement-intern-haki-yetu-charitable-trust',
         'Procurement internship for recent supply-chain and related graduates.',
         ['Excel', 'Microsoft Word'],
         'Relevant diploma or degree completed within two years; no work experience required.',
         '2026-11-22', notes='Closing time 5pm per secondary advert; professional study and student KISM membership are advantages.')
    lead('Capital Markets Authority', 'Student Attachment - ICT (Operations and Infrastructure)', 'IT infrastructure',
         'https://www.greatkenyanjobs.com/jobs/job-detail/job-Student-Attachment-%E2%80%93-Information-and-Communication-Technology-Operations-and-Infrastructure-job-at-Capital-Markets-Authority-CMA-179620',
         'ICT operations and infrastructure attachment advertised for continuing students.',
         eligibility='Currently pursuing a relevant computing or information-science bachelor degree.',
         deadline='2026-11-23', notes='Student attachment rather than graduate-only internship; verify through the authority recruitment portal.')
    lead('LOLC Kenya Microfinance Bank PLC', 'Digital Marketing Intern', 'Digital marketing',
         'https://manuel.co.ke/jobs/230787e6-e0c3-4c51-a420-84c3fb920d2e',
         'Assist online campaigns, graphics and marketing performance analysis.',
         ['Google Ads', 'Meta Ads', 'Canva', 'Adobe Photoshop', 'Adobe Illustrator'],
         'Pursuing or recently completed relevant diploma or degree; available full-time.',
         notes='Secondary boards show several conflicting November/December deadlines; deadline left unknown. Design tools are examples, not all mandatory.')
