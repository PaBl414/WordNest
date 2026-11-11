import concurrent.futures
import tempfile
import unittest
from pathlib import Path
from wordnest.core import Store, Problem, norm

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.temp.name)/'test.sqlite3')
    def tearDown(self): self.temp.cleanup()
    def expected(self,ident):
        import json
        with self.store.db() as db:
            return json.loads(db.execute('SELECT questions FROM sessions WHERE id=?',(ident,)).fetchone()[0])
    def test_catalog(self):
        for lang in ('en','de','es'):
            self.assertEqual(self.store.words(lang)['total'],200)
            self.assertEqual(self.store.words(lang,level='A1')['total'],100)
        self.store.seed()
        self.assertEqual(self.store.words()['total'],200)
    def test_diacritics(self):
        self.assertEqual(norm('  GUTEN   MORGEN '),'guten morgen')
        self.assertNotEqual(norm('sí'),norm('si'))
        self.assertNotEqual(norm('Straße'),norm('strase'))
        self.assertNotEqual(norm('Straße'),norm('strasse'))
        self.assertEqual(norm('cafe\u0301'),norm('café'))
    def test_custom_duplicates_and_edit_conflict(self):
        data={'language':'en','term':'curiosity','meaning':'ciekawość'}
        w=self.store.save_word(data.copy())
        self.assertEqual(w['id'],self.store.save_word(data.copy())['id'])
        edited=self.store.save_word({**w,'meaning':'dociekliwość'},w['id'])
        self.assertEqual(edited['version'],2)
        with self.assertRaises(Problem): self.store.save_word(w,w['id'])
    def test_builtin_protection(self):
        w=self.store.words()['items'][0]
        with self.assertRaises(Problem):self.store.save_word(w,w['id'])
        with self.assertRaises(Problem):self.store.change_word(w['id'],archive=True)
    def test_selection_and_archive(self):
        w=self.store.save_word({'language':'en','term':'unusual','meaning':'niezwykły'})
        self.store.change_word(w['id'],selected=False)
        self.assertEqual(self.store.words(q='unusual',selected=True)['total'],0)
        self.store.change_word(w['id'],archive=True)
        self.assertEqual(self.store.words(q='unusual')['total'],0)
    def test_readding_archived_word_restores_same_entry(self):
        data={'language':'en','term':'restorable','meaning':'do przywrocenia'}
        word=self.store.save_word(data.copy())
        self.store.change_word(word['id'],selected=False)
        self.store.change_word(word['id'],archive=True)
        restored=self.store.save_word(data.copy())
        self.assertEqual(restored['id'],word['id'])
        self.assertFalse(restored['archived'])
        self.assertTrue(restored['selected'])
        self.assertEqual(restored['version'],word['version']+3)
        self.assertEqual(self.store.words(q='restorable',selected=True)['total'],1)
        with self.assertRaises(Problem):
            self.store.save_word({**word,'meaning':'stara wersja'},word['id'])
    def test_every_mode_language_direction(self):
        for lang in ('en','de','es'):
            for direction in ('to_pl','from_pl'):
                for mode in ('flashcards','typing','quiz','matching','test'):
                    s=self.store.create_session(lang,mode,direction)
                    self.assertGreaterEqual(len(s['questions']),2)
    def test_no_test_answers_before_finish(self):
        s=self.store.create_session('en','test','to_pl')
        questions=self.expected(s['id'])
        self.assertNotIn('expected',s['questions'][0])
        s=self.store.answer(s['id'],questions[0]['id'],questions[0]['expected'])
        self.assertNotIn('correct',next(iter(s['answers'].values())))
        for q in questions[1:]:s=self.store.answer(s['id'],q['id'],q['expected'])
        self.assertEqual(s['score'],len(questions))
        self.assertTrue(s['finished'])
        self.assertIn('expected',s['questions'][0])
    def test_idempotent_answer(self):
        s=self.store.create_session('en','typing','to_pl')
        q=self.expected(s['id'])[0]
        self.store.answer(s['id'],q['id'],q['expected'])
        result=self.store.answer(s['id'],q['id'],'wrong')
        self.assertEqual(len(result['answers']),1)
        self.assertTrue(result['answers'][q['id']]['correct'])
    def test_variants_and_punctuation(self):
        w=self.store.save_word({'language':'en','term':'colour','meaning':'kolor','variants':['color']})
        s=self.store.create_session('en','typing','from_pl',topic='Własne')
        s=self.store.answer(s['id'],s['questions'][0]['id'],' COLOR ')
        self.assertEqual(s['score'],1)
    def test_flashcard_schedule_and_no_extra_review(self):
        s=self.store.create_session('en','flashcards','to_pl')
        q=s['questions'][0]
        self.store.answer(s['id'],q['id'],'known')
        self.store.answer(s['id'],q['id'],'again')
        with self.store.db() as db:
            p=db.execute('SELECT * FROM progress WHERE word_id=?',(q['word_id'],)).fetchone()
            self.assertEqual(p['stage'],1)
        s2=self.store.create_session('en','flashcards','to_pl')
        self.assertNotIn(q['word_id'],[x['word_id'] for x in s2['questions']])
    def test_small_pool(self):
        self.store.save_word({'language':'en','term':'unique','meaning':'jedyny'})
        with self.assertRaises(Problem):self.store.create_session('en','test','to_pl',topic='Własne')
        with self.assertRaises(Problem):self.store.create_session('en','matching','to_pl',topic='Własne')
        s=self.store.create_session('en','quiz','to_pl',topic='Własne')
        self.assertEqual(s['questions'][0]['kind'],'typing')
    def test_parallel_answers(self):
        s=self.store.create_session('es','typing','to_pl')
        questions=self.expected(s['id'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(lambda q:self.store.answer(s['id'],q['id'],q['expected']),questions))
        self.assertEqual(self.store.session(s['id'])['score'],20)
    def test_parallel_sessions_independent(self):
        a=self.store.create_session('en','typing','to_pl')
        b=self.store.create_session('en','typing','to_pl')
        q=self.expected(a['id'])[0]
        self.store.answer(a['id'],q['id'],q['expected'])
        self.assertEqual(self.store.session(b['id'])['answers'],{})
    def test_snapshot_and_persistence(self):
        w=self.store.save_word({'language':'en','term':'bright','meaning':'jasny'})
        s=self.store.create_session('en','typing','to_pl',topic='Własne')
        self.store.save_word({**w,'meaning':'błyskotliwy'},w['id'])
        self.store=Store(Path(self.temp.name)/'test.sqlite3')
        s=self.store.answer(s['id'],s['questions'][0]['id'],'jasny')
        self.assertEqual(s['score'],1)
        self.assertEqual(self.store.stats('en')['sessions'],1)
    def test_quiz_options(self):
        for lang in ('en','de','es'):
            s=self.store.create_session(lang,'quiz','from_pl')
            for q in self.expected(s['id']):
                self.assertEqual(len(q['options']),4)
                self.assertEqual(len(set(map(norm,q['options']))),4)
                self.assertIn(q['expected'],q['options'])

if __name__=='__main__':unittest.main()
