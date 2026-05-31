# Moduł parsowania dziennika pomiarów tachimetrycznych
# Etap A — wczytywanie i strukturyzacja danych wejściowych


def wczytaj_dziennik(sciezka_pliku):
    """
    Parsuje plik dziennika pomiarów tachimetrycznych.

    Wczytuje sekcję nagłówkową oraz sekcję obserwacji z pliku tekstowego
    i zwraca dane w dwóch ustrukturyzowanych słownikach Pythona.

    Parametry:
        sciezka_pliku (str): Ścieżka do pliku dziennika obserwacji (.txt).

    Zwraca:
        tuple: Para (metadata, pomiary), gdzie:
            - metadata (dict): Słownik z danymi nagłówkowymi w postaci klucz: wartość (str).
            - pomiary (dict): Słownik z listami obserwacji:
                'pkt'    (list of str)   — nazwy punktów
                'data'   (list of str)   — daty obserwacji
                'hz_deg' (list of int)   — stopnie kąta poziomego
                'hz_min' (list of int)   — minuty kąta poziomego
                'hz_sec' (list of int)   — sekundy kąta poziomego
                'hz_dd'  (list of float) — kąt poziomy w stopniach dziesiętnych
                'd_m'    (list of float) — odległość pozioma [m]
    """
    metadata = {}

    # Słownik obserwacji — każda kolumna to osobna lista.
    # Będziemy do nich dopisywać dane linijka po linijce.
    pomiary = {
        'pkt':    [],
        'data':   [],
        'hz_deg': [],
        'hz_min': [],
        'hz_sec': [],
        'hz_dd':  [],
        'd_m':    []
    }

    # Otwieramy plik — używamy 'with', żeby plik zamknął się automatycznie
    with open(sciezka_pliku, 'r', encoding='utf-8') as f:
        linie = f.readlines()

    # Ta flaga mówi nam w której sekcji jesteśmy:
    # False = nagłówek, True = obserwacje
    czy_jestem_w_sekcji_obserwacji = False

    for linia in linie:
        # Usuwamy białe znaki z początku i końca linii
        linia = linia.strip()

        # Puste linie pomijamy — nie ma w nich nic ciekawego
        if linia == "":
            continue

        # Jak natrafimy na słowo OBSERWACJE, to przełączamy się na tryb obserwacji
        if "OBSERWACJE" in linia:
            czy_jestem_w_sekcji_obserwacji = True
            continue

        if czy_jestem_w_sekcji_obserwacji == False:
            # Jesteśmy w nagłówku — każda linia ma format "Klucz : wartość"
            # Dzielimy po pierwszym dwukropku (maxsplit=1) żeby nie rozciąć wartości
            if ":" in linia:
                klucz, wartosc = linia.split(":", 1)
                metadata[klucz.strip()] = wartosc.strip()
        else:
            # Jesteśmy w sekcji obserwacji — pomijamy linie pomocnicze tabeli
            if "Pkt" in linia or "D [m]" in linia or "---" in linia or "===" in linia:
                continue
            if "KONIEC" in linia:
                continue

            # Dzielimy linię na kolumny po białych znakach
            dane = linia.split()

            # Sprawdzamy czy mamy wszystkie 4 kolumny: pkt, data, hz, d
            if len(dane) >= 4:
                pkt       = dane[0]
                data      = dane[1]
                hz_surowe = dane[2]   # format: DDD°MM'SS"
                d         = float(dane[3])

                pomiary['pkt'].append(pkt)
                pomiary['data'].append(data)
                pomiary['d_m'].append(d)

                # Przetwarzanie kąta DDD°MM'SS" na składowe i stopnie dziesiętne.
                # Zamieniamy symbole kąta na spacje, żeby split() mógł rozdzielić liczby.
                hz_czysty   = hz_surowe.replace('°', ' ').replace("'", ' ').replace('"', ' ')
                czesci_kata = hz_czysty.split()

                deg  = int(czesci_kata[0])
                min_ = int(czesci_kata[1])  # min_ żeby nie nadpisywać wbudowanej funkcji min()
                sec  = int(czesci_kata[2])

                pomiary['hz_deg'].append(deg)
                pomiary['hz_min'].append(min_)
                pomiary['hz_sec'].append(sec)

                # Przeliczamy kąt na stopnie dziesiętne
                dd = deg + (min_ / 60) + (sec / 3600)
                pomiary['hz_dd'].append(dd)

    # Zwracamy oba słowniki do main.py
    return metadata, pomiary