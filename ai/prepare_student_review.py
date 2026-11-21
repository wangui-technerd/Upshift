"""Freeze a blinded student-profile review; never invent reviewer labels."""
from pathlib import Path
import os, sys, json, hashlib, random, csv, shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ['OMP_NUM_THREADS'] = '2'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    import joblib
    import pandas as pd
    from upshift_ai.matching import recommend
    from upshift_ai.semantic import load_encoder
    out = ROOT / 'student_review'
    if out.exists():
        raise SystemExit('Review folder already exists. Preserve frozen files; use a new version for another run.')
    out.mkdir()
    private = out / 'private'; private.mkdir()
    profiles = []
    examples = [
      ('computing', 'Software internship', 'Python, JavaScript, HTML, CSS, Git and SQL. Built a Flask REST API and a small React interface; wrote basic pytest tests.', 'Kotlin, Android Studio, Firebase and Git. Built a student expense tracker with authentication and a database; basic unit testing.'),
      ('finance', 'Finance or accounting internship', 'Excel, bookkeeping, bank reconciliation and financial statements. Coursework project preparing a budget and cash-flow spreadsheet; no professional certification.', 'Accounting and finance student with Excel, QuickBooks practice and accounts payable coursework. Prepared ledger entries and reconciliations in a class project.'),
      ('marketing', 'Marketing internship', 'Canva, social media content, copywriting and Excel. Planned a student-club Instagram campaign and tracked reach and engagement.', 'Google Analytics introductory practice, market research, survey design and PowerPoint. Analysed a student business customer survey; basic digital advertising knowledge.'),
      ('human_resources', 'Human resources internship', 'HR management student with recruitment administration coursework, Excel, record keeping and clear writing. Organised volunteer interviews for a campus club.', 'Human resources student with onboarding, employee records, communication and basic labour-relations coursework. Used Excel to organise attendance for a student society.'),
      ('engineering', 'Engineering internship', 'Mechanical engineering student with AutoCAD, SolidWorks, technical drawings and workshop safety coursework. Designed a simple pump assembly as a university project.', 'Electrical engineering student with circuit analysis, MATLAB, basic PLC programming and electrical safety. Built and documented a small sensor-monitoring project.'),
      ('digital_media', 'Digital media or design internship', 'Figma, Adobe Illustrator and Photoshop. Designed a campus-event poster and a mobile interface prototype; has a small student portfolio.', 'Adobe Premiere Pro, photography, video editing and storytelling. Produced a short student documentary and social-media clips; basic audio editing.'),
    ]
    for i,(field,interest,a,b) in enumerate(examples,1):
        for split,text in [('validation',a),('test',b)]:
            pid=f'SP{(i-1)*2+(1 if split=="validation" else 2):02d}'
            full=f'Year 3 undergraduate {field.replace("_"," ")} student in Kenya seeking a first {interest.lower()}. {text} No full-time professional experience. Open to international roles only where location and work-authorisation requirements permit; availability and eligibility must be checked separately.'
            profiles.append({'profile_id':pid,'split':split,'field':field,'profile_text':full,'fictional':True})
    profiles += [
        {'profile_id':'CAL01','split':'calibration','field':'computing','profile_text':'Year 2 computing student in Kenya seeking a first software internship. Python, SQL, Git and HTML. Built a basic Django student club website. No professional work experience. Location and work-authorisation eligibility unknown.','fictional':True},
        {'profile_id':'CAL02','split':'calibration','field':'business','profile_text':'Year 3 business student in Kenya seeking a first operations internship. Excel, customer service, inventory coursework and report writing. Managed stock records for a campus event. No professional work experience. Location and work-authorisation eligibility unknown.','fictional':True},
    ]
    pd.DataFrame(profiles).to_csv(out/'student_profiles.csv',index=False)
    artifact=ROOT/'artifacts/upshift_bundle.joblib'
    bundle=joblib.load(artifact)
    encoder=load_encoder(ROOT/'artifacts/semantic_encoder')
    pairs={}; rankings=[]; slots=[]
    for p in profiles:
        for method in ('lexical','semantic'):
            result=recommend(bundle,p['profile_text'],method=method,encoder=encoder,top_k=5)
            slots.append({'profile_id':p['profile_id'],'split':p['split'],'method':method,'returned':len(result['matches'])})
            for rank,j in enumerate(result['matches'],1):
                key=(p['profile_id'],j['job_id'])
                pairs[key]={'profile_id':p['profile_id'],'split':p['split'],'field':p['field'],'profile_text':p['profile_text'],'job_id':j['job_id'],'job_title':j['title'],'company':j['company_name'],'job_description':j['description'],'location':j['location'],'experience_level':j['experience_level'],'listed_date':j['listed_date'],'expiry_date':j['expiry_date'],'application_url':j['application_url']}
                rankings.append({'profile_id':p['profile_id'],'split':p['split'],'method':method,'rank':rank,'job_id':j['job_id'],'similarity':j['similarity']})
    keys=list(pairs);random.Random(20261121).shuffle(keys)
    ids={k:f'PAIR{i:04d}' for i,k in enumerate(keys,1)}
    for r in rankings:r['pair_id']=ids[(r['profile_id'],r['job_id'])]
    pd.DataFrame(rankings).to_csv(private/'rankings_private.csv',index=False)
    pd.DataFrame(slots).to_csv(private/'retrieval_counts.csv',index=False)
    rows=[]
    for k in keys:
        row=dict(pairs[k]);row.pop('split');row.pop('field')
        row={'pair_id':ids[k],**row,'relevance':'','eligibility':'','availability':'','reason':'','uncertain_reason':''}
        rows.append(row)
    calibration=[r for r in rows if r['profile_id'].startswith('CAL')][:5]
    calibration_ids={r['pair_id'] for r in calibration}
    mainrows=[r for r in rows if not r['profile_id'].startswith('CAL')]
    pd.DataFrame(calibration).to_csv(out/'calibration_five_pairs.csv',index=False)
    for number in (1,2):
        folder=out/f'reviewer_{number}';folder.mkdir()
        pd.DataFrame(mainrows).to_csv(folder/'reviewer_ratings.csv',index=False)
        (folder/'reviewer_identity.json').write_text(json.dumps({'reviewer_id':f'reviewer_{number}','reviewer_type':'','date_completed':'','rubric_version':'1.0'},indent=2))
    adjudication=pd.DataFrame([{'pair_id':r['pair_id'],'reviewer_1_relevance':'','reviewer_2_relevance':'','final_relevance':'','final_eligibility':'','final_availability':'','resolution_reason':''}for r in mainrows])
    adjudication.to_csv(private/'adjudication_template.csv',index=False)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'seed':20261121,'status':'awaiting_real_ratings','profiles':12,'validation_profiles':6,'test_profiles':6,'calibration_profiles':2,'calibration_pairs':len(calibration),'main_unique_pairs':len(mainrows),'methods':['lexical','semantic'],'top_k':5,'catalogue':'Frozen historical research catalogue; not current vacancies','bundle_sha256':digest(artifact),'selection_rule':'Choose on validation mean pooled NDCG@5, then mean P@5; exact ties prefer lexical. Report selected method on held-out test once.','ndcg_scope':'Ideal order based on pooled top-five candidates from both methods; not full-catalogue relevance.','eligibility_rule':'Separate explicit eligibility from skill relevance; unknown is not ineligible.','reviewer_requirement':'Human and AI assessments must be separately attributed; do not call AI a human reviewer.'}
    manifest['files']={p.relative_to(out).as_posix():digest(p)for p in out.rglob('*')if p.is_file()}
    (private/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items()if k!='files'},indent=2))

if __name__=='__main__':main()
