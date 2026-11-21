"""Record the disclosed single AI review and reproduce its descriptive metrics.

These are authored AI judgements, not human labels or a second reviewer.
No method, rank or split was used to assign the ratings below.
"""
from pathlib import Path
import json, hashlib, math
import pandas as pd

ROOT = Path(__file__).resolve().parent
REVIEW = ROOT / 'student_review'

# grade, eligibility, evidence-based reason; groups share the same vacancy evidence.
DECISIONS = [
('0001',1,'unknown','Broad application-development training offers a partial route into software; it is not a focused Android internship. US authorisation and age are unverified.'),
('0002',1,'unknown','College marketing internship accepts beginners, but this design profile provides limited marketing or campaign evidence.'),
('0003',2,'unknown','Beginner college marketing internship aligns with marketing study, survey analysis and introductory analytics.'),
('0004',0,'ineligible','Requires a completed bachelor degree and two years professional experience; profile is a first-internship student.'),
('0006',1,'unknown','Python and Git align, but the profile does not demonstrate the requested Jenkins, Ansible or Terraform knowledge; GPA and sponsorship status are unknown.'),
('0027',1,'unknown','Git and software projects transfer, but Python scripting and automation-tool knowledge are not demonstrated; GPA and sponsorship status are unknown.'),
('0059',0,'unknown','Mechanical CAD and pump-design project do not demonstrate the core scripting and DevOps automation knowledge.'),
('0007,0020',2,'unknown','HR student internship covers records, administration and communication that align with the supplied coursework and campus experience.'),
('0008,0090',1,'ineligible','Finance internship aligns with accounting coursework but explicitly requires at least one previous internship or work experience, not present in this first-internship profile.'),
('0009',2,'unknown','Social content, campaign planning and engagement tracking support this beginner social-media internship; additional tools can be learned.'),
('0071',2,'unknown','Video editing and social-media clips support the content-creation internship, with marketing analytics a normal development area.'),
('0010,0078',1,'unknown','HR duties overlap coursework, but independent employee relations and HRIS work exceed the demonstrated campus administration; experience is phrased as helpful.'),
('0012,0108',0,'ineligible','Requires an accounting degree and one to three years accounting experience; neither completed degree nor professional experience is evidenced.'),
('0013',1,'unknown','Computing is a STEM field and the role accepts undergraduates, but astronomy-education research is outside the stated software goal; US citizenship/residency is unknown.'),
('0113',1,'unknown','Survey analysis transfers to education research, but the profile does not establish the specified STEM/education field or strong academic record; citizenship/residency is unknown.'),
('0014,0023',0,'ineligible','Requires two to four years HR experience and solid HR practice, beyond this first-internship student.'),
('0015',2,'unknown','Student video-editing opportunity requires no experience; Premiere Pro, photography and documentary work directly align.'),
('0016',0,'ineligible','Requires two years HR experience or a completed bachelor degree; student has neither demonstrated.'),
('0017',2,'unknown','Marketing student has social-content, Canva and campaign tracking evidence matching the internship core duties.'),
('0018',2,'unknown','Video-editing and digital-media internship explicitly accepts students; Premiere Pro and documentary work match its main duties.'),
('0019,0129',0,'ineligible','Requires two years full-time clerical work with education substituting for at most one year; campus tasks do not meet the remaining experience requirement.'),
('0022',2,'unknown','Electrical student internship aligns with circuit analysis and sensor project; onsite availability remains unverified.'),
('0024',2,'unknown','Student marketing/operations programme accepts learning and introductory analytics; marketing research and PowerPoint support its duties. US location eligibility remains unknown.'),
('0025',1,'ineligible','Graduate training could build on Android projects, but requires a completed degree or bootcamp and graduation by May 2024, not evidenced for the student.'),
('0026,0089',2,'unknown','Accounting internship accepts current students with zero to one year experience; ledger, reconciliation and Excel coursework align. US work eligibility is unknown.'),
('0029',0,'ineligible','Pump and CAD project overlap, but role requires three to five years applicable experience and extensive slurry-pump expertise.'),
('0030,0042',0,'ineligible','Requires three years accounts-receivable work or a degree plus one year; first-internship student does not meet either route.'),
('0032',1,'unknown','Video skills are useful, but main internship duty is graphic creation and proficiency in graphic-design software is not demonstrated.'),
('0047',2,'unknown','College graphic-content internship aligns directly with Illustrator, Photoshop and the poster portfolio.'),
('0033',1,'ineligible','Design skills are related, but ad trafficking, campaign tools and spreadsheet reporting are not demonstrated; degree or one year DFP experience is required.'),
('0034,0109',1,'unknown','Computing projects transfer to a student project-management internship, but project-management principles and AI/blockchain interest are not demonstrated.'),
('0035',2,'unknown','Social-media internship aligns with marketing study, Canva content and the student-club campaign; short-form video is a development area.'),
('0036',0,'ineligible','Requires multiple years of professional development and infrastructure-as-code experience plus a degree; student project experience is insufficient.'),
('0038',2,'unknown','Student marketing background, Canva, campaign content and Excel fit the social-media internship; Photoshop and editorial practice need development.'),
('0111',1,'unknown','Video and editing skills transfer, but PR/marketing background and required Photoshop/Canva/Office evidence are limited.'),
('0039',0,'ineligible','Requires completed accounting degree and one to three years accounting experience, beyond the student profile.'),
('0040',1,'unknown','Analytics and marketing study transfer, but the content-creation and practical campaign evidence is limited in this profile.'),
('0041',2,'unknown','Premiere Pro, documentary production and storytelling directly support this student videography internship.'),
('0043',1,'ineligible','Student design portfolio and Adobe tools align, but the stated degree requirement is not completed and InDesign/press-ready workflow are not demonstrated.'),
('0044',2,'unknown','Circuit analysis and sensor project support the electrical internship. At least two years remaining, US work authorisation and onsite availability are unverified.'),
('0045',0,'ineligible','Mandatory seven years developer experience and over five years enterprise experience are far beyond first-internship Android projects.'),
('0046',0,'ineligible','Requires proven executive-level marketing experience, advanced campaign tools and a degree; introductory analytics and coursework are insufficient.'),
('0048,0081',0,'unknown','Cell engineering here means CRISPR, tissue culture and molecular biology; the computing/mechanical profile does not demonstrate those core laboratory skills.'),
('0051',1,'unknown','Design tools and portfolio transfer, but routine social-content/copyediting evidence is limited; school credit and Carson attendance are unverified.'),
('0130',2,'unknown','Marketing study, Canva, copywriting and Instagram campaign align with student social-content duties; school credit and onsite availability are unknown.'),
('0052',2,'unknown','Student software internship accepts Python fundamentals and supervised learning; Flask, React, Git and basic tests directly support the work.'),
('0053',1,'ineligible','Electrical knowledge and MATLAB transfer, but a completed degree and specialist signal-integrity tools/measurement experience are not demonstrated; export authorisation is unknown.'),
('0054',0,'ineligible','Senior SharePoint role requires eight years relevant experience and active security clearance; first-internship web projects do not qualify.'),
('0055',1,'unknown','Design background transfers, but writing, video and social-calendar evidence is limited; mandatory Phoenix residence is unverified.'),
('0062',2,'unknown','Copywriting and social campaign experience align with this content internship; video is a preferred extra and Phoenix residence remains unverified.'),
('0068',2,'unknown','Video editing and social clips directly support the marketing-video/content internship; Phoenix residence is unverified.'),
('0056',0,'ineligible','Civil/construction engineering work requires a completed relevant degree; electrical coursework alone does not demonstrate the main field-inspection duties.'),
('0057,0107',0,'ineligible','Requires four or more years related experience, education or training and ownership of complex marketing automation; Year 3 introductory practice does not establish this.'),
('0060',1,'ineligible','Ledger, Excel and reconciliation coursework align with a junior role, but completed bachelor degree is required.'),
('0061,0105',0,'ineligible','Requires three years HR experience or undergraduate core completion plus twelve months HR experience; campus administration does not meet these alternatives.'),
('0063',2,'unknown','Introductory analytics, marketing study and survey analysis align with an internship requiring knowledge or experience of web analytics.'),
('0064',2,'unknown','Student creative internship explicitly values photography/video and willingness to learn; Premiere Pro and documentary work align.'),
('0127',2,'unknown','Student creative internship accepts developing talent; Photoshop and visual-design portfolio support digital creative tasks, with photography to develop.'),
('0065',1,'ineligible','Records and onboarding coursework align, but requires completed bachelor degree or lower qualification plus professional experience.'),
('0066,0069',0,'ineligible','Requires at least two years HR experience (two to five in qualifications); student coursework does not meet it.'),
('0070,0094',1,'ineligible','HR coursework and communication transfer, but requires a completed degree plus professional experience.'),
('0072',1,'ineligible','Budgeting, finance study and Excel are relevant, but completed degree or equivalent experience and advanced modelling evidence are missing.'),
('0073',0,'ineligible','Python overlaps but mandatory eight to ten years experience is far beyond a first-internship student.'),
('0074',1,'unknown','Beginner digital-media apprenticeship offers training, but marketing rather than design focus is a partial goal match; Detroit residence and US work authorisation are unknown.'),
('0075',2,'unknown','Student development-engineering internship accepts mechanical students; CAD, technical drawings and workshop coursework support its hands-on engineering duties.'),
('0128',2,'unknown','Internship accepts electrical students; MATLAB, electrical principles and sensor project provide relevant foundational evidence.'),
('0076',1,'ineligible','Electrical coursework is relevant but graduate role requires completed electrical degree and established building-systems experience.'),
('0083',0,'ineligible','Role requires electrical engineering degree and electrical-building experience; profile is a mechanical undergraduate.'),
('0077',1,'ineligible','Volunteer recruitment and communication align, but requires completed degree and proven HR coordination experience.'),
('0079',0,'ineligible','Requires electrical-trade training/apprenticeship and valid electrician licence; engineering coursework does not establish those credentials.'),
('0080',2,'unknown','Internship asks for basic digital marketing and analytics familiarity; Google Analytics practice and marketing research align.'),
('0082',0,'ineligible','Requires completed degree and three to five years agency experience at senior-account level, far beyond student design work.'),
('0084',0,'ineligible','Requires engineering degree and at least five years mechanical experience; CAD student project is insufficient.'),
('0085',0,'ineligible','Requires completed degree and one to two years progressive general-ledger experience; first-internship coursework does not meet it.'),
('0086',0,'ineligible','Despite Android subject overlap, role requires IT-company work experience and Java development experience plus a degree; student Kotlin project does not meet those requirements.'),
('0087',0,'ineligible','Requires bachelor degree and minimum two years accounting experience, beyond the finance student profile.'),
('0088',0,'ineligible','CAD overlaps but role seeks production-level designer, completed qualification and three-plus years modular design/manufacturing experience.'),
('0091',1,'ineligible','React, HTML/CSS and JavaScript projects align, but requires completed degree, previous developer experience and deeper Redux/performance tooling.'),
('0092',0,'ineligible','Intern title conflicts with required degree and two to three years marketing analytics experience; introductory student practice is insufficient.'),
('0093',0,'ineligible','Mechanical profile lacks electrical building-system evidence; requires at least three years AutoCAD and electrical-system experience.'),
('0095',2,'unknown','College videography internship aligns with photography, video editing and storytelling; ownership of required camera gear is unknown.'),
('0097',2,'unknown','Beginner remote social-content internship aligns with marketing, Canva and the Instagram campaign; video editing can develop.'),
('0098',0,'ineligible','Requires minimum five years budget/forecast analysis and completed degree; coursework is insufficient. Citizenship/clearance also require verification.'),
('0099',0,'ineligible','Requires at least three years industrial electrical controls and PLC/HMI experience; basic student PLC knowledge is insufficient.'),
('0100',1,'unknown','Graduate-focused junior accounting duties align with Excel and ledger coursework; completed degree is preferred, not mandatory, and student is not yet a graduate.'),
('0101',0,'unknown','Programme accepts varied majors but is banking rather than software; profile shows no finance interest. GPA and graduation window are unknown.'),
('0102',0,'ineligible','Bookkeeping coursework overlaps but posting requires paid AR/AP experience, at least one year even in its closing invitation.'),
('0103',2,'unknown','Undergraduate social-media internship aligns with Canva, copywriting and campaign experience; US work authorisation is unknown.'),
('0115',1,'ineligible','SolidWorks and mechanical project fit a zero-experience graduate role, but a completed mechanical degree is required; US citizenship is unknown.'),
('0117',1,'ineligible','Finance and financial-statement coursework are relevant, but requires completed degree and proven accountant experience across tax/audit tasks.'),
('0119',2,'unknown','Social campaign and content evidence support this student internship; LA presence, class credit and phone-video proficiency remain unverified.'),
('0120',1,'ineligible','Reconciliations and financial statements overlap, but requires BA/BS or equivalent and recent relevant accounting/ERP experience, not demonstrated.'),
('0121',2,'unknown','Finance internship accepts college coursework and Office skills; budget/cash-flow project and Excel support its duties.'),
('0122',0,'ineligible','Requires seven-plus years web/REST application experience; student Flask and React projects are insufficient.'),
('0123',0,'unknown','Beach water sampling and environmental monitoring do not align with the Android/software internship goal; enrolment alone does not establish relevance.'),
('0124',2,'unknown','Marketing student social campaign, Canva and engagement tracking align with the internship core requirements; SEO/tools can develop.'),
('0125',1,'unknown','Kotlin, Git and unit tests transfer, but one year Java coding, REST/cloud APIs and SQL are not demonstrated; absence of evidence is not proof of no coding history.'),
('0126',0,'ineligible','Requires PR/journalism/communications enrolment and mass-communication/AP-style coursework; mechanical student profile does not meet the specified programme requirement.'),
]

def run():
    out=REVIEW/'ai_assisted';out.mkdir(exist_ok=True)
    source=pd.read_csv(REVIEW/'reviewer_1/reviewer_ratings.csv').fillna('')
    labels={}
    for ids,grade,eligible,reason in DECISIONS:
        for number in ids.split(','):
            pid='PAIR'+number
            assert pid not in labels,pid
            labels[pid]=(grade,eligible,reason)
    assert set(labels)==set(source.pair_id), (set(source.pair_id)-set(labels),set(labels)-set(source.pair_id))
    for i,row in source.iterrows():
        grade,eligible,reason=labels[row.pair_id]
        expiry=pd.to_datetime(row.expiry_date,utc=True,errors='coerce')
        source.loc[i,['relevance','eligibility','availability','reason','uncertain_reason']]=[grade,eligible,'expired' if pd.notna(expiry) and expiry<pd.Timestamp('2026-11-22',tz='UTC') else 'unknown',reason,'']
    source.to_csv(out/'ratings.csv',index=False)
    meta={'reviewer_id':'codex_ai_assisted_1','reviewer_type':'ai_assisted','date_completed':'2026-11-22','rubric_version':'1.0','independent_human_review':False,'rating_basis':'Authored contextual judgements from student profiles and vacancy descriptions/requirements. Requirement-focused evidence excerpts were used; not an exhaustive human audit of every description. No main-sheet method/rank/split used to assign labels. Unverified location, GPA, equipment and citizenship were kept unknown; explicit unmet mandatory qualifications marked ineligible.'}
    (out/'reviewer_identity.json').write_text(json.dumps(meta,indent=2))
    manifest=json.loads((REVIEW/'private/manifest.json').read_text())
    for name in ['student_profiles.csv','private/rankings_private.csv','private/retrieval_counts.csv']:
        assert hashlib.sha256((REVIEW/name).read_bytes()).hexdigest()==manifest['files'][name]
    ranks=pd.read_csv(REVIEW/'private/rankings_private.csv');ranks=ranks[ranks.split.ne('calibration')]
    lookup=source.set_index('pair_id').relevance.astype(int).to_dict()
    metrics=[]
    def dcg(values):return sum((2**v-1)/math.log2(i+2) for i,v in enumerate(values))
    for (pid,split,method),g in ranks.groupby(['profile_id','split','method']):
        grades=[lookup[x] for x in g.sort_values('rank').head(5).pair_id]
        pool=ranks[ranks.profile_id.eq(pid)].pair_id.unique()
        ideal=dcg(sorted([lookup[x] for x in pool],reverse=True)[:5])
        metrics.append(dict(profile_id=pid,split=split,method=method,precision_at_5=sum(x==2 for x in grades)/5,pooled_ndcg_at_5=dcg(grades)/ideal if ideal else 0.0,result_coverage=int(bool(grades)),good_match_coverage=int(2 in grades)))
    per=pd.DataFrame(metrics)
    summary=per.groupby(['split','method']).agg(precision_at_5=('precision_at_5','mean'),pooled_ndcg_at_5=('pooled_ndcg_at_5','mean'),result_coverage=('result_coverage','mean'),good_match_coverage=('good_match_coverage','mean'),profiles=('profile_id','count')).reset_index()
    # Frozen rule: validation NDCG, then P@5, then lexical. No test-based tuning.
    selected=summary[summary.split.eq('validation')].sort_values(['pooled_ndcg_at_5','precision_at_5','method'],ascending=[False,False,True]).iloc[0].method
    report={'status':'completed_single_ai_assisted_review','selected_method':selected,'selection_basis':'validation pooled NDCG@5, then P@5, then lexical','test_result':summary[summary.split.eq('test')&summary.method.eq(selected)].to_dict('records'),'reviewer':meta,'pairs':len(source),'independent_human_review':False,'inter_rater_agreement':None,'limits':['Single AI-assisted judgement set, not independent human ground truth','12 fictional profiles; six validation and six held-out test profiles','Pooled NDCG uses union of both top-five lists, not full catalogue','Historical jobs: relevance is separate from current eligibility and availability','Method choice is provisional pending representative human validation']}
    per.to_csv(out/'per_profile_metrics.csv',index=False);summary.to_csv(out/'summary.csv',index=False)
    (out/'evaluation.json').write_text(json.dumps(report,indent=2))
    print(summary.to_string(index=False));print('Selected:',selected)
    return report

if __name__=='__main__':run()
