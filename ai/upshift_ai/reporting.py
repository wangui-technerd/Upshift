"""Generate figures only from measured outputs."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BLUE='#2E5AE8';ORANGE='#E0862E';TEAL='#17634F'
def make_figures(results):
 results=Path(results)
 sentiment=pd.read_csv(results/'sentiment_metrics.csv')
 fig,ax=plt.subplots(figsize=(10,5));sentiment.set_index('method')[['accuracy','macro_f1']].plot.bar(ax=ax,color=[BLUE,ORANGE])
 ax.set_ylim(0,1);ax.set_ylabel('Score');ax.set_title('Sentiment comparison — same held-out TweetEval texts');ax.tick_params(axis='x',rotation=18);fig.tight_layout();fig.savefig(results/'sentiment_comparison.png',dpi=160);plt.close(fig)
 reports=json.loads((results/'sentiment_reports.json').read_text())
 fig,axes=plt.subplots(1,2,figsize=(11,4.8))
 for ax,name in zip(axes,['VADER default','TF-IDF + logistic regression']):
  matrix=reports[name]['confusion_matrix'];ax.imshow(matrix,cmap='Blues')
  for i,row in enumerate(matrix):
   for j,count in enumerate(row):ax.text(j,i,str(count),ha='center',va='center',color='white'if count>max(max(r)for r in matrix)/2 else 'black')
  ax.set_xticks(range(3),['negative','neutral','positive'],rotation=30);ax.set_yticks(range(3),['negative','neutral','positive']);ax.set_xlabel('Predicted');ax.set_ylabel('True');ax.set_title(name)
 fig.tight_layout();fig.savefig(results/'sentiment_confusion_matrices.png',dpi=160);plt.close(fig)
 career=pd.read_csv(results/'career_test_metrics.csv')
 fig,ax=plt.subplots(figsize=(9,4.7));career.set_index('model')[['accuracy','macro_f1']].plot.bar(ax=ax,color=[BLUE,TEAL]);ax.set_ylim(0,1);ax.set_title('Supporting CV-category classification — not job-match accuracy');ax.tick_params(axis='x',rotation=18);fig.tight_layout();fig.savefig(results/'career_comparison.png',dpi=160);plt.close(fig)
 if(results/'retrieval_proxy_summary.csv').exists():
  proxy=pd.read_csv(results/'retrieval_proxy_summary.csv')
  fig,ax=plt.subplots(figsize=(7,4));ax.bar(proxy.method,proxy.proxy_category_precision_at_5,color=[BLUE,ORANGE]);ax.set_ylim(0,1);ax.set_ylabel('Category compatibility @5 (weak proxy)');ax.set_title('Retrieval comparison — NOT human relevance accuracy');fig.tight_layout();fig.savefig(results/'retrieval_proxy_comparison.png',dpi=160);plt.close(fig)
 return sorted(p.name for p in results.glob('*.png'))
