import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== FUNKCJE BAZY DANYCH (SQLite) ====================
DB_FILE = "baza_lotow.db"

def init_db():
    """Tworzy tabele w bazie danych dla lotów oraz użytkowników."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabela rotacji
    c.execute('''
        CREATE TABLE IF NOT EXISTS rotacje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pracownik_nick TEXT,
            start_date TEXT,
            koniec_date TEXT,
            kierunek TEXT,
            w_zamian TEXT
        )
    ''')
    # Tabela użytkowników - nicki są zapisywane małymi literami jako klucz główny
    c.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            nick TEXT PRIMARY KEY,
            imie_nazwisko TEXT
        )
    ''')
    conn.commit()
    conn.close()

def sprawdz_uzytkownika(nick):
    """Sprawdza, czy nick istnieje w bazie danych."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE nick = ?", (nick.lower(),))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def zarejestruj_uzytkownika(nick, imie_nazwisko):
    """Rejestruje nowego użytkownika w bazie."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO uzytkownicy (nick, imie_nazwisko) VALUES (?, ?)", (nick.lower(), imie_nazwisko))
        conn.commit()
        sukces = True
    except sqlite3.IntegrityError:
        sukces = False  # Nick jest już zajęty
    conn.close()
    return sukces

def pobierz_dane():
    """Pobiera rotacje połączone z prawdziwymi danymi użytkowników."""
    conn = sqlite3.connect(DB_FILE)
    query = '''
        SELECT r.id, r.pracownik_nick, u.imie_nazwisko, r.start_date, r.koniec_date, r.kierunek, r.w_zamian 
        FROM rotacje r
        JOIN uzytkownicy u ON r.pracownik_nick = u.nick
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def dodaj_rotacje_db(nick, start, koniec, kierunek, w_zamian):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO rotacje (pracownik_nick, start_date, koniec_date, kierunek, w_zamian)
        VALUES (?, ?, ?, ?, ?)
    ''', (nick.lower(), start, koniec, kierunek, w_zamian))
    conn.commit()
    conn.close()

def usun_rotacje_db(id_rotacji, nick):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM rotacje WHERE id = ? AND pracownik_nick = ?", (id_rotacji, nick.lower()))
    conn.commit()
    conn.close()

# Uruchomienie bazy danych
init_db()

# ==================== SYSTEM LOGOWANIA / REJESTRACJI ====================
if 'zalogowany_nick' not in st.session_state:
    st.session_state.zalogowany_nick = None
if 'zalogowany_imie' not in st.session_state:
    st.session_state.zalogowany_imie = None

if st.session_state.zalogowany_nick is None:
    st.title("🔐 Panel Logowania i Rejestracji")
    st.write("Witaj w aplikacji do wymiany rotacji!")
    
    strefa_akcji = st.tabs(["Zaloguj się", "Utwórz nowe konto"])
    
    with strefa_akcji[0]:
        st.subheader("Mam już konto")
        wpisany_nick = st.text_input("Wpisz swój Nick:", key="login_nick").strip()
        if st.button("Wejdź do aplikacji", use_container_width=True):
            if wpisany_nick:
                imie = sprawdz_uzytkownika(wpisany_nick)
                if imie:
                    st.session_state.zalogowany_nick = wpisany_nick.lower()
                    st.session_state.zalogowany_imie = imie
                    st.success(f"Witaj z powrotem, {imie}!")
                    st.rerun()
                else:
                    st.error("Ten nick nie istnieje. Przejdź do zakładki obok i załóż konto.")
            else:
                st.warning("Wpisz swój nick.")
                
    with strefa_akcji[1]:
        st.subheader("Pierwszy raz w aplikacji")
        nowy_nick = st.text_input("Wymyśl swój unikalny Nick (np. pilot_adam):", key="reg_nick").strip()
        nowe_imie = st.text_input("Twoje Imię i Nazwisko:")
        if st.button("Zarejestruj się i zaloguj", use_container_width=True):
            if not nowy_nick or not nowe_imie:
                st.error("Wypełnij oba pola, aby utworzyć konto!")
            elif " " in nowy_nick:
                st.error("Nick nie może zawierać spacji!")
            else:
                udana_rejestracja = zarejestruj_uzytkownika(nowy_nick, nowe_imie)
                if udana_rejestracja:
                    st.session_state.zalogowany_nick = nowy_nick.lower()
                    st.session_state.zalogowany_imie = nowe_imie
                    st.success("Konto zostało utworzone pomyślnie!")
                    st.rerun()
                else:
                    st.error("Ten nick jest już zajęty przez innego pracownika. Wybierz inny!")
    st.stop()

# ==================== INTERFEJS PO ZALOGOWANIU ====================
st.title("✈️ Giełda Rotacji Lotniczych")

# Panel boczny z informacją o zalogowanym
st.sidebar.markdown(f"👤 Zalogowany: **{st.session_state.zalogowany_imie}**")
st.sidebar.markdown(f"🔑 Twój Nick: `@ {st.session_state.zalogowany_nick}`")
if st.sidebar.button("Wyloguj się"):
    st.session_state.zalogowany_nick = None
    st.session_state.zalogowany_imie = None
    st.rerun()

ZAKLADKI = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia"]
wybrana_zakladka = st.sidebar.radio("Nawigacja", ZAKLADKI)

baza_rotacji = pobierz_dane()

# --- ZAKŁADKA 1: FILTROWANIE ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    
    st.subheader("Filtry wyszukiwania")
    col1, col2 = st.columns(2)
    
    with col1:
        szukany_kierunek = st.text_input("🛫 Kierunek docelowy (np. JFK):", "").strip()
    with col2:
        filtruj_daty = st.checkbox("📅 Filtruj po zakresie dat")
        szukany_zakres = st.date_input("Wybierz przedział czasu:", value=(datetime.today(), datetime.today())) if filtruj_daty else None

    wyniki = baza_rotacji.copy()
    
    # Ukryj własne ogłoszenia zalogowanego użytkownika
    wyniki = wyniki[wyniki["pracownik_nick"] != st.session_state.zalogowany_nick]
    
    if szukany_kierunek:
        wyniki = wyniki[wyniki["kierunek"].str.contains(szukany_kierunek, case=False, na=False)]
        
    if filtruj_daty and szukany_zakres and len(szukany_zakres) == 2:
        od_daty = pd.to_datetime(szukany_zakres)
        do_daty = pd.to_datetime(szukany_zakres)
        wyniki["start_dt"] = pd.to_datetime(wyniki["start_date"])
        wyniki["koniec_dt"] = pd.to_datetime(wyniki["koniec_date"])
        wyniki = wyniki[(wyniki["start_dt"] <= do_daty) & (wyniki["koniec_dt"] >= od_daty)]

    st.divider()
    st.subheader(f"Dostępne oferty ({len(wyniki)})")
    
    if wyniki.empty:
        st.info("Brak pasujących rotacji od innych pracowników.")
    else:
        for idx, row in wyniki.iterrows():
            naglowek = f"✈️ {row['kierunek']} | 📅 {row['start_date']} do {row['koniec_date']}"
            with st.expander(naglowek, expanded=True):
                st.write(f"👤 **Wystawiający:** {row['imie_nazwisko']} (`@{row['pracownik_nick']}`)")
                st.warning(f"🔄 **Warunki wymiany:** {row['w_zamian']}")
                if st.button(f"Zaproponuj wymianę", key=f"trade_{row['id']}", use_container_width=True):
                    st.success(f"Zgłoszono chęć wymiany! Skontaktuj się z użytkownikiem: {row['imie_nazwisko']} (`@{row['pracownik_nick']}`).")

# --- ZAKŁADKA 2: DODAWANIE ---
elif wybrana_zakladka == "📤 Wystaw swoją rotację":
    st.header("📤 Dodaj nową rotację")
    
    with st.form("form_dodaj_rotacje"):
        nowy_kierunek = st.text_input("Kierunek docelowy (np. JFK, CDG):")
        col_start, col_end = st.columns(2)
        with col_start:
            data_start = st.date_input("Start rotacji:", min_value=datetime.today())
        with col_end:
            data_koniec = st.date_input("Koniec rotacji:", min_value=datetime.today())
            
        w_zamian = st.text_area("Za co chcesz się wymienić? (np. 'Szukam lotu do USA w terminie X', 'Chcę wolne')")
        submit = st.form_submit_button("Zapisz w bazie danych")
        
        if submit:
            if data_koniec < data_start:
                st.error("Błąd: Data zakończenia nie może być wcześniejsza niż startu!")
            elif nowy_kierunek and w_zamian:
                dodaj_rotacje_db(st.session_state.zalogowany_nick, str(data_start), str(data_koniec), nowy_kierunek, w_zamian)
                st.success("Rotacja została dodana do bazy!")
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola.")

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    moje = baza_rotacji[baza_rotacji["pracownik_nick"] == st.session_state.zalogowany_nick]
    
    if moje.empty:
        st.info("Nie wystawiłeś/aś obecnie żadnych lotów na giełdę.")
    else:
        for idx, row in moje.iterrows():
            with st.container():
                st.write(f"✈️ **{row['kierunek']}** ({row['start_date']} do {row['koniec_date']})")
                st.write(f"🔄 Oczekiwania: {row['w_zamian']}")
                if st.button("Usuń to ogłoszenie", key=f"del_{row['id']}", use_container_width=True):
                    usun_rotacje_db(row['id'], st.session_state.zalogowany_nick)
                    st.success("Ogłoszenie usunięte z bazy.")
                    st.rerun()
                st.divider()
