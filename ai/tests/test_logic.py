import pandas as pd
import pytest
from upshift_ai.preprocessing import clean_text,prepare_resume
from upshift_ai.skills import build_lexicon
from upshift_ai.semantic import text_chunks
from upshift_ai.api import RecommendationRequest,SentimentRequest
from pydantic import ValidationError

@pytest.fixture
def lexicon():
 return build_lexicon(pd.DataFrame([
  {'conceptUri':'esco:python','preferredLabel':'Python (computer programming)','altLabels':'Python\nPython programming'},
  {'conceptUri':'esco:sql','preferredLabel':'SQL','altLabels':'Structured query language'},
  {'conceptUri':'esco:java','preferredLabel':'Java (computer programming)','altLabels':'Java'},
 ]).fillna(''))

def test_technical_punctuation():assert clean_text('C++ C# .NET node.js')=='c++ c# .net node.js'
def test_training_and_serving_same_cleaner():assert prepare_resume('SOFTWARE ENGINEER\n\nSkills: .NET and node.js')=='skills .net and node.js'
def test_alias_identity(lexicon):assert lexicon.profile_skills('Python')==lexicon.profile_skills('Python programming')=={'esco:python'}
def test_no_experience_is_not_a_skill(lexicon):assert 'esco:python'not in lexicon.profile_skills('I have no experience with Python.')
def test_not_only_keeps_skill(lexicon):assert 'esco:python'in lexicon.profile_skills('Not only Python but also SQL.')
def test_job_required_vs_preferred(lexicon):
 found=lexicon.job_skills('Requirements:\nPython and SQL are required.\nNice to have:\nJava preferred.')
 assert set(found['required'])=={'esco:python','esco:sql'}
 assert set(found['preferred'])=={'esco:java'}
def test_negated_requirement(lexicon):assert 'esco:python'not in lexicon.job_skills('Python is not required.')['required']
def test_company_mentions_are_not_requirements(lexicon):assert not lexicon.job_skills('About us:\nOur company built a Python tool.')['required']
def test_unknown_alias_collision_excluded():
 frame=pd.DataFrame([{'conceptUri':'a','preferredLabel':'data systems','altLabels':'shared phrase'},{'conceptUri':'b','preferredLabel':'computing systems','altLabels':'shared phrase'}]).fillna('')
 lex=build_lexicon(frame);assert 'shared phrase'not in lex.aliases
def test_chunks_cover_start_and_end():
 words=[str(i)for i in range(2000)];chunks=text_chunks(' '.join(words));assert len(chunks)==4;assert chunks[0].startswith('0 ');assert chunks[-1].split()[-1]=='1999'
@pytest.mark.parametrize('payload',[{'resume_text':''},{'resume_text':' '},{'resume_text':'x','top_k':True},{'resume_text':'x','top_k':0},{'resume_text':'x','method':'invalid'},{'resume_text':'x','min_similarity':float('nan')}])
def test_invalid_recommendation_requests(payload):
 with pytest.raises(ValidationError):RecommendationRequest(**payload)
def test_sentiment_blank():
 with pytest.raises(ValidationError):SentimentRequest(text=' ')

def test_joint_negation_does_not_invent_requirements(lexicon):
 found=lexicon.job_skills("Python and SQL are not required.")
 assert not found["required"]
 assert set(found["excluded"])=={"esco:python","esco:sql"}
 mixed=lexicon.job_skills('Python is required and SQL is not required.')
 assert set(mixed['required'])=={'esco:python'}
 assert set(mixed['excluded'])=={'esco:sql'}
