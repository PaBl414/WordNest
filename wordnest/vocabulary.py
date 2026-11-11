"""Original starter vocabulary. First ten entries per topic: A1, next ten: A2."""
DATA = {
'Podstawowe zwroty': '''hello|hallo|hola|cześć
good morning|guten Morgen|buenos días|dzień dobry
good evening|guten Abend|buenas tardes|dobry wieczór
good night|gute Nacht|buenas noches|dobranoc
goodbye|auf Wiedersehen|adiós|do widzenia
please|bitte|por favor|proszę
thank you|danke|gracias|dziękuję
yes|ja|sí|tak
no|nein|no|nie
sorry|Entschuldigung|perdón|przepraszam
welcome|willkommen|bienvenido|witaj
see you later|bis später|hasta luego|do zobaczenia później
of course|natürlich|por supuesto|oczywiście
perhaps|vielleicht|quizás|być może
never|niemals|nunca|nigdy
always|immer|siempre|zawsze
sometimes|manchmal|a veces|czasami
together|zusammen|juntos|razem
again|wieder|otra vez|ponownie
help|die Hilfe|la ayuda|pomoc''',
'Rodzina': '''mother|die Mutter|la madre|matka
father|der Vater|el padre|ojciec
sister|die Schwester|la hermana|siostra
brother|der Bruder|el hermano|brat
child|das Kind|el niño|dziecko
son|der Sohn|el hijo|syn
daughter|die Tochter|la hija|córka
grandmother|die Großmutter|la abuela|babcia
grandfather|der Großvater|el abuelo|dziadek
family|die Familie|la familia|rodzina
aunt|die Tante|la tía|ciocia
uncle|der Onkel|el tío|wujek
cousin|der Cousin|el primo|kuzyn
parents|die Eltern|los padres|rodzice
husband|der Ehemann|el marido|mąż
wife|die Ehefrau|la esposa|żona
relatives|die Verwandten|los parientes|krewni
granddaughter|die Enkelin|la nieta|wnuczka
grandson|der Enkel|el nieto|wnuk
twins|die Zwillinge|los gemelos|bliźnięta''',
'Dom': '''house|das Haus|la casa|dom
room|das Zimmer|la habitación|pokój
kitchen|die Küche|la cocina|kuchnia
bathroom|das Badezimmer|el baño|łazienka
bed|das Bett|la cama|łóżko
table|der Tisch|la mesa|stół
chair|der Stuhl|la silla|krzesło
door|die Tür|la puerta|drzwi
window|das Fenster|la ventana|okno
garden|der Garten|el jardín|ogród
ceiling|die Decke|el techo|sufit
floor|der Fußboden|el suelo|podłoga
stairs|die Treppe|la escalera|schody
wardrobe|der Kleiderschrank|el armario|szafa
mirror|der Spiegel|el espejo|lustro
fridge|der Kühlschrank|la nevera|lodówka
oven|der Backofen|el horno|piekarnik
washing machine|die Waschmaschine|la lavadora|pralka
balcony|der Balkon|el balcón|balkon
key|der Schlüssel|la llave|klucz''',
'Jedzenie': '''water|das Wasser|el agua|woda
bread|das Brot|el pan|chleb
milk|die Milch|la leche|mleko
cheese|der Käse|el queso|ser
apple|der Apfel|la manzana|jabłko
egg|das Ei|el huevo|jajko
rice|der Reis|el arroz|ryż
fish|der Fisch|el pescado|ryba
tea|der Tee|el té|herbata
coffee|der Kaffee|el café|kawa
breakfast|das Frühstück|el desayuno|śniadanie
lunch|das Mittagessen|el almuerzo|obiad
dinner|das Abendessen|la cena|kolacja
vegetables|das Gemüse|las verduras|warzywa
fruit|das Obst|la fruta|owoce
chicken|das Hähnchen|el pollo|kurczak
salt|das Salz|la sal|sól
sugar|der Zucker|el azúcar|cukier
strawberry|die Erdbeere|la fresa|truskawka
potato|die Kartoffel|la patata|ziemniak''',
'Szkoła': '''school|die Schule|la escuela|szkoła
book|das Buch|el libro|książka
pen|der Kugelschreiber|el bolígrafo|długopis
pencil|der Bleistift|el lápiz|ołówek
notebook|das Heft|el cuaderno|zeszyt
teacher|der Lehrer|el profesor|nauczyciel
student|der Schüler|el alumno|uczeń
lesson|die Unterrichtsstunde|la lección|lekcja
classroom|das Klassenzimmer|el aula|sala lekcyjna
homework|die Hausaufgaben|los deberes|praca domowa
exam|die Prüfung|el examen|egzamin
subject|das Schulfach|la asignatura|przedmiot szkolny
grade|die Note|la nota|ocena
dictionary|das Wörterbuch|el diccionario|słownik
library|die Bibliothek|la biblioteca|biblioteka
break|die Pause|el recreo|przerwa
question|die Frage|la pregunta|pytanie
answer|die Antwort|la respuesta|odpowiedź
mistake|der Fehler|el error|błąd
knowledge|das Wissen|el conocimiento|wiedza''',
'Praca': '''work|die Arbeit|el trabajo|praca
office|das Büro|la oficina|biuro
computer|der Computer|el ordenador|komputer
telephone|das Telefon|el teléfono|telefon
company|die Firma|la empresa|firma
boss|der Chef|el jefe|szef
colleague|der Kollege|el compañero de trabajo|kolega z pracy
job|der Beruf|la profesión|zawód
email|die E-Mail|el correo electrónico|e-mail
meeting|die Besprechung|la reunión|spotkanie służbowe
salary|das Gehalt|el sueldo|wynagrodzenie
contract|der Vertrag|el contrato|umowa
application|die Bewerbung|la solicitud de empleo|podanie o pracę
interview|das Vorstellungsgespräch|la entrevista de trabajo|rozmowa kwalifikacyjna
experience|die Erfahrung|la experiencia|doświadczenie
task|die Aufgabe|la tarea|zadanie
customer|der Kunde|el cliente|klient
invoice|die Rechnung|la factura|faktura
deadline|die Frist|el plazo|termin wykonania
holiday|der Urlaub|las vacaciones|urlop''',
'Podróże': '''train|der Zug|el tren|pociąg
bus|der Bus|el autobús|autobus
car|das Auto|el coche|samochód
airport|der Flughafen|el aeropuerto|lotnisko
ticket|die Fahrkarte|el billete|bilet
hotel|das Hotel|el hotel|hotel
street|die Straße|la calle|ulica
city|die Stadt|la ciudad|miasto
map|die Landkarte|el mapa|mapa
beach|der Strand|la playa|plaża
station|der Bahnhof|la estación|dworzec
suitcase|der Koffer|la maleta|walizka
passport|der Reisepass|el pasaporte|paszport
reservation|die Reservierung|la reserva|rezerwacja
departure|die Abfahrt|la salida|odjazd
arrival|die Ankunft|la llegada|przyjazd
journey|die Reise|el viaje|podróż
border|die Grenze|la frontera|granica
platform|der Bahnsteig|el andén|peron
delay|die Verspätung|el retraso|opóźnienie''',
'Zakupy': '''shop|das Geschäft|la tienda|sklep
money|das Geld|el dinero|pieniądze
price|der Preis|el precio|cena
bag|die Tasche|la bolsa|torba
shirt|das Hemd|la camisa|koszula
shoes|die Schuhe|los zapatos|buty
trousers|die Hose|los pantalones|spodnie
dress|das Kleid|el vestido|sukienka
cheap|billig|barato|tani
expensive|teuer|caro|drogi
receipt|der Kassenbon|el recibo|paragon
discount|der Rabatt|el descuento|rabat
size|die Größe|la talla|rozmiar
cash|das Bargeld|el efectivo|gotówka
credit card|die Kreditkarte|la tarjeta de crédito|karta kredytowa
fitting room|die Umkleidekabine|el probador|przymierzalnia
checkout|die Kasse|la caja|kasa
market|der Markt|el mercado|targ
shopping basket|der Einkaufskorb|la cesta de la compra|koszyk na zakupy
special offer|das Sonderangebot|la oferta especial|oferta specjalna''',
'Zdrowie': '''head|der Kopf|la cabeza|głowa
hand|die Hand|la mano|dłoń
leg|das Bein|la pierna|noga
eye|das Auge|el ojo|oko
ear|das Ohr|la oreja|ucho
nose|die Nase|la nariz|nos
mouth|der Mund|la boca|usta
doctor|der Arzt|el médico|lekarz
hospital|das Krankenhaus|el hospital|szpital
healthy|gesund|sano|zdrowy
pharmacy|die Apotheke|la farmacia|apteka
medicine|das Medikament|el medicamento|lekarstwo
pain|der Schmerz|el dolor|ból
fever|das Fieber|la fiebre|gorączka
cough|der Husten|la tos|kaszel
appointment|der Arzttermin|la cita médica|wizyta lekarska
tooth|der Zahn|el diente|ząb
stomach|der Magen|el estómago|żołądek
back|der Rücken|la espalda|plecy
tired|müde|cansado|zmęczony''',
'Czas wolny': '''music|die Musik|la música|muzyka
film|der Film|la película|film
sport|der Sport|el deporte|sport
football|der Fußball|el fútbol|piłka nożna
game|das Spiel|el juego|gra
park|der Park|el parque|park
friend|der Freund|el amigo|przyjaciel
weekend|das Wochenende|el fin de semana|weekend
to read|lesen|leer|czytać
to dance|tanzen|bailar|tańczyć
swimming|das Schwimmen|la natación|pływanie
cycling|das Radfahren|el ciclismo|jazda na rowerze
photography|die Fotografie|la fotografía|fotografia
concert|das Konzert|el concierto|koncert
theatre|das Theater|el teatro|teatr
exhibition|die Ausstellung|la exposición|wystawa
walk|der Spaziergang|el paseo|spacer
mountains|die Berge|las montañas|góry
to paint|malen|pintar|malować
to cook|kochen|cocinar|gotować'''
}

def entries():
    for topic, lines in DATA.items():
        for i,line in enumerate(lines.splitlines()):
            en,de,es,pl=line.split('|')
            for language,term in [('en',en),('de',de),('es',es)]:
                yield {'language':language,'term':term,'meaning':pl,'topic':topic,'level':'A1' if i<10 else 'A2'}
