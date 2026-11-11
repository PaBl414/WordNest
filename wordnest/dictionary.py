"""Bounded, opt-in dictionary access. No requests happen during learning."""
import asyncio
import json
import time
from collections import deque
from urllib.parse import quote
import httpx
from .core import Problem, norm

class Dictionary:
    def __init__(self, store, enabled=False):
        self.store,self.enabled=store,enabled
        self.active={}
        self.calls=deque()
        self.failures=0
        self.blocked_until=0

    async def lookup(self, term):
        if not self.enabled: raise Problem('Słownik online jest wyłączony.',503)
        term=norm(term)
        if not term or len(term)>100: raise Problem('Podaj hasło o długości 1–100 znaków.')
        stamp=time.time()
        row=await asyncio.to_thread(self.read_cache,term,stamp)
        if row:
            payload=json.loads(row['payload'])
            if stamp-row['fetched']<(3600 if payload.get('missing') else 604800): return {**payload,'cached':True}
        if term in self.active: return await asyncio.shield(self.active[term])
        while self.calls and self.calls[0]<stamp-60: self.calls.popleft()
        if self.blocked_until>stamp or len(self.active)>=2 or len(self.calls)>=30:
            if row and stamp-row['fetched']<7776000: return {**json.loads(row['payload']),'stale':True,'cached':True}
            raise Problem('Słownik jest zajęty. Spróbuj za chwilę.',429)
        task=asyncio.create_task(self.fetch(term,row))
        self.active[term]=task
        self.calls.append(stamp)
        try: return await asyncio.shield(task)
        finally:
            if task.done(): self.active.pop(term,None)
            else: task.add_done_callback(lambda _: self.active.pop(term,None))

    def read_cache(self,term,stamp):
        with self.store.db() as db:
            row=db.execute('SELECT * FROM dictionary_cache WHERE term=?',(term,)).fetchone()
            if row: db.execute('UPDATE dictionary_cache SET used=? WHERE term=?',(stamp,term))
            return dict(row) if row else None

    def write_cache(self,term,payload):
        with self.store.db() as db:
            stamp=time.time()
            db.execute('INSERT OR REPLACE INTO dictionary_cache VALUES(?,?,?,?)',(term,json.dumps(payload),stamp,stamp))
            db.execute('DELETE FROM dictionary_cache WHERE term NOT IN (SELECT term FROM dictionary_cache ORDER BY used DESC LIMIT 1000)')

    async def fetch(self,term,old):
        try:
            async with asyncio.timeout(2):
                async with httpx.AsyncClient(follow_redirects=False,trust_env=False,timeout=1.8) as client:
                    async with client.stream('GET','https://api.dictionaryapi.dev/api/v2/entries/en/'+quote(term,safe='')) as response:
                        if response.status_code==404: payload={'missing':True,'definitions':[]}
                        else:
                            response.raise_for_status()
                            raw=bytearray()
                            async for chunk in response.aiter_bytes():
                                raw.extend(chunk)
                                if len(raw)>524288: raise ValueError('Oversized response')
                            data=json.loads(raw)
                            if not isinstance(data,list): raise ValueError('Invalid dictionary response')
                            definitions=[]
                            for entry in data[:5]:
                                for meaning in entry.get('meanings',[])[:5]:
                                    for definition in meaning.get('definitions',[])[:3]:
                                        if isinstance(definition.get('definition'),str): definitions.append({'definition':definition['definition'][:2000],'example':str(definition.get('example',''))[:1000],'partOfSpeech':str(meaning.get('partOfSpeech',''))[:100]})
                            payload={'missing':False,'definitions':definitions[:10],'sources':data[0].get('sourceUrls',[]),'license':data[0].get('license',{}),'provider':'Free Dictionary API'}
            self.failures=0
            await asyncio.to_thread(self.write_cache,term,payload)
            return payload
        except (TimeoutError,httpx.HTTPError,ValueError,KeyError,TypeError,IndexError,AttributeError):
            self.failures+=1
            if self.failures>=3: self.blocked_until=time.time()+60
            if old and time.time()-old['fetched']<7776000: return {**json.loads(old['payload']),'stale':True,'cached':True}
            raise Problem('Słownik jest niedostępny. Nauka lokalna działa nadal.',503)
