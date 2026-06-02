# Moduł odpowiedzialny za generowanie szkiców i wykresów
import numpy as np                 

import matplotlib  
                
# Użycie silnika Agg 
matplotlib.use('Agg')              
import matplotlib.pyplot as plt    

KOLOR_WB   = '#1f77b4'   
KOLOR_MON  = '#d62728'   
KOLOR_STAN = '#2ca02c'   
KOLOR_NAW  = '#ff7f0e'   


def wykres_lokalizacji(wyniki, nag, sciezka_png):
    """
    Tworzy szkic sytuacyjny — rozmieszczenie punktów w układzie płaskim XY.

    Na wykresie widoczne są:
    - wielobok 20-kątny (niebieskie punkty + linia przerywana domykająca)
    - chmura pomiarów serii monitoringowej 7_xx (czerwone punkty)
    - stanowisko O (zielona gwiazdka)
    - nawiązanie A (pomarańczowy trójkąt)
    Proporcje wykresu 1:1 (set_aspect='equal') — ważne w geodezji!

    Parametry:
        wyniki      (dict): Słownik wynikowy z oblicz_wspolrzedne_i_bledy().
                            Klucze: pkt, X, Y.
        nag         (dict): Słownik z przetworzonymi metadanymi.
                            Klucze: x0, y0, x_a, y_a.
        sciezka_png (str):  Ścieżka zapisu pliku PNG.

    Korzysta z T09 (matplotlib):
        fig, ax = plt.subplots() — interfejs obiektowy (jeden wykres)
        ax.scatter()  — punkty jako symbole
        ax.plot()     — linia wieloboku
        ax.annotate() — podpisy przy punktach
        ax.set_aspect('equal') — skala 1:1
        fig.savefig() — zapis do PNG
    """

    X_wb, Y_wb, nazwy_wb = [], [], []   
    X_mn, Y_mn           = [], []       

    for i, pkt in enumerate(wyniki['pkt']):

        if '_' in pkt:
            X_mn.append(wyniki['X'][i])
            Y_mn.append(wyniki['Y'][i])
        else:
            X_wb.append(wyniki['X'][i])
            Y_wb.append(wyniki['Y'][i])
            nazwy_wb.append(pkt)

    # Inicjalizacja figury  
    fig, ax = plt.subplots(figsize=(9, 9))

    # Rysowanie linii wieloboku
    ax.plot(
        Y_wb + [Y_wb[0]], 
        X_wb + [X_wb[0]], 
        color=KOLOR_WB, linewidth=1.2, linestyle='--',
        zorder=1, label='Wielobok (linia)'
    )

    # Naniesienie punktów wieloboku
    ax.scatter(
        Y_wb, X_wb, 
        color=KOLOR_WB, s=55, zorder=3,
        label=f'Wielobok | n = {len(X_wb)}'
    )

    # Dodanie etykiet nazw punktów
    for i, nazwa in enumerate(nazwy_wb):
        ax.annotate(
            nazwa,
            xy=(Y_wb[i], X_wb[i]), 
            xytext=(4, 4),                   
            textcoords='offset points',
            fontsize=7, color='navy'
        )

    ax.scatter(
        Y_mn, X_mn, 
        color=KOLOR_MON, s=20, marker='o',
        zorder=2, alpha=0.7,
        label=f'Monitoring pkt 7 | n = {len(X_mn)}'
    )

    # Stanowisko instrumentu O 
    ax.scatter(
        [nag['y0']], [nag['x0']], 
        color=KOLOR_STAN, s=150, marker='*', zorder=5,
        label=f"Stanowisko O ({nag['x0']:.0f}, {nag['y0']:.0f})"
    )
    ax.annotate(
        'O',
        xy=(nag['y0'], nag['x0']), 
        xytext=(6, 6), textcoords='offset points',
        fontsize=10, fontweight='bold', color=KOLOR_STAN
    )

    # Punkt nawiązania A 
    ax.scatter(
        [nag['y_a']], [nag['x_a']], 
        color=KOLOR_NAW, s=120, marker='^', zorder=5,
        label=f"Nawiazanie A ({nag['x_a']:.0f}, {nag['y_a']:.0f})"
    )
    ax.annotate(
        'A',
        xy=(nag['y_a'], nag['x_a']), 
        xytext=(6, 6), textcoords='offset points',
        fontsize=10, fontweight='bold', color=KOLOR_NAW
    )

    # Opisy osi, tytuł, legenda, siatka  
    ax.set_xlabel('Y [m]', fontsize=10)
    ax.set_ylabel('X [m]', fontsize=10)
    ax.set_title(
        f"Lokalizacja punktow pomiarowych\n"
        f"Stanowisko O | Nawiazanie A | n = {len(wyniki['pkt'])} punktow",
        fontsize=11, fontweight='bold'
    )
    ax.legend(loc='lower left', framealpha=0.85, fontsize=8)
    ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.6)
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()  # Optymalizacja marginesów

    fig.savefig(sciezka_png, dpi=150, bbox_inches='tight')  # Zapis wysokiej jakości PNG
    plt.close(fig)   # Zwolnienie pamięci po zapisaniu wykresu


def wykres_bledow(wyniki, sciezka_png):
    """
    Tworzy wykres słupkowy błędów mX, mY, mP dla wszystkich punktów.
    Zawiera linie średniej i informacje statystyczne w tytule każdego subplotu.

    Parametry:
        wyniki      (dict): Słownik wynikowy z oblicz_wspolrzedne_i_bledy().
                            Klucze: pkt, mX, mY, mP (wartości w metrach [m]).
        sciezka_png (str):  Ścieżka zapisu pliku PNG.
    """

    if wyniki['mP'][0] is None:
        print("  Brak danych bledow — wykres bledow pominieto.")
        return

    pkt = wyniki['pkt']
    n   = len(pkt)

    mX_mm = [v * 1000.0 for v in wyniki['mX']]
    mY_mm = [v * 1000.0 for v in wyniki['mY']]
    mP_mm = [v * 1000.0 for v in wyniki['mP']]

    pozycje = np.arange(n)

    # Wykres zbiorczy (3 podwykresy obok siebie)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        f'Bledy pomiaru punktow — prawo propagacji Gaussa | n = {n} punktow',
        fontsize=11, fontweight='bold'
    )

    for ax, dane_mm, tytul, kolor in zip(
        axes,
        [mX_mm,      mY_mm,      mP_mm],
        ['Blad skladowej X — mX',
         'Blad skladowej Y — mY',
         'Blad punktu — mP'],
        ['#5b9bd5', '#ed7d31', '#70ad47']
    ):
        srednia = float(np.mean(dane_mm))
        mini    = min(dane_mm)
        maxi    = max(dane_mm)

        ax.bar(pozycje, dane_mm,
               color=kolor, edgecolor='white', linewidth=0.4, zorder=2)

        ax.axhline(
            srednia,
            color='black', linewidth=1.5, linestyle='--', zorder=3,
            label=f'srednia = {srednia:.3f} mm'
        )

        ax.set_title(
            f'{tytul}\n'
            f'min = {mini:.3f}   max = {maxi:.3f}   sr = {srednia:.3f} mm',
            fontsize=9
        )
        ax.set_ylabel('[mm]', fontsize=9)
        ax.set_xlabel('Punkt', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.6, zorder=1)

        ax.set_xticks(pozycje[::5])
        ax.set_xticklabels(
            [pkt[j] for j in range(0, n, 5)],
            rotation=45, ha='right', fontsize=7
        )

    plt.tight_layout()
    fig.savefig(sciezka_png, dpi=150, bbox_inches='tight')
    plt.close(fig)



def wykres_regresji(wynik_reg, x_list, y_list, pkt_names, sciezka_png):
    """
    Tworzy wykres złożony z dwóch subplotów prezentujących wyniki regresji liniowej
    dla serii pomiarowej 7_xx:
      - lewy subplot: chmura punktów X, Y z dopasowaną prostą regresji,
      - prawy subplot: słupkowy wykres residuów e_i = Y_i - Ŷ_i.

    Parametry:
        wynik_reg   (dict): Słownik zwrócony przez regression.oblicz_regresje().
                            Klucze: a, b, y_est, residua, R2, Se, n.
        x_list      (list[float]): Współrzędne X punktów serii 7_xx.
        y_list      (list[float]): Współrzędne Y punktów serii 7_xx.
        pkt_names   (list[str]):   Nazwy punktów (np. ['7_01', '7_02', ...]).
        sciezka_png (str):         Ścieżka zapisu pliku PNG.

    """
    a       = wynik_reg['a']
    b       = wynik_reg['b']
    residua = wynik_reg['residua']
    R2      = wynik_reg['R2']
    Se      = wynik_reg['Se']
    n       = len(x_list) 

    x_min, x_max = min(x_list), max(x_list)
    margin  = (x_max - x_min) * 0.05
    x_line  = [x_min - margin, x_max + margin]
    y_line  = [a * xv + b for xv in x_line]


    znak_b    = '+' if b >= 0 else '-'
    eq_label  = f'Y = {a:.5f}·X {znak_b} {abs(b):.2f}'

    res_mm       = [e * 1000.0 for e in residua]
    max_abs_mm   = max(abs(r) for r in res_mm)

    kolory_bar = [KOLOR_MON if e >= 0 else KOLOR_WB for e in residua]

    pozycje = np.arange(n)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        f'Regresja liniowa — seria 7_xx  |  n = {n}  |  {eq_label}',
        fontsize=11, fontweight='bold'
    )

    # Podwykres 1: Regresja
    ax1 = axes[0]
    
    ax1.scatter(
        x_list, y_list,
        color=KOLOR_MON, s=28, zorder=3, alpha=0.85,
        edgecolors='darkred', linewidths=0.4,
        label='Punkty serii 7_xx'
    )
    ax1.plot(
        x_line, y_line,
        color=KOLOR_WB, linewidth=1.8, zorder=2,
        label=eq_label
    )
    ax1.set_xlabel('X [m]', fontsize=10)
    ax1.set_ylabel('Y [m]', fontsize=10)
    ax1.set_title(
        f'Punkty serii 7_xx + prosta regresji\n'
        f'R² = {R2:.5f}   Se = {Se * 1000:.3f} mm',
        fontsize=9
    )
    ax1.legend(fontsize=8, framealpha=0.85)
    ax1.grid(True, linestyle=':', linewidth=0.5, alpha=0.6)


    # Podwykres 2: Residua
    ax2 = axes[1]

    ax2.bar(
        pozycje, residua,
        color=kolory_bar, edgecolor='white', linewidth=0.3,
        width=0.7, zorder=2
    )

    ax2.axhline(0, color='black', linewidth=0.9, linestyle='-', zorder=3)

    ax2.set_xlabel('Nr pomiaru', fontsize=10)
    ax2.set_ylabel('Residuum e [m]', fontsize=10)
    ax2.set_title(
        f'Residua  e_i = Y_i − Ŷ_i\n'
        f'Se = {Se * 1000:.3f} mm   max|e| = {max_abs_mm:.3f} mm',
        fontsize=9
    )
    ax2.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.6, zorder=1)

    ax2.set_xticks(pozycje[::5])
    ax2.set_xticklabels(
        [pkt_names[j] for j in range(0, n, 5)],
        rotation=45, ha='right', fontsize=7
    )

    plt.tight_layout()
    fig.savefig(sciezka_png, dpi=150, bbox_inches='tight')
    plt.close(fig)