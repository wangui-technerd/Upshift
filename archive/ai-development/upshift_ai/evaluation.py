"""Training and comparison utilities; no student/job relevance labels are invented."""
import json,time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split,StratifiedKFold,GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import ComplementNB
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from .preprocessing import TOKEN_PATTERN,prepare_resume
from .matching import recommend

def career_comparison(resumes,results):
 train,test=train_test_split(resumes.index,test_size=.2,stratify=resumes.Category,random_state=42)
 x=resumes.loc[train,'text'];y=resumes.loc[train,'Category']
 cv=StratifiedKFold(3,shuffle=True,random_state=42)
 configs={
 'Logistic regression':(LogisticRegression(max_iter=2000,random_state=42),{'model__C':[1,10],'model__class_weight':[None,'balanced']}),
 'Linear SVM':(LinearSVC(max_iter=5000,random_state=42),{'model__C':[1,10],'model__class_weight':[None,'balanced']}),
 'Complement Naive Bayes':(ComplementNB(),{'model__alpha':[.1,1]}),
 'Majority baseline':(DummyClassifier(strategy='most_frequent'),{})}
 searches={};rows=[]
 for name,(estimator,params)in configs.items():
  print('Career comparison:',name,flush=True)
  pipe=Pipeline([('tfidf',TfidfVectorizer(token_pattern=TOKEN_PATTERN,ngram_range=(1,2),min_df=2,max_df=.95,max_features=30000,sublinear_tf=True)),('model',estimator)])
  search=GridSearchCV(pipe,params,cv=cv,scoring='f1_macro',n_jobs=1,error_score='raise');search.fit(x,y)
  searches[name]=search;rows.append({'model':name,'cv_macro_f1':float(search.best_score_),'parameters':search.best_params_})
 best=max(rows,key=lambda r:r['cv_macro_f1'])['model'];selected=searches[best].best_estimator_
 reports={};test_rows=[]
 for name,search in searches.items():
  predicted=search.predict(resumes.loc[test,'text']);truth=resumes.loc[test,'Category']
  test_rows.append({'model':name,'accuracy':accuracy_score(truth,predicted),'macro_f1':f1_score(truth,predicted,average='macro',zero_division=0)})
  reports[name]=classification_report(truth,predicted,output_dict=True,zero_division=0)
 pd.DataFrame(rows).to_json(results/'career_validation.json',orient='records',indent=2)
 pd.DataFrame(test_rows).to_csv(results/'career_test_metrics.csv',index=False)
 (results/'career_reports.json').write_text(json.dumps(reports,indent=2))
 resumes.assign(split=np.where(resumes.index.isin(train),'train','test'))[['ID','Category','split']].to_csv(results/'career_split_manifest.csv',index=False)
 print('Career winner selected by CV:',best,flush=True);print(pd.DataFrame(test_rows).to_string(index=False),flush=True)
 return selected,train,test,best

def retrieval_proxy_evaluation(bundle,resumes,test,encoder,results):
 from .data import title_category
 # Category compatibility is explicitly a weak proxy, NOT true recommendation relevance.
 available=set(bundle['jobs'].proxy_category.dropna())
 queries=resumes.loc[test];queries=queries[queries.Category.isin(available)].groupby('Category',group_keys=False).head(4)
 queries[['ID','Resume_str']].rename(columns={'ID':'resume_id','Resume_str':'resume_text'}).to_csv(results/'retrieval_annotation_queries.csv',index=False)
 rows=[];annotation=[];rankings=[]
 for _,row in queries.iterrows():
  for method in ['lexical','semantic']:
   start=time.perf_counter();found=recommend(bundle,row.Resume_str,top_k=5,method=method,encoder=encoder)['matches'];elapsed=time.perf_counter()-start
   hits=sum(title_category(r['title'])==row.Category for r in found)
   rows.append({'resume_id':row.ID,'method':method,'category':row.Category,'proxy_category_precision_at_5':hits/5,'returned':len(found),'latency_seconds':elapsed})
   for rank,r in enumerate(found,1):rankings.append({'resume_id':row.ID,'method':method,'rank':rank,'job_id':r['job_id']})
   for r in found:annotation.append({'resume_id':row.ID,'job_id':r['job_id'],'job_title':r['title'],'job_description':r['description'],'relevant':'','eligibility_review':''})
 pd.DataFrame(rankings).to_csv(results/'retrieval_rankings.csv',index=False)
 metrics=pd.DataFrame(rows);metrics.to_csv(results/'retrieval_proxy_queries.csv',index=False)
 metrics.groupby('method').agg(proxy_category_precision_at_5=('proxy_category_precision_at_5','mean'),queries=('resume_id','count'),median_latency_seconds=('latency_seconds','median')).to_csv(results/'retrieval_proxy_summary.csv')
 sheet=pd.DataFrame(annotation).drop_duplicates(['resume_id','job_id']).sample(frac=1,random_state=42)
 sheet.to_csv(results/'retrieval_annotation_sheet.csv',index=False)
 (results/'relevance_evaluation.json').write_text(json.dumps({'status':'not_evaluated','reason':'No independent human relevance labels supplied. Proxy category compatibility must not be called recommendation accuracy.','annotation_pairs':len(sheet),'queries':len(queries)},indent=2))
 print('Retrieval PROXY metrics:',flush=True);print(pd.read_csv(results/'retrieval_proxy_summary.csv').to_string(index=False),flush=True)
 return metrics
