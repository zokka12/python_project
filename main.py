# main.py — zaktualizowany o opcje C i D
from parsowanie import wczytaj_dziennik
from obliczenia import przetworz_metadane, oblicz_wspolrzedne_i_bledy, oblicz_regresje
from raporty    import zapisz_raport_wspolrzednych, zapisz_raport_regresji   # opcja C + F
from wizualizacja import wykres_lokalizacji, wykres_bledow, wykres_regresji
import os

# ── Stałe ścieżek (definiujemy tu w main.py zgodnie z wymaganiami) ──
PLIK_WEJSCIOWY      = os.path.join('dane', 'dziennik_obserwacji.txt')
RAPORT_WSPOLRZEDNE  = os.path.join('wyniki', 'raporty', 'raport_wspolrzednych.txt')
WYKRES_LOKALIZACJA  = os.path.join('wyniki', 'wykresy', 'wykres_lokalizacja.png')
WYKRES_BLEDY        = os.path.join('wyniki', 'wykresy', 'wykres_bledy.png')
RAPORT_REGRESJI     = os.path.join('wyniki', 'raporty', 'raport_regresji.txt')
WYKRES_REGRESJA     = os.path.join('wyniki', 'wykresy', 'wykres_regresja.png')



def wyswietl_menu():
    print('\n' + '=' * 50)
    print('  PROGRAM — pomiary tachimetryczne')
    print('=' * 50)
    print('  A | 1  — Wczytaj dziennik obserwacji')
    print('  B | 2  — Oblicz wspolrzedne i bledy')
    print('  C | 3  — Raport: wspolrzedne (.txt)')
    print('  D | 4  — Wykresy: lokalizacja + bledy (.png)')
    print('  F | 6  — Regresja: oblicz i zapisz raport (.txt)')
    print('  G | 7  — Regresja: wykres prostej + rezidua (.png)')
    print('  0      — Wyjscie')
    print('-' * 50)


def main():
    # Katalogi wyjściowe — tworzymy jeśli nie istnieją
    os.makedirs(os.path.join('wyniki', 'raporty'), exist_ok=True)
    os.makedirs(os.path.join('wyniki', 'wykresy'), exist_ok=True)

    # Stan programu — słownik przechowujący dane między opcjami
    stan = {
        'wczytano':  False,
        'obliczono': False,
        'metadata':  None,
        'pomiary':   None,
        'nag':       None,
        'wyniki':    None,
    }

    while True:   # T04: pętla while — działa do wyboru '0'
        wyswietl_menu()
        wybor = input('  Twoj wybor: ').strip().lower()

        # ── Opcja A — parsowanie ──────────────────────────────────
        if wybor in ('a', '1'):
            if not os.path.exists(PLIK_WEJSCIOWY):
                print(f"  [BLAD] Nie znaleziono pliku: {PLIK_WEJSCIOWY}")
                continue
            print(f"  Wczytuje: {PLIK_WEJSCIOWY}")
            metadata, pomiary = wczytaj_dziennik(PLIK_WEJSCIOWY)
            stan['metadata'] = metadata
            stan['pomiary']  = pomiary
            stan['wczytano'] = True
            print(f"  [OK] Wczytano {len(pomiary['pkt'])} punktow.")

        # ── Opcja B — obliczenia ──────────────────────────────────
        elif wybor in ('b', '2'):
            if not stan['wczytano']:
                print("  [BLAD] Najpierw wykonaj opcje A.")
                continue
            nag    = przetworz_metadane(stan['metadata'])
            wyniki = oblicz_wspolrzedne_i_bledy(nag, stan['pomiary'])
            stan['nag']       = nag
            stan['wyniki']    = wyniki
            stan['obliczono'] = True
            bledy = 'tak' if wyniki['mP'][0] is not None else 'brak danych'
            print(f"  [OK] Obliczono {len(wyniki['pkt'])} punktow. Bledy: {bledy}.")

        # ── Opcja C — raport współrzędnych ────────────────────────
        elif wybor in ('c', '3'):
            if not stan['obliczono']:
                print("  [BLAD] Najpierw wykonaj opcje B.")
                continue
            # Pytamy czy dołączyć błędy
            odp = input("  Dolaczyc kolumny bledow mX, mY, mP? [t/n]: ").strip().lower()
            z_bledami = odp in ('t', 'tak')
            zapisz_raport_wspolrzednych(
                stan['wyniki'], stan['nag'],
                RAPORT_WSPOLRZEDNE, z_bledami=z_bledami
            )
            print(f"  [OK] Raport zapisany: {RAPORT_WSPOLRZEDNE}")

        # ── Opcja D — wykresy ─────────────────────────────────────
        elif wybor in ('d', '4'):
            if not stan['obliczono']:
                print("  [BLAD] Najpierw wykonaj opcje B.")
                continue
            print("  Generuje wykres lokalizacji...")
            wykres_lokalizacji(stan['wyniki'], stan['nag'], WYKRES_LOKALIZACJA)
            print(f"  [OK] Zapisano: {WYKRES_LOKALIZACJA}")

            print("  Generuje wykres bledow...")
            wykres_bledow(stan['wyniki'], WYKRES_BLEDY)
            print(f"  [OK] Zapisano: {WYKRES_BLEDY}")

    # ── Opcja F — regresja liniowa serii 7_xx ────────────────
        elif wybor in ('f', '6'):
            if not stan['obliczono']:
                print("  [BLAD] Najpierw wykonaj opcje B.")
                continue

            # Wyodrebnij punkty serii 7_xx z wynikow
            pkt_7   = [(p, x, y)
                       for p, x, y in zip(stan['wyniki']['pkt'],
                                          stan['wyniki']['X'],
                                          stan['wyniki']['Y'])
                       if str(p).startswith('7_')]

            if len(pkt_7) < 3:
                print("  [BLAD] Za malo punktow serii 7_xx (min. 3).")
                continue

            pkt_names = [t[0] for t in pkt_7]
            x_list    = [t[1] for t in pkt_7]
            y_list    = [t[2] for t in pkt_7]

            wynik_reg = oblicz_regresje(x_list, y_list)
            stan['regresja'] = {
                'wynik':     wynik_reg,
                'x_list':    x_list,
                'y_list':    y_list,
                'pkt_names': pkt_names,
            }

            zapisz_raport_regresji(
                wynik_reg, x_list, y_list, pkt_names, RAPORT_REGRESJI
            )
            print(f"  [OK] Regresja obliczona dla {wynik_reg['n']} punktow.")
            print(f"       a = {wynik_reg['a']:+.8f}")
            print(f"       b = {wynik_reg['b']:+.4f}")
            print(f"       R2 = {wynik_reg['R2']:.6f}   Se = {wynik_reg['Se']*1000:.3f} mm")
            print(f"  [OK] Raport zapisany: {RAPORT_REGRESJI}")

        # ── Opcja G — wizualizacja regresji ───────────────────────
        elif wybor in ('g', '7'):
            if stan['regresja'] is None:
                if not stan['obliczono']:
                    print("  [BLAD] Najpierw wykonaj opcje B, a nastepnie F.")
                    continue
                # Automatycznie przelicz regresje jesli B jest juz wykonane
                print("  Brak wynikow regresji — uruchamiam obliczenia F automatycznie...")
                pkt_7 = [(p, x, y)
                         for p, x, y in zip(stan['wyniki']['pkt'],
                                            stan['wyniki']['X'],
                                            stan['wyniki']['Y'])
                         if str(p).startswith('7_')]
                if len(pkt_7) < 3:
                    print("  [BLAD] Za malo punktow serii 7_xx (min. 3).")
                    continue
                pkt_names = [t[0] for t in pkt_7]
                x_list    = [t[1] for t in pkt_7]
                y_list    = [t[2] for t in pkt_7]
                stan['regresja'] = {
                    'wynik':     oblicz_regresje(x_list, y_list),
                    'x_list':    x_list,
                    'y_list':    y_list,
                    'pkt_names': pkt_names,
                }

            reg = stan['regresja']
            print("  Generuje wykres regresji...")
            wykres_regresji(
                reg['wynik'], reg['x_list'], reg['y_list'],
                reg['pkt_names'], WYKRES_REGRESJA
            )
            print(f"  [OK] Zapisano: {WYKRES_REGRESJA}")

        # ── Wyjście ───────────────────────────────────────────────
        elif wybor == '0':
            print("  Do widzenia!")
            break
        else:
            print(f"  [BLAD] Nieznana opcja: '{wybor}'")


if __name__ == '__main__':
    main()