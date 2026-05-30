# Funkcja do wczytywania dziennika pomiarów tachimetrycznych Etap 1


def wczytaj_dziennik(sciezka_pliku):
    """
    Parsuje plik dziennika pomiarów tachimetrycznych.
    Zwraca dwa słowniki: metadata i pomiary.
    """
    metadata = {}
    # Słownik do przechowywania obserwacji (każda kolumna to osobna lista)
    pomiary = {
        'pkt': [], 
        'data': [], 
        'hz_deg': [], 
        'hz_min': [], 
        'hz_sec': [], 
        'hz_dd': [], 
        'd_m': []
    }
    
    # Otwieramy plik używając 'with' 
    with open(sciezka_pliku, 'r', encoding='utf-8') as f:
        linie = f.readlines()
        
    czy_jestem_w_sekcji_obserwacji = False
    
    for linia in linie:
        # Usuwamy białe znaki z końców 
        linia = linia.strip()
        
        # Pomijamy puste linie
        if linia == "":
            continue
            
        # Sprawdzamy czy doszliśmy do sekcji OBSERWACJE
        if "OBSERWACJE" in linia:
            czy_jestem_w_sekcji_obserwacji = True
            continue
            
        if czy_jestem_w_sekcji_obserwacji == False:
            # Parsowanie nagłówka - jeśli jest dwukropek, dzielimy linię
            if ":" in linia:
                klucz, wartosc = linia.split(":", 1)
                metadata[klucz.strip()] = wartosc.strip()
        else:

            # Pomiń linię z nazwami kolumn, jeśli istnieje
            if "Pkt" in linia or "D [m]" in linia or "---" in linia:
                continue
            
            dane = linia.split()
            # Sprawdź czy mamy wystarczająco dużo kolumn
            if len(dane) >= 4:
                pkt = dane[0]
                data = dane[1]
                hz_surowe = dane[2]
                d = float(dane[3])
            
                pomiary['pkt'].append(pkt)
                pomiary['data'].append(data)
                pomiary['d_m'].append(d)
                
                # Przetwarzanie kąta: zamieniamy symbole na spacje, żeby łatwiej podzielić
                # Używamy prostych metod replace i split (zgodnie z T06)
                hz_czysty = hz_surowe.replace('°', ' ').replace("'", ' ').replace('"', ' ')
                czesci_kata = hz_czysty.split()
                
                deg = int(czesci_kata[0])
                min = int(czesci_kata[1])
                sec = int(czesci_kata[2])
                
                pomiary['hz_deg'].append(deg)
                pomiary['hz_min'].append(min)
                pomiary['hz_sec'].append(sec)
                
                # Obliczenie kąta w stopniach dziesiętnych
                dd = deg + (min / 60) + (sec / 3600)
                pomiary['hz_dd'].append(dd)
            else:
                # Jeśli linia jest pusta lub nie ma danych - po prostu idź dalej
                continue
                
    # Na koniec zwracamy do main.py
    return metadata, pomiary