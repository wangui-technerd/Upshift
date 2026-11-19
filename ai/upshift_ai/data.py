"""Load original CSVs; preserve metadata and use a fixed research catalogue."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from .preprocessing import plain_text,prepare_resume,clean_text

SEED=42
TITLE_RULES={
 'INFORMATION-TECHNOLOGY':r'\b(?:software|developer|network|help desk|it support|system administrator|data scientist|data analyst)\b',
 'ACCOUNTANT':r'\b(?:accountant|accounting|bookkeeper)\b',
 'BANKING':r'\b(?:bank|banking|teller)\b','CHEF':r'\b(?:chef|cook|kitchen)\b',
 'CONSTRUCTION':r'\b(?:construction|carpenter|electrician|plumber)\b','ENGINEERING':r'\bengineer\b',
 'FINANCE':r'\b(?:finance|financial)\b','FITNESS':r'\b(?:fitness|personal trainer)\b',
 'HEALTHCARE':r'\b(?:nurse|medical|patient care|clinical|pharmacist)\b',
 'HR':r'\b(?:hr|human resources|recruiter|recruitment)\b','SALES':r'\bsales\b',
 'TEACHER':r'\b(?:teacher|tutor|instructor)\b','DESIGNER':r'\b(?:designer|design intern)\b',
 'DIGITAL-MEDIA':r'\b(?:digital marketing|social media|content creator)\b'}
def title_category(title):
 import re
 hits=[label for label,pattern in TITLE_RULES.items() if re.search(pattern,clean_text(title))]
 return hits[0] if len(hits)==1 else None

def fingerprint(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def load_resumes(path):
 df=pd.read_csv(path,usecols=['ID','Resume_str','Category'],dtype=str).fillna('')
 original=len(df);df['text']=df.Resume_str.map(prepare_resume)
 df=df[df.text.str.len()>0]
 conflicts=df.groupby('text').Category.nunique();ambiguous=set(conflicts[conflicts>1].index)
 df=df[~df.text.isin(ambiguous)].drop_duplicates('text').reset_index(drop=True)
 return df,{'raw':original,'clean':len(df),'conflicting_texts_removed':len(ambiguous)}

def load_jobs(path,max_jobs=6000):
 cols=['job_id','title','description','company_name','location','remote_allowed','formatted_work_type','formatted_experience_level','listed_time','expiry','closed_time','application_url','job_posting_url','skills_desc']
 df=pd.read_csv(path,usecols=lambda c:c in cols,dtype={'job_id':str},low_memory=False).fillna('')
 raw=len(df)
 df=df[(df.description.str.strip().str.len()>0)&(df.title.str.strip().str.len()>0)]
 df=df.drop_duplicates('job_id').copy()
 df['is_internship']=df.formatted_work_type.astype(str).str.upper().eq('INTERNSHIP')|df.formatted_experience_level.astype(str).str.lower().eq('internship')
 df['entry']=df.formatted_experience_level.astype(str).str.lower().eq('entry level')
 df=df[df.is_internship|df.entry].copy()
 df['description']=df.description.map(plain_text)
 df['text']=(df.title+'\n'+df.description+'\n'+df.skills_desc.astype(str)).map(clean_text)
 df=df[df.text.str.len()>0].drop_duplicates(['title','company_name','text']).copy()
 df['proxy_category']=df.title.map(title_category)
 eligible=len(df)
 if max_jobs and len(df)>max_jobs:
  # Preserve rare proxy categories; the remaining positions are sampled from the full catalogue.
  rng=np.random.default_rng(SEED)
  reserved=df[df.proxy_category.notna()].sample(frac=1,random_state=SEED).groupby('proxy_category').head(100)
  remainder=df.drop(index=reserved.index)
  needed=max_jobs-len(reserved)
  if needed<0:reserved=reserved.sample(max_jobs,random_state=SEED);needed=0
  df=pd.concat([reserved,remainder.loc[rng.choice(remainder.index,needed,replace=False)]])
 df=df.sort_values('job_id',kind='stable').reset_index(drop=True)
 now=pd.Timestamp.now(tz='UTC')
 for col in ['listed_time','expiry','closed_time']:
  df[col+'_utc']=pd.to_datetime(pd.to_numeric(df[col],errors='coerce'),unit='ms',utc=True,errors='coerce').astype(str).replace('NaT','')
 expiry=pd.to_datetime(df.expiry_utc,utc=True,errors='coerce')
 df['is_expired']=expiry.notna() & (expiry<now)
 df['eligibility_status']='unverified'
 return df,{'raw':raw,'early_career_unique':eligible,'indexed':len(df),'sampling_seed':SEED,'expired_indexed':int(df.is_expired.sum()),'catalogue_status':'historical_research_not_live'}
