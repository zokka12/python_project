# Moduł obliczeń tachimetrycznych
# Etap B — wyznaczanie współrzędnych i błędów pomiaru punktu

import math


def przetworz_metadane(metadata):
    """
    Wyciąga i konwertuje parametry liczbowe ze słownika metadanych.

    Parametry:
        metadata (dict): Słownik z surowymi danymi nagłówkowymi (str) zwrócony
                         przez wczytaj_dziennik().

    Zwraca:
        dict: Słownik z kluczami:
            'x0'      (float)       — współrzędna X stanowiska [m]
            'y0'      (float)       — współrzędna Y stanowiska [m]
            'x_a'     (float)       — współrzędna X nawiązania [m]
            'y_a'     (float)       — współrzędna Y nawiązania [m]
            'mHz_sec' (float|None)  — dokładność kątowa ["] lub None
            'mD_mm'   (float|None)  — składowa stała błędu odległości [mm] lub None
            'mD_ppm'  (float|None)  — składowa proporcjonalna [ppm] lub None
    """
    nag = {}

    # Ze stringa "X₀ = 1000.000 m    Y₀ = 1000.000 m" chcemy wyciągnąć dwie liczby.
    # Zamieniamy '=' i 'm' na spacje, żeby split() dał nam listę
    # i wyciągamy elementy pod indeksami [1] i [3]
    stan = metadata.get('Stanowisko O', '')
    czesci = stan.replace('=', ' ').replace('m', ' ').split()
    if len(czesci) >= 4:
        nag['x0'] = float(czesci[1])
        nag['y0'] = float(czesci[3])
    else:
        # Jak nie ma danych w nagłówku, ustawiamy None żeby program się nie wysypał
        nag['x0'] = None
        nag['y0'] = None

    # To samo dla punktu nawiązania A
    naw = metadata.get('Nawiązanie A', '')
    czesci = naw.replace('=', ' ').replace('m', ' ').split()
    if len(czesci) >= 4:
        nag['x_a'] = float(czesci[1])
        nag['y_a'] = float(czesci[3])
    else:
        nag['x_a'] = None
        nag['y_a'] = None

    # Dokładność kątowa jest w formacie '5"' — usuwamy cudzysłów i bierzemy liczbę
    kat = metadata.get('Dokł. kątowa', '')
    czesci = kat.replace('"', ' ').split()
    nag['mHz_sec'] = float(czesci[0]) if czesci else None

    # Dokładność długości jest w formacie "2 mm + 2 ppm"
    # Po replace('+', ' ') i split() dostajemy ['2', 'mm', '2', 'ppm']
    # więc mm jest pod [0], a ppm pod [2]
    dl = metadata.get('Dokł. długości', '')
    czesci = dl.replace('+', ' ').split()
    if len(czesci) >= 3:
        nag['mD_mm']  = float(czesci[0])
        nag['mD_ppm'] = float(czesci[2])
    else:
        nag['mD_mm']  = None
        nag['mD_ppm'] = None

    return nag


def oblicz_wspolrzedne_i_bledy(nag, pomiary):
    """
    Oblicza współrzędne płaskie X, Y oraz błędy mX, mY, mP dla wszystkich
    punktów pomiarowych metodą biegunową.

    Współrzędne wyznaczane są ze wzorów:
        alfa = 90° - Hz          (kąt matematyczny)
        dX   = D * cos(alfa)
        dY   = D * sin(alfa)
        X    = X0 + dX
        Y    = Y0 + dY

    Błędy wyznaczane są z prawa propagacji Gaussa (tylko jeśli dostępne mHz i mD):
        mD  = mD_mm/1000 + mD_ppm*1e-6 * D   [m]
        mHz = mHz_sec / 206265                [rad]
        mX  = sqrt((mD*cos(alfa))^2 + (D*sin(alfa)*mHz)^2) * 1000.0 [mm]
        mY  = sqrt((mD*sin(alfa))^2 + (D*cos(alfa)*mHz)^2) * 1000.0 [mm]
        mP  = sqrt(mX^2 + mY^2) [mm]

    Parametry:
        nag     (dict): Słownik z przetworzonymi metadanymi zwrócony przez
                        przetworz_metadane().
        pomiary (dict): Słownik z obserwacjami zwrócony przez wczytaj_dziennik().

    Zwraca:
        dict: Słownik 'wyniki' z kluczami (każdy to lista o długości n punktów):
            'pkt'   (list of str)        — nazwy punktów
            'data'  (list of str)        — daty obserwacji
            'hz_dd' (list of float)      — kąt poziomy [°]
            'd_m'   (list of float)      — odległość [m]
            'dX'    (list of float)      — przyrost współrzędnej X [m]
            'dY'    (list of float)      — przyrost współrzędnej Y [m]
            'X'     (list of float)      — współrzędna X [m]
            'Y'     (list of float)      — współrzędna Y [m]
            'mX'    (list of float|None) — błąd składowej X [mm] lub None
            'mY'    (list of float|None) — błąd składowej Y [mm] lub None
            'mP'    (list of float|None) — błąd punktu [mm] lub None
    """
    x0 = nag['x0']
    y0 = nag['y0']

    # Sprawdzamy czy mamy dane o dokładności instrumentu.
    czy_bledy = (nag['mHz_sec'] is not None and
                 nag['mD_mm']  is not None and
                 nag['mD_ppm'] is not None)

    # Przygotowujemy pusty słownik wyników — każdy klucz to lista,
    # do której będziemy dopisywać wyniki punkt po punkcie
    wyniki = {
        'pkt':  [],
        'data': [],
        'hz_dd': [],
        'd_m':  [],
        'dX':   [],
        'dY':   [],
        'X':    [],
        'Y':    [],
        'mX':   [],
        'mY':   [],
        'mP':   []
    }

    # Główna pętla — przechodzimy przez wszystkie punkty pomiarowe
    for i in range(len(pomiary['pkt'])):
        hz_dd = pomiary['hz_dd'][i]
        d     = pomiary['d_m'][i]

        # Zamieniamy kąt poziomy Hz na kąt matematyczny alfa (w radianach)
        # wzór: alfa = 90° - Hz
        alfa_rad = math.radians(90.0 - hz_dd)

        # Obliczamy przyrosty współrzędnych i same współrzędne
        dX = d * math.cos(alfa_rad)
        dY = d * math.sin(alfa_rad)

        # Dopisujemy wyniki do słownika
        wyniki['pkt'].append(pomiary['pkt'][i])
        wyniki['data'].append(pomiary['data'][i])
        wyniki['hz_dd'].append(hz_dd)
        wyniki['d_m'].append(d)
        wyniki['dX'].append(dX)
        wyniki['dY'].append(dY)
        wyniki['X'].append(x0 + dX)
        wyniki['Y'].append(y0 + dY)

        # Błędy liczymy tylko jeśli mamy dane o dokładności instrumentu
        if czy_bledy:
            # Przeliczamy mHz z sekund na radiany (206265" = 1 radian)
            mHz_rad = nag['mHz_sec'] / 206265.0

            # Błąd odległości: część stała [mm->m] + część proporcjonalna [ppm]
            mD_m = nag['mD_mm'] / 1000.0 + nag['mD_ppm'] * 1e-6 * d

            # Prawo propagacji Gaussa — wyniki w metrach mnożymy przez 1000 by uzyskać milimetry
            mX = math.sqrt((mD_m * math.cos(alfa_rad))**2 +
                           (d * math.sin(alfa_rad) * mHz_rad)**2) * 1000.0
            mY = math.sqrt((mD_m * math.sin(alfa_rad))**2 +
                           (d * math.cos(alfa_rad) * mHz_rad)**2) * 1000.0
            mP = math.sqrt(mX**2 + mY**2)

            wyniki['mX'].append(mX)
            wyniki['mY'].append(mY)
            wyniki['mP'].append(mP)
        else:
            # Jak nie liczymy błędów, wstawiamy None żeby struktura była spójna
            wyniki['mX'].append(None)
            wyniki['mY'].append(None)
            wyniki['mP'].append(None)

    return wyniki