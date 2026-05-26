import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

DB_FILE = "gielda_nowa.db"

# ==================== INICJALIZACJA STAŁEJ BAZY DANYCH ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabela kont użytkowników
    c.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            nick TEXT PRIMARY KEY,
            imie TEXT,
            haslo TEXT
        )
    ''')
    # Tabela ogłoszeń rotacji
    c.execute('''
        CREATE TABLE IF NOT EXISTS oferty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nick TEXT,
            imie TEXT,
            kierunek TEXT,
            start TEXT,
            koniec TEXT,
            w_zamian TEXT
        )
    ''')
    # Tabela propozycji wymiany
    c.execute('''
        CREATE TABLE IF NOT EXISTS propozycje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferty INTEGER,
            kierunek_oferty TEXT,
            daty_oferty TEXT,
            wlasciciel_nick TEXT,
            proponujacy_nick TEXT,
            proponujacy_imie TEXT,
            co_proponuje TEXT
        )
    ''')
    # Automatyczne dodanie konta administratora, jeśli baza jest czysta
    c.execute("SELECT 1 FROM uzytkownicy WHERE nick = 'RUTKSA17'")
    if not c.fetchone():
        c.execute("INSERT INTO uzytkownicy (nick, imie, haslo) VALUES ('RUTKSA17', 'ADMINISTRATOR', 'ADMIN123')")
    conn.commit()
    conn.close()

init_db()

# ==================== OBSŁUGA TRWAŁEJ SESJI (Ciasteczka w przeglądarce) ====================
if 'user_nick' not in st.session_state:
    st.session_state.user_nick = None
if 'user_imie' not in st.session_state:
    st.session_state.user_imie = None
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

# ==================== SYSTEM LOGOWANIA / REJESTRACJI ====================
if st.session_state.user_nick is None:
    st.title("✈️ Giełda Rotacji Lotniczych")
    zakladka_logowanie, zakladka_rejestracja = st.tabs(["🔒 Zaloguj się", "📝 Utwórz nowe konto"])
    
    with zakladka_logowanie:
        wpisany_nick = st.text_input("Twój Nick:", key="l_nick").strip().upper()
        wpisane_haslo = st.text_input("Twoje Hasło:", type="password", key="l_pass")
        
        if st.button("Wejdź do aplikacji", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT imie, haslo FROM uzytkownicy WHERE nick = ?", (wpisany_nick,))
            user = c.fetchone()
            conn.close()
            
            if user and user[1] == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = user[0]
                st.session_state.nav_index = 0
                st.rerun()
            else:
                st.error("Nieprawidłowy nick lub hasło!")
                
    with zakladka_rejestracja:
        nowy_nick = st.text_input("Wymyśl swój Nick (bez spacji):", key="r_nick").strip().upper()
        nowe_imie = st.text_input("Twoje Imię i Nazwisko:", key="r_imie").strip()
        nowe_haslo = st.text_input("Wymyśl swoje Hasło:", type="password", key="r_pass")
        
        if st.button("Stwórz konto", use_container_width=True):
            if not nowy_nick or not nowe_imie or not nowe_haslo:
                st.error("Wypełnij wszystkie pola!")
            elif " " in nowy_nick:
                st.error("Nick nie może zawierać spacji!")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT 1 FROM uzytkownicy WHERE nick = ?", (nowy_nick,))
                zajety = c.fetchone()
                
                if zajety:
                    st.error("Ten nick jest już zajęty!")
                    conn.close()
                else:
                    c.execute("INSERT INTO uzytkownicy (nick, imie, haslo) VALUES (?, ?, ?)", (nowy_nick, nowe_imie, nowe_haslo))
                    conn.commit()
                    conn.close()
                    st.session_state.user_nick = nowy_nick
                    st.session_state.user_imie = nowe_imie
                    st.session_state.nav_index = 0
                    st.success("Konto utworzone!")
                    st.rerun()
    st.stop()

# ==================== INTERFEJS PO ZALOGOWANIU ====================
st.title("✈️ Giełda Rotacji Lotniczych")

# Panel boczny
st.sidebar.markdown(f"👤 Zalogowany: **{st.session_state.user_imie}**")
st.sidebar.markdown(f"🔑 Twój Nick: `{st.session_state.user_nick}`")
if st.sidebar.button("Wyloguj się"):
    st.session_state.user_nick = None
    st.session_state.user_imie = None
    st.session_state.nav_index = 0
    st.rerun()

ZAKLADKI = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia", "📩 Otrzymane Propozycje"]
if st.session_state.user_nick == NICK_ADMINA:
    ZAKLADKI.append("🛠️ Panel Admina")

if st.session_state.nav_index >= len(ZAKLADKI):
    st.session_state.nav_index = 0

wybrana_zakladka = st.sidebar.radio(
    "Nawigacja", 
    ZAKLADKI, 
    index=st.session_state.nav_index, 
    key=f"navigation_radio_{st.session_state.nav_index}"
)
st.session_state.nav_index = ZAKLADKI.index(wybrana_zakladka)

# --- POBIERANIE AKTUALNYCH DANYCH Z BAZY ---
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT id, nick, imie, kierunek, start, koniec, w_zamian FROM oferty")
wszystkie_oferty = [{"id": r[0], "nick": r[1], "imie": r[2], "kierunek": r[3], "start": r[4], "koniec": r[5], "w_zamian": r[6]} for r in c.fetchall()]
conn.close()

# --- ZAKŁADKA 1: SZUKAJ I FILTRUJ ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukany_kierunek = st.text_input("🛫 Wpisz kierunek docelowy (np. JFK):").strip().upper()
    st.write("---")
    
    licznik_ofert = 0
    for o in wszystkie_oferty:
        if o["nick"] != st.session_state.user_nick:
            if szukany_kierunek and szukany_kierunek not in o["kierunek"]:
                continue
            licznik_ofert += 1
            
            with st.expander(f"✈️ {o['kierunek']} | 📅 {o['start']} do {o['koniec']}", expanded=True):
                st.write(f"👤 **Wystawca:** {o['imie']} (`@{o['nick']}`)")
                st.write(f"🔄 **Chce w zamian:** {o['w_zamian']}")
                st.write("---")
                
                tekst_propozycji = st.text_input("Co proponujesz w zamian za ten lot?", key=f"input_{o['id']}", placeholder="Wpisz rejs lub daty...")
                
                if st.button(f"Wyślij propozycję wymiany", key=f"btn_{o['id']}", use_container_width=True):
                    if tekst_propozycji.strip():
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO propozycje (id_oferty, kierunek_oferty, daty_oferty, wlasciciel_nick, proponujacy_nick, proponujacy_imie, co_proponuje)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (o['id'], o['kierunek'], f"{o['start']} do {o['koniec']}", o['nick'], st.session_state.user_nick, st.session_state.user_imie, tekst_propozycji.strip()))
                        conn.commit()
                        conn.close()
                        st.success("Twój warunek wymiany został wysłany!")
                        st.rerun()
                    else:
                        st.error("Wpisz najpierw, co oferujesz w zamian!")
                    
    if licznik_ofert == 0:
        st.info("Brak dostępnych ofert od innych pracowników.")

# --- ZAKŁADKA 2: WYSTAW ROTACJĘ ---
elif wybrana_zakladka == "📤 Wystaw swoją rotację":
    st.header("📤 Dodaj nową rotację")
    
    with st.form("form_dodaj"):
        kierunek = st.text_input("Kierunek (np. JFK, CDG):").strip().upper()
        data_start = st.date_input("Start rotacji:", min_value=datetime.today())
        data_koniec = st.date_input("Koniec rotacji:", min_value=datetime.today())
        w_zamian = st.text_area("Za co chcesz się wymienić?")
        submit = st.form_submit_button("Zapisz ogłoszenie")
        
        if submit:
            if data_koniec < data_start:
                st.error("Błąd: Data zakończenia nie może być wcześniejsza niż startu!")
            elif kierunek and w_zamian:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO oferty (nick, imie, kierunek, start, koniec, w_zamian)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (st.session_state.user_nick, st.session_state.user_imie, kierunek, str(data_start), str(data_koniec), w_zamian))
                conn.commit()
                conn.close()
                st.session_state.nav_index = 2
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola formularza.")

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    
    moje_loty = [o for o in wszystkie_oferty if o["nick"] == st.session_state.user_nick]
    
    if not moje_loty:
        st.info("Nie wystawiłeś obecnie żadnych lotów na giełdę.")
    else:
        for o in moje_loty:
            st.write(f"✈️ **{o['kierunek']}** ({o['start']} do {o['koniec']})")
            st.write(f"🔄 Oczekiwania: {o['w_zamian']}")
            
            if st.button("Usuń ogłoszenie", key=f"del_{o['id']}", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM oferty WHERE id = ?", (o['id'],))
