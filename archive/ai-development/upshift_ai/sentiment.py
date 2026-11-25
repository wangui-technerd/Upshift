"""VADER and trained logistic regression compared on the same TweetEval splits."""
from pathlib import Path
import json,urllib.request,time
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

LABELS=['negative','neutral','positive']
def download_tweeteval(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 manifest=root/'source.json'
 if manifest.exists():revision=json.loads(manifest.read_text())['revision']
 else:
  request=urllib.request.Request('https://api.github.com/repos/cardiffnlp/tweeteval/commits/main',headers={'User-Agent':'Upshift academic benchmark'})
  with urllib.request.urlopen(request,timeout=60)as response:revision=json.load(response)['sha']
  manifest.write_text(json.dumps({'dataset':'TweetEval sentiment / SemEval-2017 Task 4','repository':'https://github.com/cardiffnlp/tweeteval','revision':revision,'use':'external English sentiment benchmark, not evidence of performance on Kenyan app feedback'}))
 for split in ['train','val','test']:
  for kind in ['text','labels']:
   path=root/f'{split}_{kind}.txt'
   if not path.exists():
    url=f'https://raw.githubusercontent.com/cardiffnlp/tweeteval/{revision}/datasets/sentiment/{split}_{kind}.txt'
    with urllib.request.urlopen(url,timeout=90)as response:path.write_bytes(response.read())
 frames={};seen=set();audit={}
 for split in ['train','val','test']:
  texts=(root/f'{split}_text.txt').read_text(encoding='utf-8').splitlines();labels=(root/f'{split}_labels.txt').read_text().splitlines()
  if len(texts)!=len(labels):raise ValueError('Sentiment texts and labels have different lengths.')
  df=pd.DataFrame({'text':texts,'label':[LABELS[int(n)]for n in labels]})
  df['key']=df.text.str.lower().str.replace(r'\s+',' ',regex=True).str.strip()
  before=len(df);conflict=df.groupby('key').label.nunique();ambiguous=set(conflict[conflict>1].index)
  df=df[df.key.ne('')&~df.key.isin(ambiguous)&~df.key.isin(seen)].drop_duplicates('key').copy()
  seen.update(df.key);frames[split]=df.reset_index(drop=True)
  audit[split]={'original':before,'used':len(df),'removed_blank_duplicate_or_conflict':before-len(df),'classes':df.label.value_counts().to_dict()}
 return frames,audit

def vader_labels(vader,texts,threshold=.05):
 values=np.array([vader.polarity_scores(str(text))['compound']for text in texts])
 return np.where(values>=threshold,'positive',np.where(values<=-threshold,'negative','neutral'))

def metric_row(name,true,pred,seconds=None):
 return {'method':name,'accuracy':accuracy_score(true,pred),'macro_f1':f1_score(true,pred,average='macro',zero_division=0),'prediction_seconds':seconds}

def sentiment_benchmark(data_root,results_root):
 results_root=Path(results_root);frames,audit=download_tweeteval(Path(data_root)/'sentiment')
 nltk_root=Path(data_root)/'nltk';nltk_root.mkdir(exist_ok=True)
 nltk.data.path.insert(0,str(nltk_root))
 nltk.download('vader_lexicon',download_dir=str(nltk_root),quiet=True,raise_on_error=True)
 vader=SentimentIntensityAnalyzer();train,val,test=[frames[k]for k in ['train','val','test']]
 candidates=[];models={}
 for c in [.5,2.0]:
  for weight in [None,'balanced']:
   name=f'Logistic regression C={c}, weight={weight}'
   model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=80000,sublinear_tf=True,strip_accents='unicode')),
                   ('classifier',LogisticRegression(C=c,class_weight=weight,max_iter=1000,solver='lbfgs',random_state=42))])
   print('Training sentiment:',name,flush=True);model.fit(train.text,train.label)
   candidates.append(metric_row(name,val.label,model.predict(val.text)));models[name]=model
 dev=pd.DataFrame(candidates).sort_values('macro_f1',ascending=False);best=dev.iloc[0]['method'];model=models[best]
 # Freeze selection on validation data; final test is evaluated only after selection.
 thresholds=[.05,.1,.2,.3]
 threshold=max(thresholds,key=lambda t:f1_score(val.label,vader_labels(vader,val.text,t),average='macro',zero_division=0))
 validation_vader=f1_score(val.label,vader_labels(vader,val.text,threshold),average='macro',zero_division=0)
 selected='logistic'if float(dev.iloc[0].macro_f1)>=validation_vader else 'vader'
 predictors={'Majority baseline':lambda:np.repeat(train.label.mode().iloc[0],len(test)),
  'VADER default':lambda:vader_labels(vader,test.text,.05),
  'VADER validation-tuned':lambda:vader_labels(vader,test.text,threshold),
  'TF-IDF + logistic regression':lambda:model.predict(test.text)}
 rows=[];reports={};predictions=test[['text','label']].copy()
 for name,predict in predictors.items():
  start=time.perf_counter();pred=predict();rows.append(metric_row(name,test.label,pred,time.perf_counter()-start))
  predictions[name]=pred;reports[name]={'classification_report':classification_report(test.label,pred,labels=LABELS,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(test.label,pred,labels=LABELS).tolist()}
 metrics=pd.DataFrame(rows);metrics.to_csv(results_root/'sentiment_metrics.csv',index=False)
 dev.to_csv(results_root/'sentiment_validation.csv',index=False)
 (results_root/'sentiment_reports.json').write_text(json.dumps(reports,indent=2))
 (results_root/'sentiment_data_audit.json').write_text(json.dumps(audit,indent=2))
 predictions.to_csv(results_root/'sentiment_predictions.csv',index=False)
 print(metrics.to_string(index=False),flush=True)
 return {'model':model,'vader':vader,'vader_threshold':float(threshold),'selected':selected,'selected_logistic_parameters':best,'labels':LABELS,'source':json.loads((Path(data_root)/'sentiment/source.json').read_text())},metrics

def analyse_sentiment(bundle,text):
 if not isinstance(text,str)or not text.strip():raise ValueError('Provide non-empty feedback text.')
 if len(text)>10000:raise ValueError('Feedback exceeds 10,000 characters.')
 model=bundle['sentiment'];pipe=model['model']
 probabilities=pipe.predict_proba([text])[0]
 label=str(pipe.classes_[int(np.argmax(probabilities))])
 vader_score=model['vader'].polarity_scores(text)['compound']
 vader_label='positive'if vader_score>=model['vader_threshold'] else 'negative'if vader_score<=-model['vader_threshold']else 'neutral'
 return {'label':label if model['selected']=='logistic'else vader_label,'method':'TF-IDF + logistic regression'if model['selected']=='logistic'else 'VADER validation-tuned',
  'logistic_label':label,'logistic_probabilities':dict(zip(pipe.classes_.tolist(),[float(x)for x in probabilities])),
  'vader_label':vader_label,'vader_compound':float(vader_score),'scope':'external English benchmark; not validated on Kenyan app feedback'}
