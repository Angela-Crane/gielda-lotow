import streamlit as st
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
    c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE UPPER(nick) = ? AND haslo_hash = ?", (nick.upper(), hash_do_sprawdzenia))
    user = c.fetchone()
    conn.close()
    return user if user else None

def sprawdz_czy_nick_zajety(nick):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM uzytkownicy WHERE UPPER(nick) = ?", (nick.upper(),))
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
    return sukses

def pobierz_wszystkie_rotacje():
    """Pobiera rotacje bezpośrednio jako standardową listę słowników Pythona."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    query = '''
        SELECT r.id, r.pracownik_nick, u.imie_nazwisko, r.start_date, r.koniec_date, r.kierunek, r.w_zamian 
        FROM rotacje r
        LEFT JOIN uzytkownicy u ON UPPER(r.pracownik_nick) = UPPER(u.nick)
    '''
    c.execute(query)
    rekordy = c.fetchall()
    conn.close()
    
    lista_rotacji = []
    for r in rekordy:
        lista_rotacji.append({
            "id": r[0],
            "pracownik_nick": r[1] if r[1] else "",
            "imie_nazwisko": r[2] if r[2] else "Nieznany",
            "start_date": r[3] if r[3] else "",
            "koniec_date": r[4] if r[4] else "",
            "kierunek": r[5] if r[5] else "",
            "w_zamian": r[6] if r[6] else ""
        })
    return lista_rotacji

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
    c.execute("DELETE FROM rotacje WHERE id = ? AND UPPER(pracownik_nick) = ?", (id_rotacji, nick.upper()))
    conn.commit()
    conn.close()

def usun_uzytkownika_z_bazy(nick_do_usuniecia):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM rotacje WHERE UPPER(pracownik_nick) = ?", (nick_do_usuniecia.upper(),))
    c.execute("DELETE FROM uzytkownicy WHERE UPPER(nick) = ?", (nick_do_usuniecia.upper(),))
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
wszystkie_rotacje = pobierz_wszystkie_rotacje()

# --- ZAKŁADKA 1: FILTROWANIE ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    st.subheader("Filtry wyszukiwania")
    col1, col2 = st.columns(2)
    with col1:
        szukany_kierunek = st.text_input("🛫 Kierunek docelowy (np. JFK):", "").strip().upper()
    with col2:
        filtruj_daty = st.checkbox("📅 Filtruj po zakresie dat")
        szukany_zakres = st.date_input("Wybierz przedział czasu:", value=(datetime.today(), datetime.today())) if filtruj_daty else None

    # Bezpieczne wyciąganie ofert innych użytkowników
    wyniki = []
    for r in wszystkie_rotacje:
        if r["pracownik_nick"].upper() != st.session_state.zalogowany_nick.upper():
            # Filtrowanie po kierunku
            if szukany_kierunek and szukany_kierunek not in r["kierunek"].upper():
                continue
            # Filtrowanie po dacie
            if filtruj_daty and szukany_zakres and len(szukany_zakres) == 2:
                od_daty = szukany_zakres[0]
                do_daty = szukany_zakres[1]
                r_start = datetime.strptime(r["start_date"], "%Y-%m-%d").date()
                r_koniec = datetime.strptime(r["koniec_date"], "%Y-%m-%d").date()
                if not (r_start <= do_daty and r_koniec >= od_daty):
                    continue
            wyniki.append(r)

    st.divider()
    st.subheader(f"Dostępne oferty ({len(wyniki)})")
    if not wyniki:
        st.info("Brak pasujących rotacji od innych pracowników.")
    else:
        for r in wyniki:
            naglowek = f"✈️ {r['kierunek'].upper()} | 📅 {r['start_date']} do {r['koniec_date']}"
            with st.expander(naglowek, expanded=True):
                st.write(f"👤 **Wystawiający:** {r['imie_nazwisko']} (`@{r['pracownik_nick'].upper()}`)")
                st.warning(f"🔄 **Warunki wymiany:** {r['w_zamian']}")
                if st.button(f"Zaproponuj wymianę", key=f"trade_{r['id']}", use_container_width=True):
                    st.success(f"Zgłoszono chęć wymiany! Skontaktuj się z użytkownikiem: {r['imie_nazwisko']} (`@{r['pracownik_nick'].upper()}`).")

# --- ZAKŁADKA 2: DODAWANIE ---
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
