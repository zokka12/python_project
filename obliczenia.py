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

 
def oblicz_pole_gaussa(wyniki):
    """
    Oblicza pole powierzchni wieloboku metodą Gaussa (Shoelace formula).
 
    Bierze tylko punkty wieloboku (1–20 + punkt 7) — pomija serię monitoringową
    7_xx bo to nie są wierzchołki wieloboku, tylko wielokrotne pomiary tego samego punktu.
 
    Wzór Gaussa:
        P = 0.5 * |Σ(Xi * Yi+1 - Xi+1 * Yi)|
    gdzie indeks i+1 jest cykliczny — ostatni punkt łączy się z pierwszym.
 
    Parametry:
        wyniki (dict): Słownik wynikowy z oblicz_wspolrzedne_i_bledy().
                       Klucze: pkt, X, Y.
 
    Zwraca:
        tuple: (punkty_wb, pole_m2, pole_ha), gdzie:
            punkty_wb (list of tuple) — lista par (X, Y) wierzchołków wieloboku
            pole_m2   (float)         — pole powierzchni [m²]
            pole_ha   (float)         — pole powierzchni [ha]
    """
    # Wyciągamy tylko punkty wieloboku — te bez '_' w nazwie to wierzchołki

    punkty_wb = [
        (wyniki['X'][i], wyniki['Y'][i])
        for i in range(len(wyniki['pkt']))
        if '_' not in wyniki['pkt'][i]
    ]
 
    n = len(punkty_wb)
 
    # Wzór Gaussa — sumujemy iloczyny krzyżowe sąsiednich wierzchołków
    suma = 0.0
    for i in range(n):
        xi  = punkty_wb[i][0]
        yi  = punkty_wb[i][1]
        # Następny wierzchołek — modulo n żeby po ostatnim wrócić do pierwszego
        xi1 = punkty_wb[(i + 1) % n][0]
        yi1 = punkty_wb[(i + 1) % n][1]
 
        suma += xi * yi1 - xi1 * yi
 
    pole_m2 = abs(suma) / 2.0
    # 1 ha = 10 000 m² — przeliczamy dzieląc przez 10000
    pole_ha = pole_m2 / 10000.0
 
    return punkty_wb, pole_m2, pole_ha



# ── Opcja F — regresja liniowa serii 7_xx ────────────────────────────────
# Wszystkie operacje macierzowe wykonane ręcznie (bez numpy.linalg / scipy).
 
 
def _transponuj(A):
    """
    Transponuje macierz A (listę list).
 
    Parametry:
        A (list[list[float]]): Macierz wejściowa m × n.
 
    Zwraca:
        list[list[float]]: Macierz transponowana n × m.
    """
    m = len(A)
    n = len(A[0])
    return [[A[r][c] for r in range(m)] for c in range(n)]
 
 
def _mnoz_macierze(A, B):
    """
    Mnoży dwie macierze A (m × k) i B (k × n).
 
    Parametry:
        A (list[list[float]]): Macierz lewa.
        B (list[list[float]]): Macierz prawa.
 
    Zwraca:
        list[list[float]]: Iloczyn A·B o wymiarach m × n.
    """
    m = len(A)
    k = len(A[0])
    n = len(B[0])
    C = [[0.0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            for p in range(k):
                C[i][j] += A[i][p] * B[p][j]
    return C
 
 
def _odwroc_2x2(M):
    """
    Odwraca macierz 2 × 2.
 
    Parametry:
        M (list[list[float]]): Macierz 2 × 2.
 
    Zwraca:
        list[list[float]]: Macierz odwrotna 2 × 2.
 
    Wyjątki:
        ValueError: Gdy wyznacznik wynosi zero (macierz osobliwa).
    """
    a, b = M[0][0], M[0][1]
    c, d = M[1][0], M[1][1]
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError("Macierz A^T*A jest osobliwa — brak rozwiazania regresji.")
    inv = 1.0 / det
    return [
        [ d * inv, -b * inv],
        [-c * inv,  a * inv],
    ]
 
 
def oblicz_regresje(x_list, y_list):
    """
    Wyznacza parametry prostej regresji Y = a·X + b metodą macierzową
    (najmniejsze kwadraty): theta = (A^T A)^{-1} A^T y.
 
    Obliczenia wykonywane są wyłącznie na wbudowanych strukturach Pythona
    i module math — bez gotowych funkcji statystycznych z bibliotek.
 
    Parametry:
        x_list (list[float]): Współrzędne X punktów serii 7_xx.
        y_list (list[float]): Współrzędne Y punktów serii 7_xx.
 
    Zwraca:
        dict: Słownik z kluczami:
            'a'       (float)       — nachylenie prostej
            'b'       (float)       — wyraz wolny
            'y_est'   (list[float]) — wartości estymowane Ŷ_i
            'residua' (list[float]) — residua e_i = Y_i - Ŷ_i [m]
            'R2'      (float)       — współczynnik determinacji
            'Se'      (float)       — błąd standardowy residuów [m]
            'n'       (int)         — liczba punktów
            'SSres'   (float)       — suma kwadratów residuów
            'SStot'   (float)       — całkowita suma kwadratów
 
    Wyjątki:
        ValueError: Gdy listy mają różną długość lub mniej niż 3 punkty.
    """
    n = len(x_list)
    if n != len(y_list):
        raise ValueError("x_list i y_list musza miec ta sama dlugosc.")
    if n < 3:
        raise ValueError("Do regresji potrzeba co najmniej 3 punktow.")
 
    # Budujemy macierz A (n×2) i wektor y (n×1)
    A = [[x_list[i], 1.0] for i in range(n)]
    y = [[y_list[i]] for i in range(n)]
 
    # theta = (A^T A)^{-1} A^T y  — rozwiązanie układu normalnego
    AT      = _transponuj(A)             
    ATA     = _mnoz_macierze(AT, A)      
    ATy     = _mnoz_macierze(AT, y)      
    ATA_inv = _odwroc_2x2(ATA)           
    theta   = _mnoz_macierze(ATA_inv, ATy)  
 
    a = theta[0][0]
    b = theta[1][0]
 
    # Wartości estymowane i residua 
    y_est   = [a * x_list[i] + b for i in range(n)]
    residua = [y_list[i] - y_est[i] for i in range(n)]
 
    # Statystyki dopasowania
    SSres  = sum(e ** 2 for e in residua)
    y_mean = sum(y_list) / n
    SStot  = sum((y_list[i] - y_mean) ** 2 for i in range(n))
 
    R2 = 1.0 - SSres / SStot if SStot > 1e-15 else 0.0
    Se = math.sqrt(SSres / (n - 2))
 
    return {
        'a':       a,
        'b':       b,
        'y_est':   y_est,
        'residua': residua,
        'R2':      R2,
        'Se':      Se,
        'n':       n,
        'SSres':   SSres,
        'SStot':   SStot,
    }