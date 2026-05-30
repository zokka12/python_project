from parsowanie import wczytaj_dziennik

def main():
    plik = "dane/dziennik_obserwacji.txt"
    
    try:
        meta, pomiary = wczytaj_dziennik(plik)
        print(f"Wczytano dane. Liczba punktów: {len(pomiary['pkt'])}")
    except FileNotFoundError:
        print("Blad: Nie znaleziono pliku.")
        return

if __name__ == "__main__":
    main()