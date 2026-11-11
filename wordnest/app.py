from __future__ import annotations
import ipaddress
import os
import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from .core import Store, Problem, LANGUAGES
from .dictionary import Dictionary
from .vocabulary import DATA
from .paths import resource_root, data_directory

ROOT=resource_root()
store=Store(data_directory()/'wordnest.sqlite3')
dictionary=Dictionary(store,os.environ.get('WORDNEST_DICTIONARY')=='1')
token=secrets.token_urlsafe(32)
port=int(os.environ.get('WORDNEST_PORT','8000'))
lan_ip=os.environ.get('WORDNEST_LAN_IP','')
network=ipaddress.ip_network(os.environ['WORDNEST_LAN_CIDR']) if lan_ip else None
hosts={f'127.0.0.1:{port}',f'localhost:{port}'} | ({f'{lan_ip}:{port}'} if lan_ip else set())
app=FastAPI(title='WordNest',version='1.0.0',docs_url=None,redoc_url=None)

@app.exception_handler(Problem)
async def problem_handler(request, exc):
    return JSONResponse({'code':'request_failed','message':exc.message},status_code=exc.status)

@app.exception_handler(RequestValidationError)
async def validation_handler(request,exc):
    return JSONResponse({'code':'validation','message':'Nieprawidłowe dane żądania.'},status_code=422)

@app.middleware('http')
async def protect(request: Request,call_next):
    try: address=ipaddress.ip_address(request.client.host)
    except (ValueError,AttributeError): return JSONResponse({'message':'Brak dostępu.'},status_code=403)
    if not address.is_loopback and (not network or address.version!=4 or address not in network):
        return JSONResponse({'message':'Dostęp tylko z dozwolonej sieci LAN.'},status_code=403)
    host=request.headers.get('host','').lower()
    if host not in hosts: return JSONResponse({'message':'Niedozwolony adres serwera.'},status_code=403)
    if request.method not in ('GET','HEAD','OPTIONS'):
        if request.headers.get('origin')!='http://'+host or not secrets.compare_digest(request.headers.get('x-wordnest-token',''),token):
            return JSONResponse({'message':'Odśwież stronę i spróbuj ponownie.'},status_code=403)
        if request.headers.get('content-type','').split(';')[0]!='application/json':
            return JSONResponse({'message':'Wymagane dane JSON.'},status_code=415)
        try:
            size=int(request.headers.get('content-length','0'))
        except ValueError: size=65537
        if size>65536 or request.headers.get('transfer-encoding'):
            return JSONResponse({'message':'Za duże żądanie.'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    if request.url.path.startswith('/api'): response.headers['Cache-Control']='no-store'
    return response

@app.get('/api/v1/config')
def config(): return {'token':token,'languages':LANGUAGES,'topics':list(DATA),'dictionary':dictionary.enabled}

@app.get('/api/v1/words')
def words(language:str='en',q:str='',topic:str='',level:str='',selected:bool=False,page:int=1,limit:int=50):
    return store.words(language,q,topic,level,selected,page,limit)

@app.post('/api/v1/words')
def create_word(data:dict): return store.save_word(data)

@app.put('/api/v1/words/{ident}')
def update_word(ident:str,data:dict): return store.save_word(data,ident)

@app.patch('/api/v1/words/{ident}')
def select_word(ident:str,data:dict):
    if not isinstance(data.get('selected'),bool): raise Problem('Wymagana wartość selected: true/false.')
    store.change_word(ident,selected=data['selected'])
    return {'ok':True}

@app.delete('/api/v1/words/{ident}')
def delete_word(ident:str):
    store.change_word(ident,archive=True)
    return {'ok':True}

@app.post('/api/v1/sessions')
def create_session(data:dict):
    return store.create_session(data.get('language'),data.get('mode'),data.get('direction'),data.get('topic',''),data.get('level',''))

@app.get('/api/v1/sessions/{ident}')
def get_session(ident:str): return store.session(ident)

@app.post('/api/v1/sessions/{ident}/answers')
def answer(ident:str,data:dict): return store.answer(ident,data.get('question_id'),data.get('value'))

@app.get('/api/v1/stats')
def stats(language:str='en'): return store.stats(language)

@app.post('/api/v1/dictionary')
async def lookup(data:dict):
    if not isinstance(data.get('term'),str): raise Problem('Podaj hasło.')
    return await dictionary.lookup(data['term'])

DIST=ROOT/'frontend'/'dist'
if (DIST/'assets').is_dir(): app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')

@app.get('/')
def index():
    if not (DIST/'index.html').exists():
        return JSONResponse({'message':'Najpierw zbuduj interfejs: cd frontend, npm ci, npm run build.'},status_code=503)
    return FileResponse(DIST/'index.html',headers={'Cache-Control':'no-cache'})
