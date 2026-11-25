"""Score adjudicated 0/1/2 judgements; refuse incomplete or altered reviews."""
from pathlib import Path
import json, hashlib, math
import pandas as pd

ROOT=Path(__file__).resolve().parent/'student_review'

def main():
    manifest=json.loads((ROOT/'private/manifest.json').read_text())
    for name in ['student_profiles.csv','private/rankings_private.csv','private/retrieval_counts.csv']:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest['files'][name], f'Frozen input changed: {name}'
    ratings=[]
    expected=pd.read_csv(ROOT/'private/adjudication_template.csv').pair_id
    for n in (1,2):
        meta=json.loads((ROOT/f'reviewer_{n}/reviewer_identity.json').read_text())
        if meta['reviewer_type'] not in ['human','ai_assisted']:
            raise ValueError('Record reviewer_type as human or ai_assisted; never disguise an AI review.')
        frame=pd.read_csv(ROOT/f'reviewer_{n}/reviewer_ratings.csv')
        if frame.pair_id.duplicated().any() or set(frame.pair_id)!=set(expected):raise ValueError('Reviewer pairs changed.')
        if not frame.relevance.isin([0,1,2]).all():raise ValueError(f'Reviewer {n}: missing/invalid ratings; resolve uncertainty before scoring.')
        for col,allowed in [('eligibility',['eligible','ineligible','unknown']),('availability',['active','expired','unknown'])]:
            if not frame[col].isin(allowed).all():raise ValueError(f'Reviewer {n}: complete {col}.')
        ratings.append((frame.set_index('pair_id'),meta))
    final_path=ROOT/'private/adjudication_completed.csv'
    if not final_path.exists():raise ValueError('Create private/adjudication_completed.csv after discussing disagreements; do not score the blank template.')
    final=pd.read_csv(final_path)
    if final.pair_id.duplicated().any() or set(final.pair_id)!=set(expected):raise ValueError('Adjudication pairs changed.')
    if not final.final_relevance.isin([0,1,2]).all():raise ValueError('Complete every final relevance rating with 0, 1 or 2.')
    for col,allowed in [('final_eligibility',['eligible','ineligible','unknown']),('final_availability',['active','expired','unknown'])]:
        if not final[col].isin(allowed).all():raise ValueError(f'Complete adjudicated {col}.')
    for n,(frame,meta) in enumerate(ratings,1):
        actual=final.pair_id.map(frame.relevance)
        if not actual.eq(final[f'reviewer_{n}_relevance']).all():raise ValueError('Adjudication reviewer columns must match original reviewer sheets.')
    disagree=final.reviewer_1_relevance.ne(final.reviewer_2_relevance)
    if final.loc[disagree,'resolution_reason'].fillna('').str.strip().eq('').any():raise ValueError('Explain adjudicated disagreements.')
    lookup=final.set_index('pair_id').final_relevance.to_dict()
    rankings=pd.read_csv(ROOT/'private/rankings_private.csv')
    rankings=rankings[rankings.split.ne('calibration')]
    counts=pd.read_csv(ROOT/'private/retrieval_counts.csv'); counts=counts[counts.split.ne('calibration')]
    metrics=[]
    for c in counts.itertuples():
        g=rankings[(rankings.profile_id==c.profile_id)&(rankings.method==c.method)].sort_values('rank').head(5)
        grades=[int(lookup[p]) for p in g.pair_id]
        pool=rankings[rankings.profile_id==c.profile_id].pair_id.drop_duplicates()
        ideal=sorted([int(lookup[p])for p in pool],reverse=True)[:5]
        def dcg(v):return sum((2**r-1)/math.log2(i+2)for i,r in enumerate(v))
        denominator=dcg(ideal)
        metrics.append({'profile_id':c.profile_id,'split':c.split,'method':c.method,'precision_at_5':sum(v==2 for v in grades)/5,'pooled_ndcg_at_5':dcg(grades)/denominator if denominator else 0.0,'returned':len(grades),'result_coverage':int(bool(grades)),'good_match_coverage':int(any(v==2 for v in grades))})
    output=ROOT/'results';output.mkdir(exist_ok=True)
    per=pd.DataFrame(metrics);per.to_csv(output/'per_profile_metrics.csv',index=False)
    summary=per.groupby(['split','method']).agg(precision_at_5=('precision_at_5','mean'),pooled_ndcg_at_5=('pooled_ndcg_at_5','mean'),result_coverage=('result_coverage','mean'),good_match_coverage=('good_match_coverage','mean'),profiles=('profile_id','count')).reset_index()
    validation=summary[summary.split.eq('validation')].sort_values(['pooled_ndcg_at_5','precision_at_5','method'],ascending=[False,False,True])
    selected=validation.iloc[0].method
    from sklearn.metrics import cohen_kappa_score
    report={'status':'evaluated','selected_method':selected,'selection_split':'validation','test_result':summary[(summary.split.eq('test'))&(summary.method.eq(selected))].to_dict('records'),'reviewers':[m for _,m in ratings],'exact_agreement':float((final.reviewer_1_relevance==final.reviewer_2_relevance).mean()),'weighted_kappa':None,'limits':['12 fictional student profiles; six validation and six held-out test profiles','Pooled NDCG uses the union of both methods top-five candidates, not the whole catalogue','Historical catalogue: relevance scores do not establish live vacancy availability','AI-assisted ratings, if present, are not a second human review']}
    k=float(cohen_kappa_score(final.reviewer_1_relevance,final.reviewer_2_relevance,weights='quadratic'))
    report['weighted_kappa']=k if math.isfinite(k) else None
    summary.to_csv(output/'summary.csv',index=False)
    (output/'evaluation.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(summary.to_string(index=False));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
