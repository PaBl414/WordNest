"""Persistence and learning rules; deliberately independent of HTTP and UI."""
from __future__ import annotations
import json
import random
import sqlite3
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

LANGUAGES = {'en': 'Angielski', 'de': 'Niemiecki', 'es': 'Hiszpański'}
INTERVALS = [1, 3, 7, 14, 30]

def now():
    return datetime.now(timezone.utc)

def norm(value):
    return ' '.join(unicodedata.normalize('NFC', value).strip().lower().split())

class Problem(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            if db.execute('PRAGMA user_version').fetchone()[0] > 2:
                raise Problem('Ta baza pochodzi z nowszej wersji WordNest. Zaktualizuj aplikację.')
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS words(id TEXT PRIMARY KEY, language TEXT NOT NULL, term TEXT NOT NULL, meaning TEXT NOT NULL, variants TEXT NOT NULL DEFAULT '[]', polish_variants TEXT NOT NULL DEFAULT '[]', topic TEXT NOT NULL, level TEXT NOT NULL, example TEXT NOT NULL DEFAULT '', example_pl TEXT NOT NULL DEFAULT '', source TEXT NOT NULL, selected INTEGER NOT NULL DEFAULT 1, archived INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 1, normalized TEXT NOT NULL, UNIQUE(language, normalized));
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, language TEXT NOT NULL, mode TEXT NOT NULL, direction TEXT NOT NULL, questions TEXT NOT NULL, answers TEXT NOT NULL DEFAULT '{}', finished INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS progress(word_id TEXT NOT NULL REFERENCES words(id), direction TEXT NOT NULL, stage INTEGER NOT NULL, due TEXT NOT NULL, reviewed TEXT NOT NULL, PRIMARY KEY(word_id,direction));
            CREATE TABLE IF NOT EXISTS dictionary_cache(term TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched REAL NOT NULL, used REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS word_filters ON words(language,archived,selected,topic,level);
            CREATE TABLE IF NOT EXISTS word_sets(id TEXT PRIMARY KEY, language TEXT NOT NULL, name TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS set_words(set_id TEXT NOT NULL REFERENCES word_sets(id), word_id TEXT NOT NULL REFERENCES words(id), PRIMARY KEY(set_id,word_id));
            PRAGMA user_version=2;
            ''')
        self.seed()

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def seed(self):
        from .vocabulary import entries
        with self.db() as db:
            for item in entries():
                ident = str(uuid.uuid5(uuid.NAMESPACE_URL, 'wordnest:' + item['language'] + ':' + item['term']))
                db.execute('INSERT OR IGNORE INTO words(id,language,term,meaning,topic,level,source,normalized) VALUES(?,?,?,?,?,?,?,?)', (ident,item['language'],item['term'],item['meaning'],item['topic'],item['level'],'builtin',norm(item['term'])+'|'+norm(item['meaning'])))

    def sets(self, language):
        if language not in LANGUAGES: raise Problem('Nieznany jezyk.')
        with self.db() as db:
            result=[{'id':'builtin','name':'Wbudowany (200 slow)','count':db.execute("SELECT count(*) FROM words WHERE language=? AND source='builtin' AND archived=0",(language,)).fetchone()[0]},
                    {'id':'custom','name':'Wszystkie wlasne slowa','count':db.execute("SELECT count(*) FROM words WHERE language=? AND source='custom' AND archived=0",(language,)).fetchone()[0]}]
            result += [dict(r) for r in db.execute('SELECT s.id,s.name,(SELECT count(*) FROM set_words sw JOIN words w ON w.id=sw.word_id WHERE sw.set_id=s.id AND w.archived=0) AS count FROM word_sets s WHERE s.language=? ORDER BY s.name,s.id',(language,))]
        return result

    def create_set(self, language, name):
        if not isinstance(language,str) or language not in LANGUAGES: raise Problem('Nieznany jezyk.')
        if not isinstance(name,str) or not name.strip() or len(name.strip())>100: raise Problem('Nazwa zbioru musi miec 1-100 znakow.')
        ident=str(uuid.uuid4())
        with self.db() as db:
            db.execute('INSERT INTO word_sets VALUES(?,?,?)',(ident,language,name.strip()))
        return {'id':ident,'name':name.strip(),'count':0}

    def set_filter(self, db, language, set_id):
        if not isinstance(set_id,str): raise Problem('Nieprawidlowy zbior.')
        if not set_id: return '',[]
        if set_id in ('builtin','custom'): return ' AND source=?',[set_id]
        if not db.execute('SELECT 1 FROM word_sets WHERE id=? AND language=?',(set_id,language)).fetchone(): raise Problem('Nie znaleziono zbioru dla tego jezyka.',404)
        return ' AND id IN (SELECT word_id FROM set_words WHERE set_id=?)',[set_id]

    def builtin_candidates(self, set_id, q=''):
        with self.db() as db:
            group=db.execute('SELECT language FROM word_sets WHERE id=?',(set_id,)).fetchone()
            if not group: raise Problem('Nie znaleziono wlasnego zbioru.',404)
            members={r[0] for r in db.execute('SELECT word_id FROM set_words WHERE set_id=?',(set_id,))}
        result=self.words(group['language'],q=q,set_id='builtin',limit=20)
        for word in result['items']: word['in_set']=word['id'] in members
        return result

    def add_builtin_to_set(self, set_id, word_id):
        if not isinstance(word_id,str): raise Problem('Wybierz slowo.')
        with self.db() as db:
            word=db.execute("SELECT * FROM words WHERE id=? AND source='builtin' AND archived=0",(word_id,)).fetchone()
            if not word: raise Problem('Nie znaleziono wbudowanego slowa.',404)
            self.attach_to_set(db,word_id,word['language'],set_id)
        return {'ok':True}

    def attach_to_set(self, db, word_id, language, set_id):
        if not set_id: return
        if not isinstance(set_id,str) or not db.execute('SELECT 1 FROM word_sets WHERE id=? AND language=?',(set_id,language)).fetchone(): raise Problem('Wybierz wlasny zbior dla tego jezyka.')
        db.execute('INSERT OR IGNORE INTO set_words VALUES(?,?)',(set_id,word_id))

    @staticmethod
    def word(row):
        value = dict(row)
        for key in ('variants', 'polish_variants'):
            value[key] = json.loads(value[key])
        value['selected'] = bool(value['selected'])
        return value

    def words(self, language='en', q='', topic='', level='', selected=False, page=1, limit=50, set_id=""):
        if not isinstance(language,str) or language not in LANGUAGES:
            raise Problem('Nieznany język.')
        limit, page = min(100, max(1,limit)), max(1,page)
        sql, params = 'FROM words WHERE archived=0 AND language=?', [language]
        if q:
            sql += ' AND normalized LIKE ?'
            params.append('%'+norm(q)+'%')
        for name,value in [('topic',topic),('level',level)]:
            if value:
                sql += f' AND {name}=?'
                params.append(value)
        if selected:
            sql += ' AND selected=1'
        with self.db() as db:
            clause,extra=self.set_filter(db,language,set_id)
            sql+=clause; params+=extra
            total = db.execute('SELECT count(*) '+sql,params).fetchone()[0]
            rows = db.execute('SELECT * '+sql+' ORDER BY topic,level,term LIMIT ? OFFSET ?',params+[limit,(page-1)*limit]).fetchall()
        return {'items':[self.word(x) for x in rows], 'total':total, 'page':page, 'limit':limit}

    def save_word(self, data, ident=None):
        language = data.get('language')
        if not isinstance(language,str) or language not in LANGUAGES:
            raise Problem('Wybierz język.')
        for field,maximum in [('term',200),('meaning',200),('example',1000),('example_pl',1000),('topic',100)]:
            value = data.get(field,'Własne' if field=='topic' else '')
            if not isinstance(value,str) or len(value.strip())>maximum or (field in ('term','meaning','topic') and not value.strip()):
                raise Problem('Nieprawidłowe pole: '+field)
            data[field] = value.strip()
        if data.get('level','A1') not in ('A1','A2'):
            raise Problem('Poziom musi być A1 lub A2.')
        for field in ('variants','polish_variants'):
            values = data.get(field,[])
            if not isinstance(values,list) or len(values)>20 or any(not isinstance(v,str) or not v.strip() or len(v)>200 for v in values):
                raise Problem('Nieprawidłowe warianty odpowiedzi.')
        normalized = norm(data['term'])+'|'+norm(data['meaning'])
        with self.db() as db:
            if ident:
                row = db.execute('SELECT * FROM words WHERE id=?',(ident,)).fetchone()
                if not row: raise Problem('Nie znaleziono słowa.',404)
                if row['source']!='custom': raise Problem('Skopiuj wbudowane słowo, aby je edytować.',403)
                if row['version']!=data.get('version'): raise Problem('Słowo zmieniono na innym urządzeniu. Odśwież.',409)
            duplicate = db.execute('SELECT * FROM words WHERE language=? AND normalized=? AND id!=?',(language,normalized,ident or '')).fetchone()
            if duplicate:
                if ident: raise Problem('Takie słowo już istnieje.',409)
                if duplicate['archived']:
                    db.execute('UPDATE words SET archived=0,selected=1,version=version+1 WHERE id=?',(duplicate['id'],))
                    duplicate = db.execute('SELECT * FROM words WHERE id=?',(duplicate['id'],)).fetchone()
                self.attach_to_set(db,duplicate['id'],language,data.get('set_id',''))
                return self.word(duplicate)
            values = (language,data['term'],data['meaning'],json.dumps(data.get('variants',[])),json.dumps(data.get('polish_variants',[])),data['topic'],data.get('level','A1'),data['example'],data['example_pl'],normalized)
            if ident:
                db.execute('UPDATE words SET language=?,term=?,meaning=?,variants=?,polish_variants=?,topic=?,level=?,example=?,example_pl=?,normalized=?,version=version+1 WHERE id=?',values+(ident,))
            else:
                ident = str(uuid.uuid4())
                db.execute('INSERT INTO words(language,term,meaning,variants,polish_variants,topic,level,example,example_pl,normalized,id,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',values+(ident,'custom'))
            self.attach_to_set(db,ident,language,data.get('set_id',''))
            return self.word(db.execute('SELECT * FROM words WHERE id=?',(ident,)).fetchone())

    def change_word(self, ident, selected=None, archive=False):
        with self.db() as db:
            row=db.execute('SELECT * FROM words WHERE id=?',(ident,)).fetchone()
            if not row: raise Problem('Nie znaleziono słowa.',404)
            if archive:
                if row['source']!='custom': raise Problem('Wbudowane słowo można wyłączyć z kolekcji.',403)
                db.execute('UPDATE words SET archived=1,version=version+1 WHERE id=?',(ident,))
            else:
                db.execute('UPDATE words SET selected=?,version=version+1 WHERE id=?',(int(bool(selected)),ident))

    def create_session(self, language, mode, direction, topic='', level='', set_id=''):
        if not isinstance(language,str) or language not in LANGUAGES or mode not in ('flashcards','quiz','typing','matching','test') or direction not in ('to_pl','from_pl'):
            raise Problem('Nieprawidłowe ustawienia nauki.')
        with self.db() as db:
            clause,extra=self.set_filter(db,language,set_id)
            rows=db.execute('SELECT * FROM words WHERE language=? AND selected=1 AND archived=0'+clause+' ORDER BY id',[language]+extra).fetchall()
            pool=[self.word(r) for r in rows if (not topic or r['topic']==topic) and (not level or r['level']==level)]
            if not pool: raise Problem('Dodaj słowa do kolekcji lub zmień filtry.')
            if mode=='test' and len(pool)<4: raise Problem('Test wymaga minimum 4 słów.')
            random.shuffle(pool)
            if mode=='flashcards':
                progress={r['word_id']:dict(r) for r in db.execute('SELECT * FROM progress WHERE direction=?',(direction,))}
                pool=[w for w in pool if w['id'] not in progress or progress[w['id']]['due']<=now().isoformat()]
                pool.sort(key=lambda w:(w['id'] not in progress,progress.get(w['id'],{}).get('due','')))
                if not pool: raise Problem('Wszystkie fiszki powtórzone. Wróć później lub wybierz inny tryb.')
            questions=[]
            if mode=='matching':
                left,right=set(),set()
                unique=[]
                for w in pool:
                    if norm(w['term']) not in left and norm(w['meaning']) not in right:
                        unique.append(w); left.add(norm(w['term'])); right.add(norm(w['meaning']))
                pool=unique[:5]
                if len(pool)<2: raise Problem('Dopasowywanie wymaga co najmniej 2 jednoznacznych par.')
            for i,w in enumerate(pool[:20]):
                prompt=w['term'] if direction=='to_pl' else w['meaning']
                answer=w['meaning'] if direction=='to_pl' else w['term']
                variants=w['polish_variants'] if direction=='to_pl' else w['variants']
                kind=('quiz' if i%2==0 else 'typing') if mode=='test' else mode
                options=[]
                if kind=='quiz':
                    accepted={norm(x) for x in [answer]+variants}
                    candidates=list({norm(x['meaning'] if direction=='to_pl' else x['term']):x['meaning'] if direction=='to_pl' else x['term'] for x in pool if norm(x['meaning'] if direction=='to_pl' else x['term']) not in accepted}.values())
                    if len(candidates)<3: kind='typing'
                    else:
                        options=random.sample(candidates,3)+[answer]; random.shuffle(options)
                questions.append({'id':str(uuid.uuid4()),'word_id':w['id'],'kind':kind,'prompt':prompt,'expected':answer,'accepted':[answer]+variants,'options':options,'example':w['example']})
            ident=str(uuid.uuid4())
            db.execute('INSERT INTO sessions(id,language,mode,direction,questions,created) VALUES(?,?,?,?,?,?)',(ident,language,mode,direction,json.dumps(questions),now().isoformat()))
        return self.session(ident)

    def session(self, ident):
        with self.db() as db:
            row=db.execute('SELECT * FROM sessions WHERE id=?',(ident,)).fetchone()
        if not row: raise Problem('Nie znaleziono sesji.',404)
        result=dict(row); questions=json.loads(row['questions']); answers=json.loads(row['answers'])
        result['questions']=[]
        for q in questions:
            visible={k:v for k,v in q.items() if k not in ('accepted','expected')}
            if row['mode'] in ('flashcards','matching') or row['finished'] or (q['id'] in answers and row['mode']!='test'):
                visible['expected']=q['expected']
            result['questions'].append(visible)
        result['answers']={key: ({'value':v['value']} if row['mode']=='test' and not row['finished'] else v) for key,v in answers.items()}
        result['score']=sum(v['correct'] for v in answers.values()) if row['finished'] else None
        return result

    def answer(self, ident, question_id, value):
        if not isinstance(value,str) or len(value)>200: raise Problem('Nieprawidłowa odpowiedź.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM sessions WHERE id=?',(ident,)).fetchone()
            if not row: raise Problem('Nie znaleziono sesji.',404)
            answers=json.loads(row['answers'])
            if question_id in answers: return self.session(ident)
            if row['finished']: raise Problem('Sesja zakończona.',409)
            questions=json.loads(row['questions'])
            question=next((q for q in questions if q['id']==question_id),None)
            if not question: raise Problem('Nieznane pytanie.',404)
            if row['mode']=='flashcards':
                if value not in ('known','again'): raise Problem('Nieprawidłowa ocena fiszki.')
                correct=value=='known'
                p=db.execute('SELECT stage FROM progress WHERE word_id=? AND direction=?',(question['word_id'],row['direction'])).fetchone()
                stage=min((p['stage'] if p else 0)+1,5) if correct else 0
                due=now()+(timedelta(days=INTERVALS[stage-1]) if correct else timedelta(minutes=10))
                db.execute('INSERT INTO progress VALUES(?,?,?,?,?) ON CONFLICT(word_id,direction) DO UPDATE SET stage=excluded.stage,due=excluded.due,reviewed=excluded.reviewed',(question['word_id'],row['direction'],stage,due.isoformat(),now().isoformat()))
            else: correct=norm(value) in {norm(x) for x in question['accepted']}
            answers[question_id]={'value':value,'correct':correct,'at':now().isoformat()}
            db.execute('UPDATE sessions SET answers=?,finished=? WHERE id=?',(json.dumps(answers),int(len(answers)==len(questions)),ident))
        return self.session(ident)

    def stats(self, language):
        with self.db() as db:
            words=db.execute('SELECT count(*),sum(selected) FROM words WHERE language=? AND archived=0',(language,)).fetchone()
            sessions=db.execute('SELECT * FROM sessions WHERE language=? ORDER BY created DESC',(language,)).fetchall()
            due=db.execute('SELECT count(*) FROM progress p JOIN words w ON p.word_id=w.id WHERE w.language=? AND w.archived=0 AND w.selected=1 AND p.due<=?',(language,now().isoformat())).fetchone()[0]
        finished=[s for s in sessions if s['finished']]
        answers=[a for s in finished for a in json.loads(s['answers']).values()]
        history=[{'id':s['id'],'mode':s['mode'],'created':s['created'],'total':len(json.loads(s['questions'])),'score':sum(a['correct'] for a in json.loads(s['answers']).values())} for s in finished[:10]]
        days={a['at'][:10] for a in answers}
        return {'words':words[0],'selected':words[1] or 0,'due':due,'sessions':len(finished),'answers':len(answers),'accuracy':round(100*sum(a['correct'] for a in answers)/len(answers)) if answers else 0,'days':len(days),'history':history}
