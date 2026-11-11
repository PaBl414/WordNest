# WordNest

Lokalna aplikacja do nauki angielskiego, niemieckiego i hiszpańskiego z polskim interfejsem. Wspólny profil bez logowania. 600 wbudowanych pozycji (200 na język), własny słownik, fiszki z powtórkami, quizy, dopasowywanie, wpisywanie i testy mieszane. Dane pozostają na komputerze uruchamiającym serwer.

## Wersja Windows EXE

Budowanie na Windows, z katalogu projektu:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-exe.ps1
```

Skrypt wykonuje setup, instaluje PyInstaller do `.venv`, pakuje program oraz sprawdza uruchomienie gotowego EXE z osobną bazą testową. Jeśli setup został już wykonany, można dodać `-SkipSetup`.

Wynik: `dist/WordNest.exe`. Odbiorcy przekazujesz tylko ten plik. Python, biblioteki i zbudowany interfejs są w środku; odbiorca nie potrzebuje Pythona, Node.js, npm ani uprawnień administratora.

Dwuklik uruchamia lokalny serwer na wolnym porcie i otwiera przeglądarkę. Terminal pokazuje adres aplikacji, katalog danych oraz logi żądań HTTP. Ctrl+C lub zamknięcie terminala zatrzymuje program. Nie pojawia się okno dialogowe. Ta wersja uruchamia się lokalnie; do LAN nadal służy `start.py`.

Dane są zapisywane w folderze `data` obok pliku `WordNest.exe`, niezależnie od bieżącego katalogu terminala. Baza: `data/wordnest.sqlite3`; log: `data/wordnest.log`. Katalog programu musi mieć prawo zapisu. Wymiana samego EXE zachowuje dane. Aby przenieść dane ze starej wersji, zatrzymaj program i przenieś spójną kopię bazy z `%LOCALAPPDATA%\WordNest\data` do folderu `data` obok EXE.

EXE rozpakowuje składniki do katalogu tymczasowego podczas startu. Nie dołączamy Twojej bazy do pliku EXE. Po zbudowaniu sprawdź go również na drugim komputerze bez Pythona i Node.js.

## Instalacja ze źródeł

Windows: instalator wykrywa brakujące narzędzia i pobiera lokalne kopie Pythona oraz Node.js z npm do `.tools`. Pakiety Pythona instaluje w `.venv`, a pakiety frontendu w `frontend/node_modules`. Linux: wymagane **Python 3.12 lub 3.13**, **Node.js 22.12+** i npm. Internet jest potrzebny podczas pierwszej instalacji. Nie otwieraj pliku HTML bezpośrednio — aplikacja wymaga serwera.

Windows, PowerShell, w katalogu projektu:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe start.py
```

Linux:

```sh
sh setup.sh
.venv/bin/python start.py
```

Na Windows po instalacji możesz też dwukrotnie kliknąć `start.cmd`. Przy błędzie okno pozostaje otwarte z komunikatem. Parametry LAN można przekazać również do `start.cmd`.

Sprawdzenie instalacji bez uruchamiania serwera i tworzenia bazy:

```powershell
.\.venv\Scripts\python.exe start.py --check
```

Instalator Windows wykorzystuje kompatybilne istniejące narzędzia, a gdy ich brakuje, pobiera lokalne kopie. Nie zmienia systemowego PATH. Usunięcie `.venv`, `.tools` i `frontend/node_modules` usuwa lokalne środowisko i cache; folder `data` zawiera postępy i należy go zachować. Jeśli npm jest dostępny jako osobny plik, można wskazać go parametrem `-NpmCliPath C:\narzedzia\npm\bin\npm-cli.js`. Brak dostępu do rejestru npm wymaga wykonania instalacji w środowisku z dostępem do internetu.

Otwórz **http://127.0.0.1:8000**. Zatrzymanie serwera: Ctrl+C. Dane przetrwają restart. W Linux może być potrzebny systemowy pakiet `python3-venv`.

Instalacja ręczna: utwórz środowisko Python, zainstaluj `requirements.txt`, następnie w katalogu `frontend` wykonaj `npm install` i `npm run build`. Kolejne instalacje używają `npm ci`, jeśli istnieje wygenerowany `package-lock.json`. Zachowaj ten plik przy publikacji, aby przypiąć także zależności przechodnie. W środowisku tworzenia projektu pobieranie zależności było zablokowane, dlatego początkowa paczka nie zawiera wygenerowanej blokady npm ani gotowego buildu.

## Udostępnienie w LAN

Przykład: serwer ma adres `192.168.1.10`, a sieć `192.168.1.0/24`. Zastąp oba rzeczywistymi wartościami. Adres sprawdzisz w ustawieniach sieci systemu (`ipconfig` na Windows, `ip addr` na Linux). Zarezerwuj go w DHCP routera.

Windows:

```powershell
.\.venv\Scripts\python.exe start.py --lan-ip 192.168.1.10 --lan-cidr 192.168.1.0/24
```

Linux:

```sh
.venv/bin/python start.py --lan-ip 192.168.1.10 --lan-cidr 192.168.1.0/24
```

Na telefonie lub drugim komputerze otwórz **http://192.168.1.10:8000**. Urządzenia muszą mieć łączność w tej samej sieci. Sieć gościnna i izolacja klientów WiFi mogą ją blokować.

Adres LAN musi należeć do prywatnej podsieci RFC 1918 z prefiksem /16–/30 i być adresem urządzenia (nie sieci ani rozgłoszeniowym).

Serwer LAN nasłuchuje na wszystkich interfejsach IPv4, ale odrzuca klientów spoza wskazanej podsieci. Bez parametrów LAN uruchamia się tylko na loopback. Nie obsługuje IPv6 ani nagłówków proxy. Dostęp dopuszczony jest przez skonfigurowany adres IPv4, `127.0.0.1` i `localhost`, z właściwym portem.

### Zapora Windows

Najpierw ustaw zaufaną sieć jako prywatną. Nie zgadzaj się na szerokie udostępnienie Pythona we wszystkich sieciach. W PowerShell uruchomionym jako administrator utwórz wąską regułę (dopasuj nazwę interfejsu):

```powershell
New-NetFirewallRule -DisplayName 'WordNest LAN' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -LocalAddress 192.168.1.10 -RemoteAddress 192.168.1.0/24 -InterfaceAlias 'Wi-Fi' -Profile Private
```

Sprawdź, czy nie istnieje wcześniejsza szeroka reguła dopuszczająca port 8000 lub Pythona. Zapora powinna blokować pozostały ruch przychodzący.

### Zapora Linux

W istniejącym zestawie nftables dopuszczaj port TCP 8000 wyłącznie na interfejsie LAN, dla adresu serwera i źródła z właściwej podsieci. Odrzuć ruch do tego portu na pozostałych interfejsach/od innych źródeł. Reguła dopuszczenia w istniejącym łańcuchu `input` powinna mieć warunki:

```text
iifname "wlan0" ip saddr 192.168.1.0/24 ip daddr 192.168.1.10 tcp dport 8000 accept
tcp dport 8000 drop
```

To fragment do włączenia w aktualną konfigurację przed ogólnymi regułami dopuszczenia; nie jest kompletnym skryptem zapory. Zachowaj reguły innych usług. Nie używaj `flush ruleset`. Nazwy interfejsów i konfiguracja utrwalania reguł zależą od instalacji systemu.

### Granice dostępu

Wyłącz przekierowanie portu 8000, UPnP dla tej usługi, DMZ, tunele i udostępnienie przez VPN. Nie stawiaj przed aplikacją proxy. Nie publikuj jej przez GitHub Pages. Sam brak odpowiedzi przez internet nie dowodzi poprawności konfiguracji zapory.

Każdy dopuszczony użytkownik LAN może zmieniać wspólne dane. HTTP jest przeznaczone wyłącznie do zaufanej sieci. Serwer nie może odróżnić zdalnej osoby od lokalnego urządzenia pośredniczącego w jej ruchu.

## Nauka

- Wbudowane słowa są domyślnie w kolekcji. Odznaczenie usuwa je z nauki, ale nie z katalogu.
- Ponowne dodanie zarchiwizowanego słowa przywraca ten sam wpis do kolekcji, zachowując jego historię.
- Własne słowa mogą mieć warianty odpowiedzi oddzielone średnikami. Rodzajniki, diakrytyka, `ñ`, `ß` i umlauty mają znaczenie. Wielkość liter i nadmiar spacji są ignorowane.
- Edycja wbudowanej pozycji tworzy formularz własnego wpisu. Zmień znaczenie lub hasło, ponieważ dokładny duplikat wskazuje istniejący wpis.
- Fiszki mają odstępy 1, 3, 7, 14 i 30 dni. „Powtórz” ustawia termin za 10 minut. Dalsze poprawne powtórki pozostają co 30 dni.
- Quiz i test zastępują pytanie wpisywaniem, gdy brakuje jednoznacznych odpowiedzi do wyboru.
- Dopasowywanie zawiera do 5 par; błędną próbę można poprawić, a wynik podsumowuje ostatecznie dopasowane pary.
- Test ma do 20 pytań, minimum 4 słowa, bez limitu czasu. Wynik jest ujawniany po ostatniej odpowiedzi. Nie ma progu zaliczenia.
- Tylko fiszki zmieniają terminy powtórek. Statystyki obejmują ukończone sesje, a skuteczność również samoocenę fiszek. Dni aktywności są liczone według UTC.
- Aktywna sesja jest zapamiętywana osobno dla karty przeglądarki. Odświeżenie przywraca ostatnią sesję; opuszczenie jej przyciskiem wyboru ćwiczeń usuwa odnośnik z tej karty. Historia zapisanych odpowiedzi pozostaje w bazie.

## Opcjonalny słownik

Dodaj `--dictionary` do polecenia uruchomienia. Przycisk w widoku słów angielskich odpytuje [Free Dictionary API](https://dictionaryapi.dev/) wyłącznie na wyraźne żądanie. Definicje są po angielsku; polskie znaczenie podajesz samodzielnie. Niemiecki i hiszpański korzystają z katalogu lokalnego i własnych słów.

Limit: 2 sekundy, 2 równoczesne zapytania, 30 na minutę. Cache: 7 dni, brak hasła: godzina, maksymalnie 1000 haseł. Przy awarii wynik do 90 dni jest oznaczony jako nieaktualny. Trzy kolejne błędy włączają minutową przerwę. Nie są pobierane nagrania, a przeglądarka nie łączy się bezpośrednio z dostawcą. Awaria słownika nie blokuje lokalnych ćwiczeń. Zapytanie ujawnia dostawcy hasło i publiczny adres IP serwera.

## Baza i kopie

SQLite znajduje się w `data/wordnest.sqlite3`. Nie przenoś aktywnej bazy na udział sieciowy. Alternatywny katalog można ustawić zmienną `WORDNEST_DATA`. Format schematu ma wersję 2 (`PRAGMA user_version`); przyszłe zmiany wymagają jawnej migracji. Warstwa danych używa standardowego `sqlite3`, zamiast zaplanowanego SQLAlchemy/Alembic — pozwala testować cały silnik bez instalowania pakietów.

Kopia na Windows (na Linux użyj `.venv/bin/python`):

```powershell
.\.venv\Scripts\python.exe backup.py backup C:\kopie\wordnest.sqlite3
```

Przy odtworzeniu **zatrzymaj serwer**:

```powershell
.\.venv\Scripts\python.exe backup.py restore C:\kopie\wordnest.sqlite3
```

Kopia używa SQLite Backup API, a nie kopiowania otwartego pliku. Odtwarzanie wymaga potwierdzenia i nie akceptuje pozostawionych plików WAL/SHM.

## Testowanie i rozwój

```sh
python -m unittest discover -s tests -v
```

Testy silnika nie wymagają dodatkowych bibliotek. Testy HTTP wymagają zainstalowanych zależności. `npm run build` sprawdza TypeScript przed budowaniem. Opcjonalnie uruchom serwer Python i `npm run dev` w katalogu frontend, następnie wejdź na `http://127.0.0.1:5173`. Serwer deweloperski jest ograniczony do loopback; do LAN służy wyłącznie produkcyjny build podawany przez Python.

Testy przeglądarkowe: aktywuj środowisko `.venv`, przejdź do `frontend`, wykonaj `npm run build`, `npx playwright install chromium`, następnie `npm run test:e2e`. Uruchamiają osobny serwer na porcie 8010, zapisują dane testowe w `work/e2e-data` i sprawdzają widok komputerowy oraz telefoniczny. Nie były uruchomione w środowisku tworzenia projektu. Konfiguracja automatycznie wybiera Python z `.venv`; opcjonalna zmienna `WORDNEST_PYTHON` pozwala wskazać inny interpreter.

Przed publikacją sprawdź na Windows i Linux: telefon i drugi komputer w LAN, niedozwolona podsieć, fałszywe Host/Origin/X-Forwarded-For, wyłączony internet, równoległe sesje, restart oraz odtworzenie kopii. Zmierz p95 lokalnych żądań przy 10 klientach i 10 000 wpisów; cel wynosi 300 ms. Nie oznaczaj tych kontroli jako wykonanych bez pomiaru.

## Publikacja

Publikuj źródła, instrukcję, testy i wygenerowany `package-lock.json`. `.gitignore` wyklucza dane, kopie w `data`, zależności i build. Kopie zapisuj poza repozytorium. Sprawdź zawartość i historię pod kątem danych prywatnych. Nie publikuj cache słownika ani lokalnych ustawień. Publikacja repozytorium nie oznacza udostępnienia działającego serwera.

## Licencje

Kod projektu: MIT (patrz LICENSE). Wbudowany katalog przygotowano na potrzeby WordNest, CC0 1.0. Oznaczenia A1/A2 są orientacyjne; katalog nie jest certyfikowany i przed użyciem dydaktycznym wymaga przeglądu językowego. Treści pobrane z API zachowują własne licencje i źródła; nie obejmuje ich licencja katalogu. React, Vite, TypeScript, Lucide i zależności Pythona zachowują swoje licencje — ich informacje dołączają pakiety instalowane przez menedżery zależności.

## Zbiory slow

W widoku Slowa wpisz nazwe i kliknij Utworz zbior. Zbior dotyczy aktualnie wybranego jezyka. Wybierz go w polu Zbior slow, a nastepnie dodaj dowolne wlasne slowa przyciskiem Dodaj slowo. Nie musza wystepowac we wbudowanym katalogu.

Ten sam wybor zbioru obowiazuje przy rozpoczynaniu fiszek, quizu, wpisywania, dopasowywania i testu. Zbior Wbudowany zawiera 200 pozycji na jezyk. Wszystkie wlasne slowa obejmuja takze wpisy sprzed aktualizacji. Wszystkie zbiory lacza dostepne slowa bez duplikatow. Filtry tematu, poziomu i zaznaczenie slow do nauki nadal obowiazuja.

Schemat bazy ma wersje 2. Aktualizacja z wersji 1 automatycznie dodaje tabele zbiorow i zachowuje slowa, sesje oraz postepy. Historie powtorek wspoldzieli to samo slowo wystepujace w kilku zbiorach.

W wybranym wlasnym zbiorze sekcja **Dodaj z wbudowanych slow** pozwala wyszukiwac po hasle i polskim znaczeniu. Przycisk **Dodaj do zbioru** przypisuje pozycje bez tworzenia duplikatu. Slowo pozostaje we wbudowanym katalogu i zachowuje historie powtorek.
