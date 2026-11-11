"""Windows EXE entry point: local server, browser and connection console."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

from wordnest.paths import data_directory, resource_root


def configure_environment():
    data = data_directory()
    data.mkdir(parents=True, exist_ok=True)
    # Source runs retain their original data/ directory; EXE has its own profile.
    os.environ['WORDNEST_DATA'] = str(data)
    os.environ.pop('WORDNEST_LAN_IP', None)
    os.environ.pop('WORDNEST_LAN_CIDR', None)
    os.environ['WORDNEST_DICTIONARY'] = '0'
    return data


def wait_for_server(url, server, thread, timeout=20):
    # Ignore system proxy settings for the loopback health check.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while thread.is_alive() and time.monotonic() < deadline:
        if server.started:
            try:
                with opener.open(url, timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (OSError, ValueError):
                pass
        threading.Event().wait(0.1)
    raise RuntimeError('Nie udalo sie uruchomic lokalnego serwera WordNest.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='WordNest')
    parser.add_argument('--smoke-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    server = thread = bound_socket = None
    try:
        dist = resource_root() / 'frontend' / 'dist'
        if not (dist / 'index.html').is_file() or not (dist / 'assets').is_dir():
            raise RuntimeError('Brak interfejsu w paczce. Zbuduj WordNest ponownie przez build-exe.ps1.')
        data = configure_environment()
        log = data / 'wordnest.log'
        logging.basicConfig(
            level=logging.INFO,
            handlers=[logging.StreamHandler(sys.stdout), RotatingFileHandler(log, maxBytes=2_000_000, backupCount=2, encoding='utf-8')],
            format='%(asctime)s %(levelname)s %(name)s: %(message)s', force=True,
        )
        # Hold the selected port until Uvicorn takes ownership; no port race.
        bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            bound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        bound_socket.bind(('127.0.0.1', 0))
        port = bound_socket.getsockname()[1]
        os.environ['WORDNEST_PORT'] = str(port)
        from wordnest.app import app
        import uvicorn
        server = uvicorn.Server(uvicorn.Config(
            app, host='127.0.0.1', port=port, proxy_headers=False,
            loop='asyncio', http='h11', ws='none', lifespan='off',
            log_config=None, access_log=True,
        ))
        thread = threading.Thread(target=server.run, kwargs={'sockets': [bound_socket]}, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{port}/'
        wait_for_server(url, server, thread)
        if not args.smoke_test:
            print(f'WordNest: {url}', flush=True)
            print(f'Dane: {data}', flush=True)
            print('Zatrzymanie: Ctrl+C lub zamkniecie terminala.', flush=True)
            if not webbrowser.open(url):
                print('Otworz powyzszy adres w przegladarce.', flush=True)
            while thread.is_alive():
                thread.join(timeout=0.5)
            raise RuntimeError('Serwer WordNest zakonczyl prace niespodziewanie.')
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logging.exception('WordNest startup failed')
        if not args.smoke_test:
            print(f'Nie mozna uruchomic WordNest: {exc}', flush=True)
            try:
                input('Nacisnij Enter, aby zamknac okno...')
            except (EOFError, KeyboardInterrupt):
                pass
        return 1
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=10)
        if bound_socket is not None:
            bound_socket.close()
        logging.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
