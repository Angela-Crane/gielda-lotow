import streamlit as st
from datetime import datetime

# Konfiguracja strony mobilnej
st.set_page_config(page_title="Wymiana Rotacji Lotniczych", page_icon="✈️", layout="centered")

# ==================== TAJNY NICK ADMINISTRATORA ====================
NICK_ADMINA = "RUTKSA17"

# ==================== CAŁKOWICIE UPROSZCZONA PAMIĘĆ ====================
if 'konta' not in st.session_state:
    st.session_state.konta = {"RUTKSA17": {"imie": "ADMINISTRATOR", "haslo": "ADMIN123"}}

if 'oferty' not in st.session_state:
    st.session_state.oferty = []

if 'propozycje' not in st.session_state:
    st.session_state.propozycje = []

if 'licznik_id_ofert' not in st.session_state:
    st.session_state.licznik_id_ofert = 1

# Inicjalizacja domyślnego indeksu dla nawigacji
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

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
            elif nowy_nick in st.session_state.konta:
                st.error("Ten nick jest już zajęty!")
            else:
                st.session_state.konta[nowy_nick] = {"imie": nowe_imie, "haslo": nowe_haslo}
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

# Dynamiczna lista zakładek
ZAKLADKI = ["🔎 Szukaj i Filtruj", "📤 Wystaw swoją rotację", "📋 Moje ogłoszenia", "📩 Otrzymane Propozycje"]
if st.session_state.user_nick == NICK_ADMINA:
    ZAKLADKI.append("🛠️ Panel Admina")

if st.session_state.nav_index >= len(ZAKLADKI):
    st.session_state.nav_index = 0

# Wyświetlanie menu bocznego
wybrana_zakladka = st.sidebar.radio(
    "Nawigacja", 
    ZAKLADKI, 
    index=st.session_state.nav_index, 
    key=f"navigation_radio_{st.session_state.nav_index}"
)

# Zapis aktualnej pozycji użytkownika, gdy klika ręcznie
st.session_state.nav_index = ZAKLADKI.index(wybrana_zakladka)

# --- ZAKŁADKA 1: SZUKAJ I FILTRUJ ---
if wybrana_zakladka == "🔎 Szukaj i Filtruj":
    st.header("🔎 Znajdź rotację na wymianę")
    szukany_kierunek = st.text_input("🛫 Wpisz kierunek docelowy (np. JFK):").strip().upper()
    
    st.write("---")
    st.subheader("Dostępne loty innych pracowników:")
    
    licznik_ofert = 0
    for o in st.session_state.oferty:
        if not isinstance(o, dict) or "nick" not in o:
            continue
            
        if o["nick"] != st.session_state.user_nick:
            if szukany_kierunek and szukany_kierunek not in o.get("kierunek", "").upper():
                continue
            licznik_ofert += 1
            
            o_id = o.get("id", f"{o.get('kierunek')}_{o.get('start')}")
            
            with st.expander(f"✈️ {o.get('kierunek', 'BRAK')} | 📅 {o.get('start')} do {o.get('koniec')}", expanded=True):
                st.write(f"👤 **Wystawca:** {o.get('imie')} (`@{o.get('nick')}`)")
                st.write(f"🔄 **Chce w zamian:** {o.get('w_zamian')}")
                
                st.write("---")
                tekst_propozycji = st.text_input("Co proponujesz w zamian za ten lot?", key=f"input_{o_id}", placeholder="Wpisz rejs lub daty...")
                
                if st.button(f"Wyślij propozycję wymiany", key=f"btn_{o_id}", use_container_width=True):
                    if tekst_propozycji.strip():
                        st.session_state.propozycje.append({
                            "id_oferty": o_id,
                            "kierunek_oferty": o.get("kierunek"),
                            "daty_oferty": f"{o.get('start')} do {o.get('koniec')}",
                            "wlasciciel_nick": o.get("nick"),
                            "proponujacy_nick": st.session_state.user_nick,
                            "proponujacy_imie": st.session_state.user_imie,
                            "co_proponuje": tekst_propozycji.strip()
                        })
                        st.success(f"Twój warunek wymiany został wysłany do @{o.get('nick')}!")
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
                st.session_state.oferty.append({
                    "id": st.session_state.licznik_id_ofert,
                    "nick": st.session_state.user_nick,
                    "imie": st.session_state.user_imie,
                    "kierunek": kierunek,
                    "start": str(data_start),
                    "koniec": str(data_koniec),
                    "w_zamian": w_zamian
                })
                st.session_state.licznik_id_ofert += 1
                st.session_state.nav_index = 2
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola formularza.")

# --- ZAKŁADKA 3: MOJE OGŁOSZENIA ---
elif wybrana_zakladka == "📋 Moje ogłoszenia":
    st.header("📋 Twoje aktualne ogłoszenia")
    
    moje_loty = []
    for o in st.session_state.oferty:
        if isinstance(o, dict) and o.get("nick") == st.session_state.user_nick:
            moje_loty.append(o)
            
    if not moje_loty:
        st.info("Nie wystawiłeś obecnie żadnych lotów na giełdę.")
    else:
        for o in moje_loty:
            o_id = o.get("id", f"{o.get('kierunek')}_{o.get('start')}")
            st.write(f"✈️ **{o.get('kierunek')}** ({o.get('start')} do {o.get('koniec')})")
            st.write(f"🔄 Oczekiwania: {o.get('w_zamian']}")
            if st.button("Usuń ogłoszenie", key=f"del_{o_id}", use_container_width=True):
                if o in st.session_state.oferty:
                    st.session_state.oferty.remove(o)
                # Zabezpieczone filtrowanie usuwające błąd linii 193 i 220
                st.session_state.propozycje = [p for p in st.session_state.propozycje if isinstance(p, dict) and p.get("id_oferty") != o_id]
                st.success("Ogłoszenie usunięte!")
                st.rerun()
            st.write("---")

# --- ZAKŁADKA 4: OTRZYMANE PROPOZYCJE ---
elif wybrana_zakladka == "📩 Otrzymane Propozycje":
    st.header("📩 Propozycje wymiany od załogi")
    
    moje_propozycje = []
    for p in st.session_state.propozycje:
        if isinstance(p, dict) and p.get("wlasciciel_nick") == st.session_state.user_nick:
            moje_propozycje.append(p)
    
    if not moje_propozycje:
        st.info("Nie otrzymałeś jeszcze żadnych konkretnych propozycji wymiany.")
    else:
        for p in moje_propozycje:
            with st.container():
                st.write(f"📌 Dotyczy Twojego lotu: **{p.get('kierunek_oferty')}** ({p.get('daty_oferty')})")
                st.info(f"👤 **{p.get('proponujacy_imie')}** (`@{p.get('proponujacy_nick')}`) oferuje w zamian:\n\n**{p.get('co_proponuje')}**")
                
                if st.button("Odrzuć tę propozycję", key=f"Reject_{p.get('id_oferty')}_{p.get('proponujacy_nick')}", use_container_width=True):
                    if p in st.session_state.propozycje:
                        st.session_state.propozycje.remove(p)
