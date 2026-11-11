"""Create a consistent database backup or restore while WordNest is stopped."""
import argparse
import sqlite3
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['backup','restore'])
    p.add_argument('file',type=Path)
    p.add_argument('--data',type=Path,default=Path(__file__).parent/'data'/'wordnest.sqlite3')
    args=p.parse_args()
    source,target=(args.data,args.file) if args.action=='backup' else (args.file,args.data)
    if source.resolve()==target.resolve(): p.error('Źródło i cel muszą być różne.')
    if not source.is_file(): p.error('Nie znaleziono źródła.')
    if args.action=='backup' and target.exists(): p.error('Plik docelowy już istnieje.')
    if args.action=='restore':
        if input('Zatrzymaj WordNest. Zastąpić dane? Wpisz TAK: ')!='TAK': raise SystemExit('Anulowano.')
        for suffix in ('-wal','-shm'):
            if Path(str(target)+suffix).exists(): p.error('Wykryto pliki WAL/SHM. Zakończ serwer i sprawdź bazę przed odtworzeniem.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        if src.execute('PRAGMA integrity_check').fetchone()[0]!='ok': p.error('Uszkodzona baza źródłowa.')
        src.backup(dst)
    print('Gotowe:',target)
