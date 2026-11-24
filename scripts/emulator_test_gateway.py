"""Local-only UI test proxy and operator fixture. Never deploy this module.

Run with demo-upshift Auth/Firestore emulators and the real backend on 8122.
Android instrumented tests use 8124 to inject deterministic error scenarios.
"""
import asyncio
import os
from uuid import uuid4
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse

if os.getenv('FIREBASE_AUTH_EMULATOR_HOST')!='127.0.0.1:9099' or os.getenv('FIRESTORE_EMULATOR_HOST')!='127.0.0.1:8080' or os.getenv('UPSHIFT_FIREBASE_PROJECT_ID')!='demo-upshift':
    raise RuntimeError('This test gateway requires isolated local demo-upshift emulators.')

app=FastAPI(docs_url=None,redoc_url=None)
mode='normal'

@app.post('/__test__/mode')
async def set_mode(request:Request):
    global mode
    value=(await request.json()).get('mode')
    if value not in ['normal','empty','slow','unavailable','unauthorized','timeout','invalid']:
        raise HTTPException(400,'Unknown test mode')
    mode=value
    return {'mode':mode}

@app.post('/__test__/approve')
async def approve(request:Request):
    import firebase_admin
    from firebase_admin import auth
    body=await request.json()
    admin=firebase_admin.get_app() if firebase_admin._apps else firebase_admin.initialize_app(options={'projectId':'demo-upshift'})
    async with httpx.AsyncClient(timeout=30,trust_env=False) as client:
        email=f'ui-operator-{uuid4().hex[:10]}@example.test';password=uuid4().hex
        base='http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/'
        account=(await client.post(base+'accounts:signUp?key=emulator',json={'email':email,'password':password,'returnSecureToken':True})).json()
        auth.set_custom_user_claims(account['localId'],{'upshift_admin':True},app=admin)
        signed=(await client.post(base+'accounts:signInWithPassword?key=emulator',json={'email':email,'password':password,'returnSecureToken':True})).json()
        headers={'Authorization':'Bearer '+signed['idToken']}
        if body.get('company_id'):
            path='/listings/admin/companies/'+body['company_id']+'/review';payload={'approved':True}
        else:
            path='/listings/admin/submissions/'+body['submission_id']+'/review';payload={'revision':body['revision'],'decision':'publish','note':'Fictional instrumented UI test only.'}
        result=await client.post('http://127.0.0.1:8122'+path,headers=headers,json=payload)
        return Response(result.content,result.status_code,media_type='application/json')

@app.api_route('/{path:path}',methods=['GET','POST','PUT','PATCH','DELETE'])
async def proxy(path:str,request:Request):
    current=mode
    if path in ['recommendations','sentiment']:
        if current=='slow':await asyncio.sleep(4)
        if current=='empty' and path=='recommendations':return {'status':'no_match','matches':[]}
        codes={'unavailable':503,'unauthorized':401,'timeout':504,'invalid':422}
        if current in codes:return JSONResponse({'error':{'message':'Controlled UI test response'}},status_code=codes[current])
    headers={k:v for k,v in request.headers.items() if k.lower() in ['authorization','content-type']}
    async with httpx.AsyncClient(timeout=60,trust_env=False) as client:
        result=await client.request(request.method,'http://127.0.0.1:8122/'+path,params=request.query_params,content=await request.body(),headers=headers)
    # New sockets make emulator network-loss tests independent of pooled sockets.
    response_headers={k:v for k,v in result.headers.items() if k.lower()=='retry-after'}
    response_headers['Connection']='close'
    return Response(result.content,result.status_code,media_type='application/json',headers=response_headers)
