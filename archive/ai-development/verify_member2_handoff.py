"""Run inside the extracted delivery: python verify_member2_handoff.py."""
from pathlib import Path
import os, json, hashlib
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
from upshift_ai.handoff import ModelService
from fastapi.testclient import TestClient
from member2_api import create_app


def main():
    root=Path(__file__).resolve().parent
    for name,expected in json.loads((root/'SHA256SUMS.json').read_text()).items():
        h=hashlib.sha256()
        with (root/name).open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==expected,f'Checksum mismatch: {name}'
    request=json.loads((root/'sample_request.json').read_text())
    expected=json.loads((root/'sample_response.json').read_text())
    client=TestClient(create_app(root/'artifacts',token='offline-verification-only'))
    assert client.get('/health').status_code==200
    assert client.post('/recommendations',json=request).status_code==401
    result=client.post('/recommendations',headers={'Authorization':'Bearer offline-verification-only'},json=request)
    assert result.status_code==200,result.text
    actual=result.json()
    assert actual['method']==expected['method']
    assert [x['job_id'] for x in actual['matches']]==[x['job_id'] for x in expected['matches']]
    assert all(abs(a['similarity']-b['similarity'])<1e-5 for a,b in zip(actual['matches'],expected['matches']))
    assert all('required_skills_not_mentioned' in x for x in actual['matches'])
    print('PASS: file checksums, offline reload, selected method, API authentication and sample prediction.')


if __name__=='__main__':main()
