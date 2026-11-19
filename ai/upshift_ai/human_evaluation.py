"""Optional human evaluations, kept separate from proxy and synthetic tests."""
from pathlib import Path
import json
import pandas as pd

def evaluate_relevance(labels_path,rankings_path,output_path):
 labels=pd.read_csv(labels_path,dtype={'resume_id':str,'job_id':str})
 if not {'resume_id','job_id','relevant'}.issubset(labels):raise ValueError('Need resume_id, job_id and relevant columns.')
 if labels.duplicated(['resume_id','job_id']).any():raise ValueError('Adjudicate duplicate judgements first.')
 if not labels.relevant.isin([0,1]).all():raise ValueError('Use independently assigned 0/1 relevance labels, without blanks.')
 lookup=labels.set_index(['resume_id','job_id']).relevant.to_dict()
 rankings=pd.read_csv(rankings_path,dtype={'resume_id':str,'job_id':str});rows=[]
 for (rid,method),group in rankings.groupby(['resume_id','method']):
  ids=group.sort_values('rank').head(5).job_id.tolist();complete=len(ids)==5 and all((rid,jid)in lookup for jid in ids)
  rows.append({'resume_id':rid,'method':method,'complete_top5':complete,'precision_at_5':sum(lookup[(rid,jid)]for jid in ids)/5 if complete else None})
 result=pd.DataFrame(rows);result.to_csv(output_path,index=False)
 return result

def evaluate_skill_sets(annotation_path):
 data=pd.read_csv(annotation_path).fillna('')
 # Blank means unannotated; [] explicitly means an annotated document with no skills.
 data=data[data.expected_ids_json.ne('')]
 tp=fp=fn=0
 for row in data.itertuples():
  expected=set(json.loads(row.expected_ids_json));predicted=set(json.loads(row.predicted_ids_json))
  tp+=len(expected&predicted);fp+=len(predicted-expected);fn+=len(expected-predicted)
 return {'annotated_documents':len(data),'precision':tp/(tp+fp)if tp+fp else None,'recall':tp/(tp+fn)if tp+fn else None,'true_positives':tp,'false_positives':fp,'false_negatives':fn}

def skill_annotation_template(bundle,resumes,test,output):
 rows=[]
 for _,row in resumes.loc[test].head(10).iterrows():
  rows.append({'document_id':str(row.ID),'kind':'CV demonstrated skills','text':row.Resume_str,'predicted_ids_json':json.dumps(sorted(bundle['lexicon'].profile_skills(row.Resume_str))),'expected_ids_json':''})
 for i,row in bundle['jobs'].head(10).iterrows():
  rows.append({'document_id':str(row.job_id),'kind':'Job required skills','text':row.description,'predicted_ids_json':json.dumps(bundle['job_skills'][i]['required']),'expected_ids_json':''})
 pd.DataFrame(rows).to_csv(output,index=False)
