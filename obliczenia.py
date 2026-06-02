# Moduł obliczeń tachimetrycznych

import math


def przetworz_metadane(metadata):
    """
    Wyciąga i konwertuje parametry liczbowe ze słownika metadanych.

    Parametry:
        metadata (dict): Słownik z surowymi danymi nagłówkowymi zwrócony
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

    # usuwanie jednostek i znaków równości dla czystych floatów
    stan = metadata.get('Stanowisko O', '')
    czesci = stan.replace('=', ' ').replace('m', ' ').split()
    if len(czesci) >= 4:
        nag['x0'] = float(czesci[1])
        nag['y0'] = float(czesci[3])
    else:

        nag['x0'] = None
        nag['y0'] = None

    naw = metadata.get('Nawiązanie A', '')
    czesci = naw.replace('=', ' ').replace('m', ' ').split()
    if len(czesci) >= 4:
        nag['x_a'] = float(czesci[1])
        nag['y_a'] = float(czesci[3])
    else:
        nag['x_a'] = None
        nag['y_a'] = None

    kat = metadata.get('Dokł. kątowa', '')
    czesci = kat.replace('"', ' ').split()
    nag['mHz_sec'] = float(czesci[0]) if czesci else None

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

     Wzory:
        alfa = 90° - Hz
        dX = D * cos(alfa),  X = X0 + dX
        dY = D * sin(alfa),  Y = Y0 + dY
        mD = mD_mm/1000 + mD_ppm*1e-6 * D
        mX = sqrt((mD*cos(alfa))^2 + (D*sin(alfa)*mHz)^2) * 1000  [mm]
        mY = sqrt((mD*sin(alfa))^2 + (D*cos(alfa)*mHz)^2) * 1000  [mm]
        mP = sqrt(mX^2 + mY^2)  [mm]

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

    czy_bledy = (nag['mHz_sec'] is not None and
                 nag['mD_mm']  is not None and
                 nag['mD_ppm'] is not None)

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

    for i in range(len(pomiary['pkt'])):
        hz_dd = pomiary['hz_dd'][i]
        d     = pomiary['d_m'][i]

        alfa_rad = math.radians(90.0 - hz_dd)

        # wyznaczenie przyrostów współrzędnych
        dX = d * math.cos(alfa_rad)
        dY = d * math.sin(alfa_rad)


        wyniki['pkt'].append(pomiary['pkt'][i])
        wyniki['data'].append(pomiary['data'][i])
        wyniki['hz_dd'].append(hz_dd)
        wyniki['d_m'].append(d)
        wyniki['dX'].append(dX)
        wyniki['dY'].append(dY)
        wyniki['X'].append(x0 + dX)
        wyniki['Y'].append(y0 + dY)


        # algorytm propagacji błędów dla metody biegunowej (Prawo Gaussa)
        if czy_bledy:
            mHz_rad = nag['mHz_sec'] / 206265.0 # zamiana sekundy na radiany

            mD_m = nag['mD_mm'] / 1000.0 + nag['mD_ppm'] * 1e-6 * d # błąd długości

            # obliczanie błędów składowych [m] i zamiana na [mm]
            mX = math.sqrt((mD_m * math.cos(alfa_rad))**2 +
                           (d * math.sin(alfa_rad) * mHz_rad)**2) * 1000.0
            mY = math.sqrt((mD_m * math.sin(alfa_rad))**2 +
                           (d * math.cos(alfa_rad) * mHz_rad)**2) * 1000.0
            mP = math.sqrt(mX**2 + mY**2)

            wyniki['mX'].append(mX)
            wyniki['mY'].append(mY)
            wyniki['mP'].append(mP)
        else:

            wyniki['mX'].append(None)
            wyniki['mY'].append(None)
            wyniki['mP'].append(None)

    return wyniki

 
def oblicz_pole_gaussa(wyniki):
    """
    Oblicza pole powierzchni wieloboku metodą Gaussa.
 
    Bierze tylko punkty wieloboku (1–20 + punkt 7) i pomija serię monitoringową
    7_xx bo to nie są wierzchołki wieloboku, tylko wielokrotne pomiary tego samego punktu.
 
    Wzór Gaussa:
        P = 0.5 * |Σ(Xi * Yi+1 - Xi+1 * Yi)|
 
    Parametry:
        wyniki (dict): Słownik wynikowy z oblicz_wspolrzedne_i_bledy().
                       Klucze: pkt, X, Y.
 
    Zwraca:
        tuple: (punkty_wb, pole_m2, pole_ha), gdzie:
            punkty_wb (list of tuple) — lista par (X, Y) wierzchołków wieloboku
            pole_m2   (float)         — pole powierzchni [m²]
            pole_ha   (float)         — pole powierzchni [ha]
    """
    # bierzemy tylko wierzchołki wieloboku
    punkty_wb = [
        (wyniki['X'][i], wyniki['Y'][i])
        for i in range(len(wyniki['pkt']))
        if '_' not in wyniki['pkt'][i]
    ]
 
    n = len(punkty_wb)
 
    suma = 0.0
    for i in range(n):
        xi  = punkty_wb[i][0]
        yi  = punkty_wb[i][1]

        xi1 = punkty_wb[(i + 1) % n][0]
        yi1 = punkty_wb[(i + 1) % n][1]
 
        suma += xi * yi1 - xi1 * yi
 
    pole_m2 = abs(suma) / 2.0

    pole_ha = pole_m2 / 10000.0
 
    return punkty_wb, pole_m2, pole_ha

 
 
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
    Wyznacza parametry prostej regresji Y = a·X + b 
    Metodą Najmniejszych Kwadratów: theta = (A^T A)^{-1} A^T y.
 
 
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
 
    A = [[x_list[i], 1.0] for i in range(n)]  # macierz modelu
    y = [[y_list[i]] for i in range(n)]     # wektor obserwacji 
 
    AT      = _transponuj(A)             
    ATA     = _mnoz_macierze(AT, A)      
    ATy     = _mnoz_macierze(AT, y)      
    ATA_inv = _odwroc_2x2(ATA)           
    theta   = _mnoz_macierze(ATA_inv, ATy)  
 
    a = theta[0][0]
    b = theta[1][0]
 
    
    # wyznaczenie estymatorów i statystyk dopasowania
    y_est   = [a * x_list[i] + b for i in range(n)]
    residua = [y_list[i] - y_est[i] for i in range(n)]
 
    SSres  = sum(e ** 2 for e in residua)
    y_mean = sum(y_list) / n
    SStot  = sum((y_list[i] - y_mean) ** 2 for i in range(n))
 
    R2 = 1.0 - SSres / SStot if SStot > 1e-15 else 0.0  #współczynnik determinacji
    Se = math.sqrt(SSres / (n - 2))                     #błąd standardowy residuów  
 
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