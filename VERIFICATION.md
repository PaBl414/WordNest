# Weryfikacja wykonania

Aktualizacja: 11 listopada 2026, Windows, Python 3.12.10, Node.js 24.22.1.

## Wykonano

- 24 testy unittest: 16 testów silnika, 3 testy HTTP oraz 5 testów uruchamiania. Wszystkie przeszły; żaden nie został pominięty.
- Testy HTTP używają FastAPI TestClient, bez połączenia TCP. Sprawdzają utworzenie sesji, nieujawnianie odpowiedzi i odrzucanie nieprawidłowych Host oraz żądań bez tokenu.
- Regresja przywracania zarchiwizowanego słowa: ten sam identyfikator, ponowne włączenie do kolekcji, zmiana wersji i odrzucenie edycji starej wersji.
- Kontrola `start.py --check` z innego katalogu, bez utworzenia bazy; odrzucanie błędnych portów, adresów i podsieci LAN bez tracebacku.
- Parser PowerShell zaakceptował poprawiony setup.ps1. Skrypt używa ASCII, aby uniknąć problemów kodowania w Windows PowerShell 5.1.

## Nadal niewykonane

- Produkcyjny build TypeScript/Vite i testy Playwright: brak zależności frontendowych. Próba npm install zakończyła się EACCES przy połączeniu z registry.npmjs.org; Python zgłasza WinError 10013. Nie wygenerowano package-lock.json ani frontend/dist.
- Wizualna kontrola interfejsu, uruchomienie kompletnej aplikacji i połączenie TCP z serwerem.
- Pełne wykonanie instalatora i start.cmd po udanym buildzie.
- Test działającego słownika online, dostęp z drugiego urządzenia LAN, kontrola routera i zapór, Linux oraz pomiar p95.

## Zmiany

- Instalator sprawdza narzędzia i ich wersje, obsługuje opcjonalną ścieżkę npm-cli.js i na końcu sprawdza gotowość aplikacji.
- Start aplikacji wykrywa brak zależności lub interfejsu przed uruchomieniem serwera. Dodano start.cmd oraz diagnostykę --check.
- Poprawiono walidację LAN i czyszczenie odziedziczonej konfiguracji LAN przy uruchamianiu lokalnym.
- Playwright wybiera interpreter .venv; poprawiono selektor przycisku fiszek. Zmiany te czekają na wykonanie testów przeglądarkowych.

Odstępstwa od pierwotnego planu pozostają: sqlite3 zamiast SQLAlchemy/Alembic, wspólne CSS zamiast CSS Modules i ręcznie typowany klient API. Katalog 600 słów wymaga niezależnego przeglądu językowego.

## Przygotowanie EXE

- 29 testów unittest przeszło (w tym 5 testów danych i konfiguracji wersji desktopowej).
- Produkcyjny build frontendu zakończył się poprawnie: TypeScript i Vite 7.1.12. package-lock.json jest już obecny.
- Launcher `desktop.py --smoke-test` uruchomił prawdziwy serwer TCP, pobrał stronę główną i poprawnie zatrzymał serwer; kod wyjścia 0. Dane testowe były odizolowane w work.
- Parser PowerShell zaakceptował build-exe.ps1.
- Wcześniejsze wpisy o braku buildu i nieweryfikowanym TCP są historyczne; powyższe kontrole zostały wykonane po pojawieniu się zależności frontendowych.
- Gotowy EXE nie został jeszcze zbudowany: PyInstaller nie jest dostępny w środowisku, a próba jego instalacji zakończyła się błędem. Skrypt budowania wykonuje test gotowej paczki przed komunikatem o powodzeniu.
- Nie sprawdzono okna Windows, otwierania przeglądarki ani uruchomienia na czystym drugim komputerze. Testy Playwright nadal nie zostały wykonane.
- Nowe automatyczne pobieranie Pythona/Node.js przez setup.ps1 wymaga osobnej weryfikacji na komputerze bez tych narzędzi.

## Aktualizacja: terminal i dane obok EXE

- Dane domyslnie w data obok WordNest.exe, niezaleznie od katalogu roboczego. Log rowniez w data.
- Usunieto okna dialogowe, wlaczono terminal i logowanie HTTP; Ctrl+C zatrzymuje serwer.
- 29 testow przeszlo. Nowy dist/WordNest.exe zbudowano i jego test uruchomienia zakonczyl sie kodem 0.
- Starych danych z LOCALAPPDATA nie przenosimy automatycznie.

## Zbiory slow

- Dodano wlasne zbiory per jezyk oraz wybor zbioru w nauce i testach.
- Migracja SQLite 1 -> 2 zachowuje istniejace slowa i sesje.
- Przeszlo 33 testy calego zestawu i dodatkowy test integracji HTTP zbiorow (4 testy HTTP lacznie), razem 34 rozne testy.
- TypeScript i produkcyjny build Vite zakonczone poprawnie.

## Kierunek nauki

- Lista slow odwraca kolejnosc hasla i znaczenia. Kierunek zachowuje sie po odswiezeniu i jest synchronizowany ze wznowiona sesja.
- W aktywnej sesji mozna zmienic kierunek; powstaje nowa sesja, dotychczasowe odpowiedzi pozostaja w bazie.
- Przeszly 34 testy oraz dodatkowa regresja obu kierunkow we wszystkich pieciu trybach (35 roznych testow). Build TypeScript/Vite poprawny.
- Dodano regresje Playwright, ale proba uruchomienia przegladarki zakonczyla sie niepowodzeniem; testow UI nie uznano za zaliczone.

## Wyszukiwanie wbudowanych slow do wlasnego zbioru

- Dodano wyszukiwarke hasel i polskich znaczen w wybranym wlasnym zbiorze.
- Przypisanie przez API jest idempotentne, zachowuje identyfikator slowa i historie. Odrzuca slowa innego jezyka oraz wpisy spoza wbudowanego katalogu.
- 36 testow pelnego zestawu i dodatkowy test HTTP wyszukiwania/przypisywania przeszly (37 roznych testow). TypeScript i Vite poprawne.
- Testy przegladarkowe nowego panelu pozostaja niewykonane.
