import tempfile
import unittest
from pathlib import Path
from wordnest.core import Store, Problem

class SetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'test.sqlite3'
        self.store=Store(self.path)
    def tearDown(self): self.temp.cleanup()
    def test_separate_sets_and_languages(self):
        a=self.store.create_set('en','Travel')
        b=self.store.create_set('en','School')
        word=self.store.save_word({'language':'en','term':'departure gate','meaning':'bramka','set_id':a['id']})
        self.store.save_word({'language':'en','term':'homework','meaning':'zadanie','set_id':b['id']})
        self.assertEqual(self.store.words('en',set_id=a['id'])['total'],1)
        session=self.store.create_session('en','typing','to_pl',set_id=a['id'])
        self.assertEqual([q['prompt'] for q in session['questions']],['departure gate'])
        self.assertEqual(self.store.words('en',set_id='builtin')['total'],200)
        with self.assertRaises(Problem): self.store.create_session('de','typing','to_pl',set_id=a['id'])
        self.assertEqual(self.store.words('en',set_id=b['id'])['items'][0]['term'],'homework')
    def test_duplicate_membership_and_restart(self):
        a=self.store.create_set('en','A'); b=self.store.create_set('en','B')
        data={'language':'en','term':'nebula','meaning':'mglawica'}
        first=self.store.save_word({**data,'set_id':a['id']})
        second=self.store.save_word({**data,'set_id':b['id']})
        self.assertEqual(first['id'],second['id'])
        self.store=Store(self.path)
        self.assertEqual(self.store.words('en',set_id=b['id'])['total'],1)
        self.assertEqual(self.store.words('en',set_id=a['id'])['total'],1)
    def test_invalid_assignment_is_atomic(self):
        with self.assertRaises(Problem):
            self.store.save_word({'language':'en','term':'invalid assignment','meaning':'test','set_id':'missing'})
        self.assertEqual(self.store.words(q='invalid assignment')['total'],0)
        for name in ('',' '*5, 'x'*101):
            with self.assertRaises(Problem): self.store.create_set('en',name)
    def test_version_one_upgrade_preserves_words_and_sessions(self):
        word=self.store.save_word({'language':'en','term':'legacyword','meaning':'stare slowo'})
        session=self.store.create_session('en','typing','to_pl')
        with self.store.db() as db:
            db.execute('DROP TABLE set_words');db.execute('DROP TABLE word_sets');db.execute('PRAGMA user_version=1')
        store=Store(self.path)
        self.assertEqual(store.words(q='legacyword')['items'][0]['id'],word['id'])
        self.assertEqual(store.session(session['id'])['id'],session['id'])
        self.assertEqual(store.sets('en')[0]['count'],200)

    def test_direction_reverses_prompt_and_answer_for_each_mode(self):
        group=self.store.create_set('en','Directions')
        for i in range(4):
            self.store.save_word({'language':'en','term':f'foreign{i}','meaning':f'polish{i}','set_id':group['id']})
        import json
        for mode in ('flashcards','typing','quiz','matching','test'):
            for direction in ('to_pl','from_pl'):
                session=self.store.create_session('en',mode,direction,set_id=group['id'])
                with self.store.db() as db:
                    questions=json.loads(db.execute('SELECT questions FROM sessions WHERE id=?',(session['id'],)).fetchone()[0])
                for q in questions:
                    self.assertTrue(q['prompt'].startswith('polish' if direction=='from_pl' else 'foreign'))
                    self.assertTrue(q['expected'].startswith('foreign' if direction=='from_pl' else 'polish'))

    def test_add_builtin_by_search_without_duplicates(self):
        group=self.store.create_set('en','From catalog')
        word=self.store.words('en',set_id='builtin')['items'][0]
        found=self.store.builtin_candidates(group['id'],word['term'])['items']
        self.assertTrue(any(w['id']==word['id'] and not w['in_set'] for w in found))
        self.store.add_builtin_to_set(group['id'],word['id'])
        self.store.add_builtin_to_set(group['id'],word['id'])
        self.assertEqual(self.store.words('en',set_id=group['id'])['total'],1)
        self.assertEqual(self.store.words('en',set_id='builtin')['total'],200)
        found=self.store.builtin_candidates(group['id'],word['term'])['items']
        self.assertTrue(next(w for w in found if w['id']==word['id'])['in_set'])
        session=self.store.create_session('en','typing','to_pl',set_id=group['id'])
        self.assertEqual(session['questions'][0]['prompt'],word['term'])
        foreign=self.store.words('de',set_id='builtin')['items'][0]
        with self.assertRaises(Problem): self.store.add_builtin_to_set(group['id'],foreign['id'])
        with self.assertRaises(Problem): self.store.builtin_candidates('missing')
        custom=self.store.save_word({'language':'en','term':'not builtin','meaning':'test'})
        with self.assertRaises(Problem): self.store.add_builtin_to_set(group['id'],custom['id'])
