# wizualizacja.py
# Moduł wykresów matplotlib
# Opcja D — szkic sytuacyjny punktów + wykres błędów pomiaru
#
# Korzysta z:
# - T09: fig, ax = plt.subplots() — interfejs obiektowy matplotlib,
#        scatter, plot, bar, axhline, annotate, grid, legend, savefig
# - T08: numpy do pomocniczych obliczeń (np.arange, np.mean)
# - T02: if/else — warunki sprawdzające dostępność danych
# - T03: pętla for — rozdzielanie punktów na kategorie

import numpy as np                  # T08: pomocnicze obliczenia

import matplotlib                   # Najpierw importujemy główny moduł
matplotlib.use('Agg')               # Wymuszamy silnik bezokienkowy (omija błąd Tkinter!)
import matplotlib.pyplot as plt     # Dopiero teraz importujemy pyplot  # T09: wykresy


# Wspólna paleta kolorów — definiujemy raz, używamy wszędzie
KOLOR_WB   = '#1f77b4'   # niebieski   — punkty wieloboku
KOLOR_MON  = '#d62728'   # czerwony    — seria monitoringowa 7_xx
KOLOR_STAN = '#2ca02c'   # zielony     — stanowisko O
KOLOR_NAW  = '#ff7f0e'   # pomarańcz.  — nawiązanie A


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
    Korzysta z T03: pętla for do rozdzielenia punktów na kategorie.
    Korzysta z T02: if '_' in pkt — rozróżnienie typ punktu.
    """
    # ── Rozdzielamy punkty na dwie grupy (T03 + T02) ──────────────
    X_wb, Y_wb, nazwy_wb = [], [], []   # wielobok (punkty 1–20 + 7)
    X_mn, Y_mn           = [], []       # seria monitoringowa (7_01..7_50)

    for i, pkt in enumerate(wyniki['pkt']):
        # Punkty serii monitoringowej mają '_' w nazwie (T02: if)
        if '_' in pkt:
            X_mn.append(wyniki['X'][i])
            Y_mn.append(wyniki['Y'][i])
        else:
            X_wb.append(wyniki['X'][i])
            Y_wb.append(wyniki['Y'][i])
            nazwy_wb.append(pkt)

    # ── Tworzymy figurę i osie (T09: interfejs obiektowy) ─────────
    fig, ax = plt.subplots(figsize=(9, 9))

    # Linia wieloboku — domykamy przez dołączenie pierwszego punktu na końcu
    # T01: konkatenacja list przez '+'
    ax.plot(
        X_wb + [X_wb[0]],
        Y_wb + [Y_wb[0]],
        color=KOLOR_WB, linewidth=1.2, linestyle='--',
        zorder=1, label='Wielobok (linia)'
    )

    # Punkty wieloboku — scatter (T09)
    ax.scatter(
        X_wb, Y_wb,
        color=KOLOR_WB, s=55, zorder=3,
        label=f'Wielobok | n = {len(X_wb)}'
    )

    # Podpisy punktów wieloboku (T03: pętla + T09: annotate)
    for i, nazwa in enumerate(nazwy_wb):
        ax.annotate(
            nazwa,
            xy=(X_wb[i], Y_wb[i]),
            xytext=(4, 4),                   # przesunięcie od punktu w pikselach
            textcoords='offset points',
            fontsize=7, color='navy'
        )

    # Punkty monitoringowe 7_xx
    ax.scatter(
        X_mn, Y_mn,
        color=KOLOR_MON, s=20, marker='o',
        zorder=2, alpha=0.7,
        label=f'Monitoring pkt 7 | n = {len(X_mn)}'
    )

    # Stanowisko O — gwiazdka zielona
    ax.scatter(
        [nag['x0']], [nag['y0']],
        color=KOLOR_STAN, s=150, marker='*', zorder=5,
        label=f"Stanowisko O ({nag['x0']:.0f}, {nag['y0']:.0f})"
    )
    ax.annotate(
        'O',
        xy=(nag['x0'], nag['y0']),
        xytext=(6, 6), textcoords='offset points',
        fontsize=10, fontweight='bold', color=KOLOR_STAN
    )

    # Nawiązanie A — trójkąt pomarańczowy
    ax.scatter(
        [nag['x_a']], [nag['y_a']],
        color=KOLOR_NAW, s=120, marker='^', zorder=5,
        label=f"Nawiazanie A ({nag['x_a']:.0f}, {nag['y_a']:.0f})"
    )
    ax.annotate(
        'A',
        xy=(nag['x_a'], nag['y_a']),
        xytext=(6, 6), textcoords='offset points',
        fontsize=10, fontweight='bold', color=KOLOR_NAW
    )

    # ── Opisy osi, tytuł, legenda, siatka (T09) ───────────────────
    ax.set_xlabel('Y [m]', fontsize=10)
    ax.set_ylabel('X [m]', fontsize=10)
    ax.set_title(
        f"Lokalizacja punktow pomiarowych\n"
        f"Stanowisko O | Nawiazanie A | n = {len(wyniki['pkt'])} punktow",
        fontsize=11, fontweight='bold'
    )
    ax.legend(loc='lower left', framealpha=0.85, fontsize=8)
    ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.6)
    # set_aspect('equal') — skala 1:1, kluczowe w geodezji!
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    # T09: fig.savefig — zapis do PNG, dpi=150 = dobra jakość
    fig.savefig(sciezka_png, dpi=150, bbox_inches='tight')
    plt.close(fig)   # zwalniamy pamięć — ważne przy wielu wykresach


def wykres_bledow(wyniki, sciezka_png):
    """
    Tworzy wykres słupkowy błędów mX, mY, mP dla wszystkich punktów.
    Zawiera linie średniej i informacje statystyczne w tytule każdego subplotu.

    Parametry:
        wyniki      (dict): Słownik wynikowy z oblicz_wspolrzedne_i_bledy().
                            Klucze: pkt, mX, mY, mP (wartości w metrach [m]).
        sciezka_png (str):  Ścieżka zapisu pliku PNG.

    Korzysta z T09 (matplotlib):
        fig, axes = plt.subplots(1, 3) — 3 subploty w jednym wierszu
        ax.bar()     — wykres słupkowy
        ax.axhline() — pozioma linia (wartość średnia)
        ax.set_xticks() — niestandardowe etykiety osi X
    Korzysta z T08 (numpy): np.arange() — pozycje słupków,
                             np.mean()  — wartość średnia.
    Korzysta z T02: if — sprawdzenie czy dane błędów istnieją.
    """
    # Sprawdzamy czy błędy zostały obliczone (T02: if)
    if wyniki['mP'][0] is None:
        print("  Brak danych bledow — wykres bledow pominieto.")
        return

    pkt = wyniki['pkt']
    n   = len(pkt)

    # Przeliczamy z metrów na milimetry — T01: list comprehension
    mX_mm = [v * 1000.0 for v in wyniki['mX']]
    mY_mm = [v * 1000.0 for v in wyniki['mY']]
    mP_mm = [v * 1000.0 for v in wyniki['mP']]

    # T08: np.arange — indeksy pozycji słupków (0, 1, 2, ..., n-1)
    pozycje = np.arange(n)

    # T09: plt.subplots(1, 3) — figura z 3 subplotami w jednym wierszu
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        f'Bledy pomiaru punktow — prawo propagacji Gaussa | n = {n} punktow',
        fontsize=11, fontweight='bold'
    )

    # T03: zip() łączy trzy listy w jedną iterację — elegancki sposób
    # na powtórzenie tego samego kodu dla mX, mY, mP
    for ax, dane_mm, tytul, kolor in zip(
        axes,
        [mX_mm,      mY_mm,      mP_mm],
        ['Blad skladowej X — mX',
         'Blad skladowej Y — mY',
         'Blad punktu — mP'],
        ['#5b9bd5', '#ed7d31', '#70ad47']
    ):
        # T08: np.mean() — obliczamy średnią
        srednia = float(np.mean(dane_mm))
        mini    = min(dane_mm)
        maxi    = max(dane_mm)

        # T09: ax.bar — słupki z kolorem i białą krawędzią
        ax.bar(pozycje, dane_mm,
               color=kolor, edgecolor='white', linewidth=0.4, zorder=2)

        # T09: ax.axhline — pozioma linia przez cały wykres
        # label= pojawi się w legendzie
        ax.axhline(
            srednia,
            color='black', linewidth=1.5, linestyle='--', zorder=3,
            label=f'srednia = {srednia:.3f} mm'
        )

        # Statystyki w tytule — T06: f-string z formatowaniem
        ax.set_title(
            f'{tytul}\n'
            f'min = {mini:.3f}   max = {maxi:.3f}   sr = {srednia:.3f} mm',
            fontsize=9
        )
        ax.set_ylabel('[mm]', fontsize=9)
        ax.set_xlabel('Punkt', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis='y', linestyle=':', linewidth=0.5, alpha=0.6, zorder=1)

        # T09: set_xticks — co 5 punkt żeby etykiety się nie tłoczyły
        ax.set_xticks(pozycje[::5])
        ax.set_xticklabels(
            [pkt[j] for j in range(0, n, 5)],
            rotation=45, ha='right', fontsize=7
        )

    plt.tight_layout()
    fig.savefig(sciezka_png, dpi=150, bbox_inches='tight')
    plt.close(fig)