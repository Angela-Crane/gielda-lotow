import streamlit as st
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# ==================== EMULACJA BEZPIECZNEJ BAZY CHMUROWEJ ONLINE ====================
if 'Baza_Konta' not in st.session_state:
    st.session_state.Baza_Konta = {
        "RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"},
        "PILOT1": {"imie": "Jan Kowalski", "haslo": "123"}
    }

if 'Baza_Oferty' not in st.session_state:
    st.session_state.Baza_Oferty = [
        {"id": 101, "nick": "PILOT1", "imie": "Jan Kowalski", "kierunek": "JFK", "start": "2026-06-01", "koniec": "2026-06-05", "w_zamian": "Szukam wolnego"}
    ]

if 'Baza_Propozycje' not in st.session_state:
    st.session_state.Baza_Propozycje = []

if 'active_index' not in st.session_state:
    st.session_state.active_index = 0

# ==================== SYSTEM KONTROLI SESJI ====================
if 'session_user' not in st.session_state:
    st.session_state.session_user = None
if 'session_name' not in st.session_state:
    st.session_state.session_name = None

# ==================== EKRAN LOGOWANIA / REJESTRACJI ====================
if st.session_state.session_user is None:
    st.title("✈️ Giełda Rotacji Lotniczych")
    tab_log, tab_reg = st.tabs(["🔒 Zaloguj się", "📝 Utwórz nowe konto"])
    
    with tab_log:
        login_n = st.text_input("Twój Nick:", key="main_l_nick").strip().upper()
        login_p = st.text_input("Twoje Hasło:", type="password", key="main_l_pass")
        
        if st.button("Wejdź do aplikacji", use_container_width=True):
            if login_n in st.session_state.Baza_Konta and st.session_state.Baza_Konta[login_n]["haslo"] == login_p:
                st.session_state.session_user = login_n
                st.session_state.session_name = st.session_state.Baza_Konta[login_n]["imie"]
                st.session_state.active_index = 0
                st.rerun()
            else:
                st.error("Nieprawidłowy nick lub hasło!")
                
    with tab_reg:
        reg_n = st.text_input("Wymyśl swój Nick (bez spacji):", key="main_r_nick").strip().upper()
        reg_i = st.text_input("Twoje Imię i Nazwisko:", key="main_r_imie").strip()
        reg_p = st.text_input("Wymyśl swoje Hasło:", type="password", key="main_r_pass")
        
        if st.button("Stwórz konto", use_container_width=True):
            if not reg_n or not reg_i or not reg_p:
                st.error("Wypełnij wszystkie pola!")
            elif " " in reg_n:
                st.error("Nick nie może zawierać spacji!")
            elif reg_n in st.session_state.Baza_Konta:
                st.error("Ten nick jest już zajęty!")
            else:
                st.session_state.Baza_Konta[reg_n] = {"imie": reg_i, "haslo": reg_p}
                st.session_state.session_user = reg_n
                st.session_state.session_name = reg_i
                st.session_state.active_index = 0
                st.success("Konto utworzone!")
                st.rerun()
    st.stop()

# ==================== INTERFEJS GŁÓWNY ====================
st.title("✈️ Giełda Rotacji Lotniczych")

st.sidebar.markdown(f"👤 Zalogowany: **{st.session_state.session_name}**")
st.sidebar.markdown(f"🔑 Twój Nick: `{st.session_state.session_user}`")
if st.sidebar.button("Wyloguj się"):
    st.session_state.session_user = None
    st.session_state.session_name = None
    st.session_state.active_index = 0
    st.rerun()

MENU = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia", "📩 Otrzymane Propozycje"]
if st.session_state.session_user == NICK_ADMINA:
    MENU.append("🛠️ Panel Admina")

if st.session_state.active_index >= len(MENU):
    st.session_state.active_index = 0

view = st.sidebar.radio("Nawigacja", MENU, index=st.session_state.active_index, key=f"nav_key_{st.session_state.active_index}")
st.session_state.active_index = MENU.index(view)

# --- SEKCJA 1: SZUKAJ I FILTRUJ ---
if view == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukaj = st.text_input("🛫 Wpisz kierunek docelowy (np. JFK):").strip().upper()
    st.write("---")
    
    puste = True
    for o in st.session_state.Baza_Oferty:
        if o["nick"] != st.session_state.session_user:
            if szukaj and szukaj not in o["kierunek"]:
                continue
            puste = False
            
            with st.expander(f"✈️ {o['kierunek']} | 📅 {o['start']} do {o['koniec']}", expanded=True):
                st.write(f"👤 **Wystawca:** {o['imie']} (`@{o['nick']}`)")
                st.write(f"🔄 **Chce w zamian:** {o['w_zamian']}")
                st.write("---")
                
                st.markdown("**Co oferujesz w zamian za ten lot?**")
                pk = st.text_input("Kierunek Twojego lotu (np. CDG):", key=f"pk_{o['id']}").strip().upper()
                
                col1, col2 = st.columns(2)
                with col1:
                    ps = st.date_input("Start Twojego lotu:", min_value=datetime.today(), key=f"ps_{o['id']}")
                with col2:
                    pk_date = st.date_input("Koniec Twojego lotu:", min_value=datetime.today(), key=f"pk_d_{o['id']}")
                    
                pu = st.text_input("Dodatkowe uwagi (opcjonalnie):", key=f"pu_{o['id']}")
                
                if st.button("Wyślij propozycję wymiany", key=f"btn_{o['id']}", use_container_width=True):
                    if pk:
                        if pk_date < ps:
                            st.error("Błąd: Data zakończenia lotu nie może być wcześniejsza niż startu!")
                        else:
                            st.session_state.Baza_Propozycje.append({
                                "id_oferty": o["id"],
                                "kierunek_oferty": o["kierunek"],
                                "daty_oferty": f"{o['start']} do {o['koniec']}",
                                "wlasciciel_nick": o["nick"],
                                "proponujacy_nick": st.session_state.session_user,
                                "proponujacy_imie": st.session_state.session_name,
                                "prop_kierunek": pk,
                                "prop_start": str(ps),
                                "prop_koniec": str(pk_date),
                                "prop_uwagi": pu.strip()
                            })
                            st.success("Twoja propozycja wymiany została pomyślnie wysłana!")
                            st.rerun()
                    else:
                        st.error("Wpisz kierunek lotu, który oferujesz w zamian!")
                        
    if puste:
        st.info("Brak dostępnych ofert od innych pracowników.")

# --- SEKCJA 2: WYSTAW ROTACJĘ ---
elif view == "📤 Wystaw swoją rotację":
    st.header("📤 Dodaj nową rotację")
    
    with st.form("form_wystaw"):
        kierunek = st.text_input("Kierunek (np. JFK, CDG):").strip().upper()
        d_start = st.date_input("Start rotacji:", min_value=datetime.today())
        d_koniec = st.date_input("Koniec rotacji:", min_value=datetime.today())
        w_zamian = st.text_area("Za co chcesz się wymienić?")
        submit = st.form_submit_button("Zapisz ogłoszenie")
        
        if submit:
            if d_koniec < d_start:
                st.error("Błąd: Data zakończenia nie może być wcześniejsza niż startu!")
            elif kierunek and w_zamian:
                nowe_id = int(datetime.now().timestamp() * 1000)
                st.session_state.Baza_Oferty.append({
                    "id": nowe_id,
                    "nick": st.session_state.session_user,
                    "imie": st.session_state.session_name,
                    "kierunek": kierunek,
                    "start": str(d_start),
                    "koniec": str(d_koniec),
                    "w_zamian": w_zamian
                })
                st.session_state.active_index = 2
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola formularza.")

# --- SEKCJA 3: MOJE OGŁOSZENIA ---
elif view == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    
    moje = [o for o in st.session_state.Baza_Oferty if o["nick"] == st.session_state.session_user]
    
    if not moje:
        st.info("Nie wystawiłeś obecnie żadnych lotów na giełdę.")
    else:
        for o in moje:
            st.write(f"✈️ **{o['kierunek']}** ({o['start']} do {o['koniec']})")
            st.write(f"🔄 Oczekiwania: {o['w_zamian']}")
            
            if st.button("Usuń ogłoszenie", key=f"del_{o['id']}", use_container_width=True):
                st.session_state.Baza_Oferty = [item for item in st.session_state.Baza_Oferty if item["id"] != o["id"]]
                st.session_state.Baza_Propozycje = [p for p in st.session_state.Baza_Propozycje if p["id_oferty"] != o["id"]]
                st.success("Ogłoszenie usunięte!")
                st.rerun()
            st.divider()

# --- SEKCJA 4: OTRZYMANE PROPOZYCJE ---
elif view == "📩 Otrzymane Propozycje":
    st.header("📩 Propozycje wymiany od załogi")
    
    moje_p = [p for p in st.session_state.Baza_Propozycje if p["wlasciciel_nick"] == st.session_state.session_user]
    
    if not moje_p:
        st.info("Nie otrzymałeś jeszcze żadnych propozycji wymiany.")
    else:
        # Dodanie indeksowania pętli naprawiające linię 214
        for idx, p in enumerate(moje_p):
            with st.container():
                st.write(f"📌 Dotyczy Twojego lotu: **{p['kierunek_oferty']}** ({p['daty_oferty']})")
                st.info(
                    f"👤 **{p['proponujacy_imie']}** (`@{p['proponujacy_nick']}`) proponuje lot:\n\n"
                    f"🛫 **Kierunek:** {p['prop_kierunek']}\n"
