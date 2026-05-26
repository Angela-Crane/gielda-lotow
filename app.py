import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# Konfiguracja strony
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== KONFIGURACJA ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

def szyfruj_haslo(haslo):
    return hashlib.sha256(str.encode(haslo)).hexdigest()

DB_FILE = "baza_lotow.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # !!! FUNKCJA RESETU !!!
    # Usuwamy stare tabele przy tym uruchomieniu, aby całkowicie opróżnić aplikację
    c.execute("DROP TABLE IF EXISTS rotacje")
    c.execute("DROP TABLE IF EXISTS uzytkownicy")
    
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            nick TEXT PRIMARY KEY,
            imie_nazwisko TEXT,
            haslo_hash TEXT
        )
    ''')
    conn.commit()
    conn.close()

def weryfikuj_logowanie(nick, haslo):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hash_do_sprawdzenia = szyfruj_haslo(haslo)
    try:
        c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE nick = ? AND haslo_hash = ?", (nick.upper(), hash_do_sprawdzenia))
        user = c.fetchone()
    except sqlite3.OperationalError:
        user = None
    conn.close()
    return user if user else None

def sprawdz_czy_nick_zajety(nick):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM uzytkownicy WHERE nick = ?", (nick.upper(),))
    res = c.fetchone()
    conn.close()
    return res is not None

def zarejestruj_uzytkownika(nick, imie_nazwisko, haslo):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hash_hasla = szyfruj_haslo(haslo)
    try:
        c.execute("INSERT INTO uzytkownicy (nick, imie_nazwisko, haslo_hash) VALUES (?, ?, ?)", 
                  (nick.upper(), imie_nazwisko, hash_hasla))
        conn.commit()
        sukces = True
    except sqlite3.IntegrityError:
        sukces = False
    conn.close()
    return sukces

def pobierz_dane():
    conn = sqlite3.connect(DB_FILE)
    try:
        query = '''
            SELECT r.id, r.pracownik_nick, u.imie_nazwisko, r.start_date, r.koniec_date, r.kierunek, r.w_zamian 
            FROM rotacje r
            JOIN uzytkownicy u ON r.pracownik_nick = u.nick
        '''
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame(columns=["id", "pracownik_nick", "imie_nazwisko", "start_date", "koniec_date", "kierunek", "w_zamian"])
    conn.close()
    return df

def dodaj_rotacje_db(nick, start, koniec, kierunek, w_zamian):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO rotacje (pracownik_nick, start_date, koniec_date, kierunek, w_zamian)
        VALUES (?, ?, ?, ?, ?)
    ''', (nick.upper(), start, koniec, kierunek, w_zamian))
    conn.commit()
    conn.close()

def usun_rotacje_db(id_rotacji, nick):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM rotacje WHERE id = ? AND pracownik_nick = ?", (id_rotacji, nick.upper()))
    conn.commit()
    conn.close()

def usun_uzytkownika_z_bazy(nick_do_usuniecia):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM rotacje WHERE pracownik_nick = ?", (nick_do_usuniecia.upper(),))
    c.execute("DELETE FROM uzytkownicy WHERE nick = ?", (nick_do_usuniecia.upper(),))
    conn.commit()
    conn.close()

init_db()

if 'zalogowany_nick' not in st.session_state:
    st.session_state.zalogowany_nick = None
if 'zalogowany_imie' not in st.session_state:
    st.session_state.zalogowany_imie = None

if st.session_state.zalogowany_nick is None:
    st.title("✈️ Giełda Rotacji Lotniczych")
    zakladka_logowanie, zakladka_rejestracja = st.tabs(["🔒 Zaloguj się", "📝 Utwórz nowe konto"])
    
    with zakladka_logowanie:
        wpisany_nick = st.text_input("Twój Nick:", key="login_nick").strip().upper()
        wpisane_haslo = st.text_input("Twoje Hasło osobiste:", type="password", key="login_pass")
        if st.button("Wejdź do aplikacji", use_container_width=True):
            if wpisany_nick and wpisane_haslo:
                imie_uzytkownika = weryfikuj_logowanie(wpisany_nick, wpisane_haslo)
                if imie_uzytkownika:
                    st.session_state.zalogowany_nick = wpisany_nick
                    st.session_state.zalogowany_imie = imie_uzytkownika
                    st.success(f"Witaj, {imie_uzytkownika}!")
                    st.rerun()
                else:
                    st.error("Nieprawidłowy nick lub hasło osobiste!")
            else:
                st.warning("Uzupełnij oba pola logowania.")
                
    with zakladka_rejestracja:
        nowy_nick = st.text_input("Wpisz swój oficjalny Nick:", help="System automatycznie zamieni litery na duże.", key="reg_nick").strip().upper()
        nowe_imie = st.text_input("Twoje Imię i Nazwisko:")
        nowe_haslo_osobiste = st.text_input("Wymyśl swoje prywatne Hasło osobiste:", type="password", key="reg_pass")
        if st.button("Stwórz konto", use_container_width=True):
            if not nowy_nick or not nowe_imie or not nowe_haslo_osobiste:
                st.error("❌ Wypełnij wszystkie pola formularza rejestracji!")
            elif " " in nowy_nick:
                st.error("❌ Nick nie może zawierać spacji!")
            elif sprawdz_czy_nick_zajety(nowy_nick):
                st.error("❌ Ten nick jest już zarejestrowany w bazie!")
            else:
                udana_rejestracja = zarejestruj_uzytkownika(nowy_nick, nowe_imie, nowe_haslo_osobiste)
                if udana_rejestracja:
                    st.session_state.zalogowany_nick = nowy_nick
                    st.session_state.zalogowany_imie = nowe_imie
                    st.success("🎉 Konto utworzone i zalogowane pomyślnie!")
                    st.rerun()
                else:
                    st.error("Coś poszło nie tak. Spróbuj ponownie.")
    st.stop()

st.title("✈️ Giełda Rotacji Lotniczych")

st.sidebar.markdown(f"👤 Zalogowany: **{st.session_state.zalogowany_imie}**")
st.sidebar.markdown(f"🔑 Twój Nick: `{st.session_state.zalogowany_nick}`")
if st.sidebar.button("Wyloguj się"):
    st.session_state.zalogowany_nick = None
    st.session_state.zalogowany_imie = None
    st.rerun()

ZAKLADKI = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia"]
if st.session_state.zalogowany_nick == NICK_ADMINA.upper():
    ZAKLADKI.append("🛠️ Panel Admina")

wybrana_zakladka = st.sidebar.radio("Nawigacja", ZAKLADKI)
baza_rotacji = pobierz_dane()

if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    st.subheader("Filtry wyszukiwania")
    col1, col2 = st.columns(2)
    with col1:
        szukany_kierunek = st.text_input("🛫 Kierunek docelowy (np. JFK):", "").strip().upper()
    with col2:
        filtruj_daty = st.checkbox("📅 Filtruj po zakresie dat")
        szukany_zakres = st.date_input("Wybierz przedział czasu:", value=(datetime.today(), datetime.today())) if filtruj_daty else None

    wyniki = baza_rotacji.copy()
    if not wyniki.empty:
        wyniki = wyniki[wyniki["pracownik_nick"] != st.session_state.zalogowany_nick]
    
    if szukany_kierunek and not wyniki.empty:
        wyniki = wyniki[wyniki["kierunek"].str.contains(szukany_kierunek, case=False, na=False)]
        
    if filtruj_daty and szukany_zakres and len(szukany_zakres) == 2 and not wyniki.empty:
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
            naglowek = f"✈️ {row['kierunek'].upper()} | 📅 {row['start_date']} do {row['koniec_date']}"
            with st.expander(naglowek, expanded=True):
                st.write(f"👤 **Wystawiający:** {row['imie_nazwisko']} (`@{row['pracownik_nick'].upper()}`)")
                st.warning(f"🔄 **Warunki wymiany:** {row['w_zamian']}")
                if st.button(f"Zaproponuj wymianę", key=f"trade_{row['id']}", use_container_width=True):
                    st.success(f"Zgłoszono chęć wymiany! Skontaktuj się z użytkownikiem: {row['imie_nazwisko']} (`@{row['pracownik_nick'].upper()}`).")

elif wybrana_zakladka == "📤 Wystaw swoją rotację":
    st.header("📤 Dodaj nową rotację")
    with st.form("form_dodaj_rotacje"):
        nowy_kierunek = st.text_input("Kierunek docelowy (np. JFK, CDG):").strip().upper()
        col_start, col_end = st.columns(2)
        with col_start:
            data_start = st.date_input("Start rotacji:", min_value=datetime.today())
        with col_end:
            data_koniec = st.date_input("Koniec rotacji:", min_value=datetime.today())
        w_zamian = st.text_area("Za co chcesz się wymienić?")
        submit = st.form_submit_button("Zapisz w bazie danych")
        if submit:
            if data_koniec < data_start:
                st.error("Błąd: Data zakończenia nie może być wcześniejsza niż startu!")
            elif nowy_kierunek and w_zamian:
                dodaj_rotacje_db(st.session_state.zalogowany_nick, str(data_start), str(data_koniec), nowy_kierunek, w_zamian)
                st.success("Rotacja została dodana do bazy!")
                st.rerun()
            else:
