"""Run: python start.py [--lan-ip 192.168.1.10 --lan-cidr 192.168.1.0/24]."""
import argparse
import os
import ipaddress
import importlib.util
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WordNest — lokalna nauka języków')
    parser.add_argument('--lan-ip')
    parser.add_argument('--lan-cidr')
    parser.add_argument('--dictionary', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--check', action='store_true', help='Sprawdz instalacje bez startowania serwera.')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port musi byc liczba od 1 do 65535.')
    if bool(args.lan_ip) != bool(args.lan_cidr):
        parser.error('Podaj razem --lan-ip i --lan-cidr.')
    if args.lan_ip:
        try:
            network = ipaddress.IPv4Network(args.lan_cidr, strict=True)
            address = ipaddress.IPv4Address(args.lan_ip)
        except ValueError:
            parser.error('Nieprawidlowy adres IPv4 lub podsiec CIDR.')
        private_ranges = [ipaddress.IPv4Network(cidr) for cidr in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
        if (not any(network.subnet_of(private) for private in private_ranges)
                or address not in network or not 16 <= network.prefixlen <= 30
                or address in (network.network_address, network.broadcast_address)):
            parser.error('Podaj konkretną prywatną podsieć LAN (/16 lub mniejszą) i należący do niej adres.')
        os.environ['WORDNEST_LAN_IP'] = str(address)
        os.environ['WORDNEST_LAN_CIDR'] = str(network)
    else:
        os.environ.pop('WORDNEST_LAN_IP', None)
        os.environ.pop('WORDNEST_LAN_CIDR', None)
    missing = [name for name in ('fastapi', 'uvicorn', 'httpx') if importlib.util.find_spec(name) is None]
    root = Path(__file__).resolve().parent
    errors = ['Brak pakietu Python: ' + name for name in missing]
    if not (root / 'frontend' / 'dist' / 'index.html').is_file() or not (root / 'frontend' / 'dist' / 'assets').is_dir():
        errors.append('Brak interfejsu. W katalogu frontend wykonaj npm install i npm run build.')
    if errors:
        print('\n'.join(errors))
        print('Instalacja: Windows - setup.ps1; Linux - sh setup.sh.')
        raise SystemExit(1)
    if args.check:
        print('WordNest: zaleznosci Python i interfejs sa gotowe.')
        raise SystemExit(0)
    import uvicorn
    os.environ['WORDNEST_PORT'] = str(args.port)
    os.environ['WORDNEST_DICTIONARY'] = '1' if args.dictionary else '0'
    print(f'WordNest: http://{args.lan_ip or "127.0.0.1"}:{args.port}')
    if not args.lan_ip:
        print('Tryb lokalny. Dostęp LAN: podaj --lan-ip i --lan-cidr oraz skonfiguruj zaporę.')
    uvicorn.run('wordnest.app:app', host='0.0.0.0' if args.lan_ip else '127.0.0.1', port=args.port, proxy_headers=False)
