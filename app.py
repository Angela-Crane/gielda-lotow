import streamlit as st
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# ==================== CAŁKOWICIE UPROSZCZONA PAMIĘĆ ====================
if 'konta' not in st.session_state:
    st.session_state.konta = {"RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "Angela007"}}

if 'oferty' not in st.session_state:
    st.session_state.oferty = []

# ==================== SYSTEM LOGOWANIA / REJESTRACJI ====================
if 'user_nick' not in st.session_state:
    st.session_state.user_nick = None
if 'user_imie' not in st.session_state:
    st.session_state.user_imie = None

if st.session_state.user_nick is None:
    st.title("✈️ Giełda Rotacji Lotniczych")
    zakladka_logowanie, zakladka_rejestracja = st.tabs(["🔒 Zaloguj się", "📝 Utwórz nowe konto"])
    
    with zakladka_logowanie:
        wpisany_nick = st.text_input("Twój Nick:", key="l_nick").strip().upper()
        wpisane_haslo = st.text_input("Twoje Hasło:", type="password", key="l_pass")
        
        if st.button("Wejdź do aplikacji", use_container_width=True):
            if wpisany_nick in st.session_state.konta and st.session_state.konta[wpisany_nick]["haslo"] == wpisane_haslo:
                st.session_state.user_nick = wpisany_nick
                st.session_state.user_imie = st.session_state.konta[wpisany_nick]["imie"]
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
            elif nowy_nick in st.session_state.konta:
                st.error("Ten nick jest już zajęty!")
            else:
                st.session_state.konta[nowy_nick] = {"imie": nowe_imie, "haslo": nowe_haslo}
                st.session_state.user_nick = nowy_nick
                st.session_state.user_imie = nowe_imie
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
    st.rerun()

# Lista zakładek (Panel Admina widoczny tylko dla RUTKSA17)
ZAKLADKI = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia"]
if st.session_state.user_nick == NICK_ADMINA:
    ZAKLADKI.append("🛠️ Panel Admina")

wybrana_zakladka = st.sidebar.radio("Nawigacja", ZAKLADKI)

# --- ZAKŁADKA 1: SZUKAJ I FILTRUJ ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukany_kierunek = st.text_input("🛫 Wpisz kierunek docelowy (np. JFK):").strip().upper()
    
    st.write("---")
    st.subheader("Dostępne loty innych pracowników:")
    
    licznik_ofert = 0
    for o in st.session_state.oferty:
        if o["nick"] != st.session_state.user_nick:
            if szukany_kierunek and szukany_kierunek not in o["kierunek"]:
                continue
            licznik_ofert += 1
            with st.expander(f"✈️ {o['kierunek']} | 📅 {o['start']} do {o['koniec']}", expanded=True):
                st.write(f"👤 **Wystawiachy:** {o['imie']} (`@{o['nick']}`)")
                st.warning(f"🔄 **Chce w zamian:** {o['w_zamian']}")
                if st.button(f"Zaproponuj wymianę", key=f"trade_{o['kierunek']}_{o['start']}"):
                    st.success(f"Zgłoszono chęć wymiany! Skontaktuj się z: {o['imie']} (`@{o['nick']}`).")
                    
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
                st.session_state.oferty.append({
                    "nick": st.session_state.user_nick,
                    "imie": st.session_state.user_imie,
                    "kierunek": kierunek,
                    "start": str(data_start),
                    "koniec": str(data_koniec),
                    "w_zamian": w_zamian
                })
                st.success("Rotacja została dodana!")
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola formularza.")

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    
    moje_loty = [o for o in st.session_state.oferty if o["nick"] == st.session_state.user_nick]
    
    if not moje_loty:
        st.info("Nie wystawiłeś obecnie żadnych lotów na giełdę.")
    else:
        for o in moje_loty:
            st.write(f"✈️ **{o['kierunek']}** ({o['start']} do {o['koniec']})")
            st.write(f"🔄 Oczekiwania: {o['w_zamian']}")
            if st.button("Usuń ogłoszenie", key=f"del_{o['kierunek']}_{o['start']}", use_container_width=True):
                st.session_state.oferty.remove(o)
                st.success("Ogłoszenie usunięte!")
                st.rerun()
            st.write("---")

# --- ZAKŁADKA 4: PANEL ADMINA ---
elif wybrana_zakladka == "🛠️ Panel Admina":
    st.header("🛠️ Panel Zarządzania Użytkownikami")
    st.write("Usuń konto pracownika, aby mógł założyć je na nowo z tym samym nickiem.")
    
    nick_do_skasowania = st.text_input("Wpisz NICK do usunięcia:").strip().upper()
    
    if st.button("🚨 Usuń użytkownika na stałe", use_container_width=True):
        if nick_do_skasowania in st.session_state.konta:
            if nick_do_skasowania == NICK_ADMINA:
                st.error("Nie możesz usunąć własnego konta administratora!")
            else:
                # Usuń konto
                del st.session_state.konta[nick_do_skasowania]
                # Usuń jego loty z giełdy
                st.session_state.oferty = [o for o in st.session_state.oferty if o["nick"] != nick_do_skasowania]
                st.success(f"Pomyślnie usunięto użytkownika @{nick_do_skasowania}.")
                st.rerun()
        else:
            st.error("Taki użytkownik nie istnieje w bazie.")
