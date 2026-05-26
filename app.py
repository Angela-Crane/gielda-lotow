import streamlit as st
import json
import urllib.request
import csv
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# Bezpośredni link pobierania z Twojego Secrets
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    BASE_URL = SHEET_URL.split("/edit") if "edit" in SHEET_URL else SHEET_URL
except Exception:
    st.error("❌ Brak konfiguracji! Upewnij się, że poprawnie zapisałaś link w panelu Secrets.")
    st.stop()

def pobierz_dane_z_chmury(gid_zakladki):
    """Pobiera dane online bezpośrednio z Twojego arkusza Google przy użyciu pancernego parsera CSV."""
    url = f"{BASE_URL}/export?format=csv&gid={gid_zakladki}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            linie = response.read().decode('utf-8').splitlines()
        
        wynik = []
        if len(linie) > 0:
            # Używamy wbudowanego modułu csv, który idealnie radzi sobie z przecinkami w tekstach
            reader = csv.DictReader(linie)
            for row in reader:
                # Czyszczenie cudzysłowów i spacji z danych
                czysty_wiersz = {str(k).strip(): str(v).strip() for k, v in row.items() if k is not None}
                wynik.append(czysty_wiersz)
        return wynik
    except Exception:
        return []

# Identyfikatory GID zakładki z Twojego adresu URL w przeglądarce
OFERTY_GID = "0"          
PROPOZYCJE_GID = "371196582" 

# Pobranie trwałych danych z dysku Google
oferty_db = pobierz_dane_z_chmury(OFERTY_GID)
propozycje_db = pobierz_dane_z_chmury(PROPOZYCJE_GID)

# Lokalne bazy zapasowe na wypadek braku połączenia lub pustego arkusza
if 'konta_zapas' not in st.session_state:
    st.session_state.konta_zapas = {
        "RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"},
        "PILOT1": {"imie": "Jan Kowalski", "haslo": "123"}
    }
if 'oferty_zapas' not in st.session_state:
    st.session_state.oferty_zapas = [
        {"id": "1001", "nick": "PILOT1", "imie": "Jan Kowalski", "kierunek": "JFK", "start": "2026-06-01", "koniec": "2026-06-05", "w_zamian": "Szukam wolnego"}
    ]
if 'propozycje_zapas' not in st.session_state:
    st.session_state.propozycje_zapas = []

# Łączenie i bezpieczna synchronizacja baz danych
wszystkie_oferty = oferty_db if oferty_db else st.session_state.oferty_zapas
wszystkie_propozycje = propozycje_db if propozycje_db else st.session_state.propozycje_zapas

# ==================== SYSTEM SESJI UŻYTKOWNIKA ====================
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
            if wpisany_nick in st.session_state.konta_zapas and st.session_state.konta_zapas[wpisany_nick]["haslo"] == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = str(st.session_state.konta_zapas[wpisany_nick]["imie"])
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
            elif nowy_nick in st.session_state.konta_zapas:
                st.error("Ten nick jest już zajęty!")
            else:
                st.session_state.konta_zapas[nowy_nick] = {"imie": nowe_imie, "haslo": nowe_haslo}
                st.session_state.user_nick = nowy_nick
                st.session_state.user_imie = nowe_imie
                st.session_state.nav_index = 0
                st.success("Konto utworzone!")
                st.rerun()
    st.stop()

# ==================== INTERFEJS PO ZALOGOWANIU ====================
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

wybrana_zakladka = st.sidebar.radio("Nawigacja", ZAKLADKI, index=st.session_state.nav_index, key=f"nav_radio_{st.session_state.nav_index}")
st.session_state.nav_index = ZAKLADKI.index(wybrana_zakladka)

# --- ZAKŁADKA 1: SZUKAJ I FILTRUJ ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukany_kierunek = st.text_input("Wpisz kierunek docelowy (np. JFK):").strip().upper()
    
    licznik_ofert = 0
    for o in wszystkie_oferty:
        # PANCERNE ZABEZPIECZENIE LINII 203: Sprawdzamy czy 'o' to słownik, ignorując uszkodzone rekordy tekstowe
        if not isinstance(o, dict) or "nick" not in o:
            continue
            
        if str(o.get("nick")).upper() != st.session_state.user_nick.upper():
            if szukany_kierunek and szukany_kierunek not in str(o.get("kierunek", "")):
                continue
            licznik_ofert += 1
            
            o_id = str(o.get("id", "101"))
            with st.expander(f"✈️ {o.get('kierunek')} | 📅 {o.get('start')} do {o.get('koniec')}", expanded=True):
                st.write(f"👤 **Wystawca:** {o.get('imie')} (`@{o.get('nick')}`)")
                st.write(f"🔄 **Chce w zamian:** {o.get('w_zamian')}")
                st.write("---")
                
                st.markdown("**Co oferujesz w zamian za ten lot?**")
                p_kierunek = st.text_input("Kierunek Twojego lotu (np. CDG):", key=f"p_kier_{o_id}").strip().upper()
                
                col1, col2 = st.columns(2)
                with col1:
                    p_start = st.date_input("Start Twojego lotu:", min_value=datetime.today(), key=f"p_start_{o_id}")
                with col2:
                    p_koniec = st.date_input("Koniec Twojego lotu:", min_value=datetime.today(), key=f"p_koniec_{o_id}")
                p_uwagi = st.text_input("Dodatkowe uwagi (opcjonalnie):", key=f"p_uwagi_{o_id}")
                
                if st.button("Wyślij propozycję wymiany", key=f"btn_{o_id}", use_container_width=True):
                    if p_kierunek:
                        st.session_state.propozycje_zapas.append({
                            "id_oferty": o_id,
                            "kierunek_oferty": str(o.get("kierunek")),
                            "daty_oferty": f"{o.get('start')} do {o.get('koniec')}",
                            "wlasciciel_nick": str(o.get("nick")),
                            "proponujacy_nick": st.session_state.user_nick,
                            "proponujacy_imie": st.session_state.user_imie,
                            "prop_kierunek": p_kierunek,
                            "prop_start": str(p_start),
                            "prop_koniec": str(p_koniec),
                            "prop_uwagi": p_uwagi.strip()
                        })
                        st.success("🎉 Wysłano pomyślnie!")
                        st.rerun()

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
        
        if submit and kierunek and w_zamian:
            nowe_id = str(int(datetime.now().timestamp() * 1000))
            st.session_state.oferty_zapas.append({
                "id": nowe_id, "nick": st.session_state.user_nick, "imie": st.session_state.user_imie,
                "kierunek": kierunek, "start": str(data_start), "koniec": str(data_koniec), "w_zamian": w_zamian
            })
            st.session_state.nav_index = 2
            st.rerun()

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    moje_loty = [o for o in wszystkie_oferty if isinstance(o, dict) and str(o.get("nick")).upper() == st.session_state.user_nick.upper()]
    
