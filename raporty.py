# raporty.py
# Opcja C — zapis wyników obliczeń do pliku .txt


from datetime import datetime  


def formatuj_kat(hz_dd):
    """
    Przelicza kąt ze stopni dziesiętnych na napis DDD°MM'SS".

    Parametry:
        hz_dd (float): Kąt w stopniach dziesiętnych.

    Zwraca:
        str: Kąt w formacie np. '076°02'47"'.

    """
    deg  = int(hz_dd)
    frac = (hz_dd - deg) * 60
    min_ = int(frac)
    sec  = round((frac - min_) * 60)

    if sec == 60:
        sec   = 0
        min_ += 1
    if min_ == 60:
        min_ = 0
        deg += 1

    return f"{deg:03d}\u00b0{min_:02d}'{sec:02d}\""


def zapisz_raport_wspolrzednych(wyniki, nag, sciezka, z_bledami=True):
    """
    Zapisuje raport z wyznaczenia współrzędnych (i opcjonalnie błędów) do pliku .txt.

    Parametry:
        wyniki   (dict): Słownik z kluczami pkt, data, hz_dd, d_m, dX, dY, X, Y,
                         mX, mY, mP — zwrócony przez oblicz_wspolrzedne_i_bledy().
                         UWAGA: mX, mY, mP są już wyliczone w [mm].
        nag      (dict): Słownik z przetworzonymi metadanymi — zwrócony przez
                         przetworz_metadane(). Klucze: x0, y0, x_a, y_a, mHz_sec,
                         mD_mm, mD_ppm.
        sciezka  (str):  Ścieżka do pliku wyjściowego, np. 'wyniki/raporty/raport.txt'.
        z_bledami (bool): Czy dołączyć kolumny mX, mY, mP do tabeli (domyślnie True).
                          Jeśli True ale mP[0] is None — kolumny są pomijane automatycznie.

    """

    bledy_dostepne = z_bledami and (wyniki['mP'][0] is not None)

    data_raportu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(sciezka, 'w', encoding='utf-8') as f:

        f.write('=' * 78 + '\n')
        f.write('  DZIENNIK POMIAROW TACHIMETRYCZNYCH\n')
        f.write('=' * 78 + '\n')

        f.write(f"  Data raportu   : {data_raportu}\n")
        f.write(f"  Stanowisko O   : X0 = {nag['x0']:.3f} m   "
                f"Y0 = {nag['y0']:.3f} m\n")
        f.write(f"  Nawiazanie A   : Xa = {nag['x_a']:.3f} m   "
                f"Ya = {nag['y_a']:.3f} m\n")

        if nag.get('mHz_sec') is not None:
            f.write(f"  Dokl. katowa   : {nag['mHz_sec']}\"\n")
        if nag.get('mD_mm') is not None:
            f.write(f"  Dokl. dlugosci : {nag['mD_mm']} mm + "
                    f"{nag['mD_ppm']} ppm\n")
        f.write('=' * 78 + '\n\n')

        f.write('  OBSERWACJE I OBLICZENIA\n')

        if bledy_dostepne:
            sep = '-' * 108 + '\n'
            naglowek = (
                f"{'Pkt':<8} {'Data':<12} {'Hz':>12} {'D[m]':>8} "
                f"{'dX[m]':>9} {'dY[m]':>9} "
                f"{'X[m]':>10} {'Y[m]':>10} "
                f"{'mX[mm]':>7} {'mY[mm]':>7} {'mP[mm]':>7}\n"
            )
        else:
            sep = '-' * 82 + '\n'
            naglowek = (
                f"{'Pkt':<8} {'Data':<12} {'Hz':>12} {'D[m]':>8} "
                f"{'dX[m]':>9} {'dY[m]':>9} "
                f"{'X[m]':>10} {'Y[m]':>10}\n"
            )

        f.write(sep)
        f.write(naglowek)
        f.write(sep)

        for i in range(len(wyniki['pkt'])):
            pkt   = wyniki['pkt'][i]
            data  = wyniki['data'][i]
            hz_dd = wyniki['hz_dd'][i]
            d     = wyniki['d_m'][i]
            dX    = wyniki['dX'][i]
            dY    = wyniki['dY'][i]
            X     = wyniki['X'][i]
            Y     = wyniki['Y'][i]

            hz_str = formatuj_kat(hz_dd)

            if bledy_dostepne:

                mX_mm = wyniki['mX'][i]
                mY_mm = wyniki['mY'][i]
                mP_mm = wyniki['mP'][i]

                linia = (
                    f"{pkt:<8} {data:<12} {hz_str:>12} {d:>8.3f} "
                    f"{dX:>+9.3f} {dY:>+9.3f} "
                    f"{X:>10.3f} {Y:>10.3f} "
                    f"{mX_mm:>7.3f} {mY_mm:>7.3f} {mP_mm:>7.3f}\n"
                )
            else:
                linia = (
                    f"{pkt:<8} {data:<12} {hz_str:>12} {d:>8.3f} "
                    f"{dX:>+9.3f} {dY:>+9.3f} "
                    f"{X:>10.3f} {Y:>10.3f}\n"
                )
            f.write(linia)

        f.write(sep)
        f.write('\n  KONIEC RAPORTU\n')
        f.write('=' * 78 + '\n')


def zapisz_raport_pola(punkty_wieloboku, pole_m2, pole_ha, sciezka):
    """
    Zapisuje raport z obliczenia pola powierzchni wieloboku metodą Gaussa.

    Parametry:
        punkty_wieloboku (list of tuple): Lista par (X, Y) wierzchołków wieloboku
                                          — punkty 1–20 bez serii monitoringowej.
        pole_m2 (float): Pole powierzchni w metrach kwadratowych [m²].
        pole_ha (float): Pole powierzchni w hektarach [ha].
        sciezka (str):   Ścieżka do pliku wyjściowego.

    """
    data_raportu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(sciezka, 'w', encoding='utf-8') as f:
        f.write('=' * 58 + '\n')
        f.write('  POLE POWIERZCHNI WIELOBOKU - metoda Gaussa\n')
        f.write(f'  Data raportu: {data_raportu}\n')
        f.write('-' * 58 + '\n')
        f.write(f"{'Nr':<5} {'X [m]':>12} {'Y [m]':>12}\n")
        f.write('-' * 32 + '\n')

        for idx, (x, y) in enumerate(punkty_wieloboku, start=1):
            f.write(f"{idx:<5} {x:>12.3f} {y:>12.3f}\n")

        f.write('-' * 32 + '\n')
        f.write(f"\n  Liczba wierzcholkow : {len(punkty_wieloboku)}\n")
        f.write(f"  Pole powierzchni    : {pole_m2:>14.3f} m2\n")
        f.write(f"                      : {pole_ha:>14.6f} ha\n")
        f.write('=' * 58 + '\n')


def zapisz_raport_regresji(reg, X_list, Y_list, pkt_list, sciezka):
    """
    Zapisuje raport z obliczenia parametrów prostej regresji liniowej.

    Parametry:
        reg      (dict): Słownik wynikowy z oblicz_regresje(). Klucze:
                         a, b — parametry prostej,
                         residua — odchylenia [m],
                         R2 — współczynnik determinacji,
                         Se — błąd standardowy residuów [m].
        X_list   (list): Lista współrzędnych X punktów analizowanych.
        Y_list   (list): Lista współrzędnych Y punktów analizowanych.
        pkt_list (list): Lista nazw punktów analizowanych (np. ['7_01', ...]).
        sciezka  (str):  Ścieżka do pliku wyjściowego.

    """
    data_raportu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    a    = reg['a']
    b    = reg['b']
    R2   = reg['R2']
    Se   = reg['Se']
    e    = reg['residua'] 
    n    = len(X_list)

    with open(sciezka, 'w', encoding='utf-8') as f:
        f.write('=' * 68 + '\n')
        f.write('  RAPORT REGRESJI LINIOWEJ - seria 7_xx\n')
        f.write('  Model: Y = a * X + b\n')
        f.write(f'  Data raportu: {data_raportu}\n')
        f.write('=' * 68 + '\n\n')

        f.write('-' * 68 + '\n')
        f.write('  PARAMETRY PROSTEJ REGRESJI\n')
        f.write('-' * 68 + '\n')
        f.write(f"  a (nachylenie)  : {a:+.8f}\n")
        f.write(f"  b (wyraz wolny) : {b:+.4f}\n")
        f.write(f"  Liczba punktow  : {n}\n\n")

        f.write('-' * 68 + '\n')
        f.write('  STATYSTYKI DOPASOWANIA\n')
        f.write('-' * 68 + '\n')
        f.write(f"  R^2  (wsp. determinacji)     : {R2:.6f}\n")
        f.write(f"  Se   (bl. std. residuow) [m] : {Se:.6f}\n\n")

        f.write('-' * 68 + '\n')
        f.write('  RESIDUA  ei = Yi - (a*Xi + b)\n')
        f.write('-' * 68 + '\n')
        f.write(f"{'Pkt':<8} {'X [m]':>12} {'Y [m]':>12} "
                f"{'Y_est [m]':>12} {'e [m]':>10}\n")
        f.write('-' * 58 + '\n')

        for i in range(n):

            Y_est = a * X_list[i] + b
            f.write(
                f"{pkt_list[i]:<8} {X_list[i]:>12.4f} {Y_list[i]:>12.4f} "
                f"{Y_est:>12.4f} {e[i]:>+10.4f}\n"
            )

        suma_e = sum(e)
        f.write('-' * 58 + '\n')
        f.write(f"  Suma e  (= 0 - kontrola) : {suma_e:+.4f}\n")
        f.write('=' * 68 + '\n')