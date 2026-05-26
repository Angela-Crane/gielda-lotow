import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# ==================== POŁĄCZENIE Z GOOGLE SHEETS ====================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Błąd połączenia z Google Sheets. Sprawdź konfigurację Secrets!")
    st.stop()

def pobierz_tabele(nazwa_arkusza, kolumny):
    """Pobiera dane z konkretnej zakładki Arkusza Google."""
    try:
        df = conn.read(worksheet=nazwa_arkusza, ttl="0s")
        if df.empty:
            return pd.DataFrame(columns=kolumny)
        return df
    except Exception:
        return pd.DataFrame(columns=kolumny)

def zapisz_tabele(nazwa_arkusza, df):
    """Zapisuje cały DataFrame z powrotem do Arkusza Google."""
    try:
        conn.update(worksheet=nazwa_arkusza, data=df)
    except Exception as e:
        st.error(f"Nie udało się zapisać danych do Google Sheets: {e}")

# Inicjalizacja i wczytanie tabel (Konta, Oferty, Propozycje)
df_konta = pobierz_tabele("uzytkownicy", ["nick", "imie", "haslo"])
df_oferty = pobierz_tabele("oferty", ["id", "nick", "imie", "kierunek", "start", "koniec", "w_zamian"])
df_propozycje = pobierz_tabele("propozycje", ["id_oferty", "kierunek_oferty", "daty_oferty", "wlasciciel_nick", "proponujacy_nick", "proponujacy_imie", "prop_kierunek", "prop_start", "prop_koniec", "prop_uwagi"])

# Upewnienie się, że Admin istnieje na stałe w tabeli
if NICK_ADMINA not in df_konta["nick"].values:
    nowy_admin = pd.DataFrame([{"nick": NICK_ADMINA, "imie": "ADMINISTRATOR", "haslo": "ADMIN123"}])
    df_konta = pd.concat([df_konta, nowy_admin], ignore_index=True)
    zapisz_tabele("uzytkownicy", df_konta)

# ==================== SYSTEM WBUDOWANEJ SESJI ====================
if 'user_nick' not in st.session_state:
    st.session_state.user_nick = None
if 'user_imie' not in st.session_state:
    st.session_state.user_imie = None
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

# ==================== PANEL LOGOWANIA / REJESTRACJI ====================
if st.session_state.user_nick is None:
    st.title("✈️ Giełda Rotacji Lotniczych")
    zakladka_logowanie, zakladka_rejestracja = st.tabs(["🔒 Zaloguj się", "📝 Utwórz nowe konto"])
    
    with zakladka_logowanie:
        wpisany_nick = st.text_input("Twój Nick:", key="l_nick").strip().upper()
        wpisane_haslo = st.text_input("Twoje Hasło:", type="password", key="l_pass")
        
        if st.button("Wejdź do aplikacji", use_container_width=True):
            user_row = df_konta[df_konta["nick"] == wpisany_nick]
            if not user_row.empty and str(user_row.iloc[0]["haslo"]) == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = str(user_row.iloc[0]["imie"])
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
            elif nowy_nick in df_konta["nick"].values:
                st.error("Ten nick jest już zajęty!")
            else:
                nowy_user = pd.DataFrame([{"nick": nowy_nick, "imie": nowe_imie, "haslo": nowe_haslo}])
                df_konta = pd.concat([df_konta, nowy_user], ignore_index=True)
                zapisz_tabele("uzytkownicy", df_konta)
                
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

# --- ZAKŁADKA 1: SZUKAJ I FILTRUJ ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukany_kierunek = st.text_input("🛫 Wpisz kierunek docelowy (np. JFK):").strip().upper()
    st.write("---")
    
    licznik_ofert = 0
    for idx, o in df_oferty.iterrows():
        if str(o["nick"]) != st.session_state.user_nick:
            if szukany_kierunek and szukany_kierunek not in str(o["kierunek"]):
                continue
            licznik_ofert += 1
            
            with st.expander(f"✈️ {o['kierunek']} | 📅 {o['start']} do {o['koniec']}", expanded=True):
                st.write(f"👤 **Wystawca:** {o['imie']} (`@{o['nick']}`)")
                st.write(f"🔄 **Chce w zamian:** {o['w_zamian']}")
                st.write("---")
                
                st.markdown("**Co oferujesz w zamian za ten lot?**")
                p_kierunek = st.text_input("Kierunek Twojego lotu (np. CDG):", key=f"p_kier_{o['id']}").strip().upper()
                
                col1, col2 = st.columns(2)
                with col1:
                    p_start = st.date_input("Start Twojego lotu:", min_value=datetime.today(), key=f"p_start_{o['id']}")
                with col2:
                    p_koniec = st.date_input("Koniec Twojego lotu:", min_value=datetime.today(), key=f"p_koniec_{o['id']}")
                    
                p_uwagi = st.text_input("Dodatkowe uwagi (opcjonalnie):", key=f"p_uwagi_{o['id']}", placeholder="np. Szukam wolnego...")
                
                if st.button(f"Wyślij propozycję wymiany", key=f"btn_{o['id']}", use_container_width=True):
                    if p_kierunek:
                        if p_koniec < p_start:
                            st.error("Błąd: Data zakończenia Twojego lotu nie może być wcześniejsza niż startu!")
                        else:
                            nowa_prop = pd.DataFrame([{
                                "id_oferty": int(o["id"]),
                                "kierunek_oferty": str(o["kierunek"]),
                                "daty_oferty": f"{o['start']} do {o['koniec']}",
                                "wlasciciel_nick": str(o["nick"]),
                                "proponujacy_nick": str(st.session_state.user_nick),
                                "proponujacy_imie": str(st.session_state.user_imie),
                                "prop_kierunek": str(p_kierunek),
                                "prop_start": str(p_start),
                                "prop_koniec": str(p_koniec),
                                "prop_uwagi": str(p_uwagi.strip())
                            }])
                            df_propozycje = pd.concat([df_propozycje, nowa_prop], ignore_index=True)
                            zapisz_tabele("propozycje", df_propozycje)
                            st.success("Twoja propozycja wymiany została pomyślnie wysłana!")
                            st.rerun()
                    else:
                        st.error("Wpisz kierunek lotu, który oferujesz w zamian!")
                    
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
                nowe_id = int(datetime.now().timestamp())
                nowa_oferta = pd.DataFrame([{
                    "id": nowe_id,
                    "nick": str(st.session_state.user_nick),
                    "imie": str(st.session_state.user_imie),
                    "kierunek": str(kierunek),
                    "start": str(data_start),
                    "koniec": str(data_koniec),
                    "w_zamian": str(w_zamian)
                }])
                df_oferty = pd.concat([df_oferty, nowa_oferta], ignore_index=True)
                zapisz_tabele("oferty", df_oferty)
                st.session_state.nav_index = 2
                st.rerun()
