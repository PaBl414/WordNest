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
