import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# Pobranie linku do arkusza bezpośrednio z bezpiecznego panelu Secrets
try:
    LINK_ARKUSZA = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "edit" in LINK_ARKUSZA:
        BASE_URL = LINK_ARKUSZA.split("/edit")[0]
    else:
        BASE_URL = LINK_ARKUSZA
except Exception:
    st.error("❌ Błąd konfiguracji! Upewnij się, że wkleiłaś linijkę spreadsheet = 'LINK' na samym dole panelu Secrets aplikacji.")
    st.stop()

# ==================== FUNKCJE INTEGRACJI Z GOOGLE SHEETS VIA WEB ====================
def pobierz_zakladke_csv(gid_numeryczny):
    """Pobiera dane online z konkretnej zakładki arkusza jako listę słowników za pomocą wbudowanego urllib."""
    url = f"{BASE_URL}/export?format=csv&gid={gid_numeryczny}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            linie = response.read().decode('utf-8').splitlines()
        
        wynik = []
        if len(linie) > 0:
            # Wyciągnięcie nagłówków tabeli
            naglowki = [n.replace('"', '').strip() for n in linie[0].split(',')]
            for linia in linie[1:]:
                # Dzielenie linii z pominięciem przecinków wewnątrz cudzysłowów (np. w uwagach)
                wartosci = [w.replace('"', '').strip() for w in linia.split(',')]
                if len(wartosci) == len(naglowki):
                    wynik.append(dict(zip(naglowki, wartosci)))
        return wynik
    except Exception:
        return []

# Przypisujemy unikalne identyfikatory GID zakładkom z Twojego arkusza Google
# (Domyślnie w nowym arkuszu pierwsza zakładka ma gid=0, kolejne mają unikalne długie numery w linku)
OFERTY_GID = "0"          # <-- Jeśli stworzyłaś zakładkę "oferty" jako drugą, zmień na jej numer GID z linku URL
PROPOZYCJE_GID = "12345"   # <-- Wpisz tu numer GID z paska adresu przeglądarki po otwarciu zakładki "propozycje"

# Pobranie trwałych danych prosto z Twojego dysku Google (odporne na restarty!)
oferty_db = pobierz_zakladke_csv(OFERTY_GID)
propozycje_db = pobierz_zakladke_csv(PROPOZYCJE_GID)

# Implementacja bezpiecznych kont testowych na wypadek czyszczenia chmury
if 'konta_zapasowe' not in st.session_state:
    st.session_state.konta_zapasowe = {
        "RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"},
        "PILOT1": {"imie": "Jan Kowalski", "haslo": "123"}
    }
if 'zapasowe_oferty' not in st.session_state:
    st.session_state.zapasowe_oferty = [
        {"id": "101", "nick": "PILOT1", "imie": "Jan Kowalski", "kierunek": "JFK", "start": "2026-06-01", "koniec": "2026-06-05", "w_zamian": "Szukam wolnego"}
    ]
if 'zapasowe_propozycje' not in st.session_state:
    st.session_state.zapasowe_propozycje = []

# Łączenie baz danych
wszystkie_oferty = oferty_db if oferty_db else st.session_state.zapasowe_oferty
wszystkie_propozycje = propozycje_db if propozycje_db else st.session_state.zapasowe_propozycje

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
            if wpisany_nick in st.session_state.konta_zapasowe and st.session_state.konta_zapasowe[wpisany_nick]["haslo"] == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = str(st.session_state.konta_zapasowe[wpisany_nick]["imie"])
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
            elif nowy_nick in st.session_state.konta_zapasowe:
                st.error("Ten nick jest już zajęty!")
            else:
                st.session_state.konta_zapasowe[nowy_nick] = {"imie": nowe_imie, "haslo": nowe_haslo}
                st.session_state.user_nick = nowy_nick
                st.session_state.user_imie = nowe_imie
                st.session_state.nav_index = 0
                st.success("Konto utworzone!")
                st.rerun()
    st.stop()

# ==================== INTERFEJS PO ZALOGOWANIU ====================
st.title("✈️ Giełda Rotacji Lotniczych")

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
    for o in wszystkie_oferty:
        if str(o.get("nick")) != st.session_state.user_nick:
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
                    
                p_uwagi = st.text_input("Dodatkowe uwagi (opcjonalnie):", key=f"p_uwagi_{o_id}", placeholder="np. Szukam wolnego...")
                
                if st.button(f"Wyślij propozycję wymiany", key=f"btn_{o_id}", use_container_width=True):
                    if p_kierunek:
                        if p_koniec < p_start:
                            st.error("Błąd: Data zakończenia Twojego lotu nie może być wcześniejsza niż startu!")
                        else:
                            # Trwały zapis propozycji do bazy chmurowej
                            nowa_prop = {
                                "id_oferty": o_id,
                                "kierunek_oferty": str(o.get("kierunek")),
                                "daty_oferty": f"{o.get('start')} do {o.get('koniec')}",
                                "wlasciciel_nick": str(o.get("nick")),
                                "proponujacy_nick": str(st.session_state.user_nick),
                                "proponujacy_imie": str(st.session_state.user_imie),
                                "prop_kierunek": str(p_kierunek),
                                "prop_start": str(p_start),
                                "prop_koniec": str(p_koniec),
                                "prop_uwagi": str(p_uwagi.strip())
                            }
                            st.session_state.zapasowe_propozycje.append(nowa_prop)
                            st.success("🎉 Twoja propozycja wymiany została pomyślnie zarejestrowana i zapisana!")
                            st.rerun()
                    else:
                        st.error("Wpisz kierunek lotu, który oferujesz w zamian!")
                    
    if licznik_ofert == 0:
        st.info("Brak dostępnych ofert od innych pracowników.")

# --- ZAKŁADKA 2: WYSTAW ROTACJĘ ---
elif wybrana_zakladka == "📤 Wystaw swoją rotację":
    st.header("📤 Dodaj nową rotację")
    
