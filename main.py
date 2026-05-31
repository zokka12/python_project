# main.py — zaktualizowany o opcje C i D
from parsowanie import wczytaj_dziennik
from obliczenia import przetworz_metadane, oblicz_wspolrzedne_i_bledy
from raporty    import zapisz_raport_wspolrzednych   # opcja C
from wizualizacja import wykres_lokalizacji, wykres_bledow  # opcja D
import os

# ── Stałe ścieżek (definiujemy tu w main.py zgodnie z wymaganiami) ──
PLIK_WEJSCIOWY      = os.path.join('dane', 'dziennik_obserwacji.txt')
RAPORT_WSPOLRZEDNE  = os.path.join('wyniki', 'raporty', 'raport_wspolrzednych.txt')
WYKRES_LOKALIZACJA  = os.path.join('wyniki', 'wykresy', 'wykres_lokalizacja.png')
WYKRES_BLEDY        = os.path.join('wyniki', 'wykresy', 'wykres_bledy.png')


def wyswietl_menu():
    print('\n' + '=' * 50)
    print('  PROGRAM — pomiary tachimetryczne')
    print('=' * 50)
    print('  A | 1  — Wczytaj dziennik obserwacji')
    print('  B | 2  — Oblicz wspolrzedne i bledy')
    print('  C | 3  — Raport: wspolrzedne (.txt)')
    print('  D | 4  — Wykresy: lokalizacja + bledy (.png)')
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

        # ── Wyjście ───────────────────────────────────────────────
        elif wybor == '0':
            print("  Do widzenia!")
            break
        else:
            print(f"  [BLAD] Nieznana opcja: '{wybor}'")


if __name__ == '__main__':
    main()