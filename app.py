import streamlit as st
import json
import os
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

KONTA_FILE = "finalne_konta.json"
OFERTY_FILE = "finalne_oferty.json"
PROP_FILE = "finalne_propozycje.json"

# ==================== SYSTEM TRWAŁEGO ZAPISU (JSON) ====================
def wczytaj_dane(sciezka, domyslne):
    if not os.path.exists(sciezka):
        with open(sciezka, 'w', encoding='utf-8') as f:
            json.dump(domyslne, f, ensure_ascii=False, indent=4)
        return domyslne
    try:
        with open(sciezka, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return domyslne

def zapisz_dane(sciezka, dane):
    with open(sciezka, 'w', encoding='utf-8') as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)

# Inicjalizacja baz tekstowych - teraz konto Admina zapisuje się TRWALE przy pierwszym starcie
konta_db = wczytaj_dane(KONTA_FILE, {"RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"}})
oferty_db = wczytaj_dane(OFERTY_FILE, [])
propozycje_db = wczytaj_dane(PROP_FILE, [])

# Upewnienie się, że plik kont na pewno fizycznie istnieje i zawiera Admina
if "RUTKSA17" not in konta_db:
    konta_db["RUTKSA17"] = {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"}
    zapisz_dane(KONTA_FILE, konta_db)

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
            if wpisany_nick in konta_db and konta_db[wpisany_nick]["haslo"] == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = str(konta_db[wpisany_nick]["imie"])
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
            elif nowy_nick in konta_db:
                st.error("Ten nick jest już zajęty!")
            else:
                konta_db[nowy_nick] = {"imie": nowe_imie, "haslo": nowe_haslo}
                zapisz_dane(KONTA_FILE, konta_db)
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
    for o in ofertas_db if 'ofertas_db' in locals() else oferty_db: # Bezpieczne przekierowanie zmiennej
        if o["nick"] != st.session_state.user_nick:
            if szukany_kierunek and szukany_kierunek not in o["kierunek"]:
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
                            propozycje_db.append({
                                "id_oferty": o["id"],
                                "kierunek_oferty": o["kierunek"],
                                "daty_oferty": f"{o['start']} do {o['koniec']}",
                                "wlasciciel_nick": o["nick"],
                                "proponujacy_nick": st.session_state.user_nick,
                                "proponujacy_imie": st.session_state.user_imie,
                                "prop_kierunek": p_kierunek,
                                "prop_start": str(p_start),
                                "prop_koniec": str(p_koniec),
                                "prop_uwagi": p_uwagi.strip()
                            })
                            zapisz_dane(PROP_FILE, propozycje_db)
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
                nowe_id = int(datetime.now().timestamp() * 1000)
                
                oferty_db.append({
                    "id": nowe_id,
                    "nick": st.session_state.user_nick,
                    "imie": st.session_state.user_imie,
                    "kierunek": kierunek,
                    "start": str(data_start),
                    "koniec": str(data_koniec),
                    "w_zamian": w_zamian
                })
                zapisz_dane(OFERTY_FILE, oferty_db)
                st.session_state.nav_index = 2
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola formularza.")

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    
    moje_loty = [o for o in oferty_db if o["nick"] == st.session_state.user_nick]
    
    if not moje_loty:
        st.info("Nie wystawiłeś obecnie żadnych lotów na giełdę.")
    else:
        for o in moje_loty:
            st.write(f"✈️ **{o['kierunek']}** ({o['start']} do {o['koniec']})")
            st.write(f"🔄 Oczekiwania: {o['w_zamian']}")
            
            if st.button("Usuń ogłoszenie", key=f"del_{o['id']}", use_container_width=True):
                oferty_db.remove(o)
                zapisz_dane(OFERTY_FILE, oferty_db)
                propozycje_db = [p for p in propozycje_db if p["id_oferty"] != o["id"]]
