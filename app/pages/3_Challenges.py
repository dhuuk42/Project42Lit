import streamlit as st
import pandas as pd
from datetime import date
from db import (
    authenticate_user,
    register_user,
    insert_weight,
    get_all_weights_for_all_users,
    register_test_users,
    init_challenge_table,
    log_challenge_completion,
    has_completed_challenge,
    get_challenge_status_all_users,
    delete_weight_entry,
    get_weights_for_user,
    change_password,
    get_user_color, 
    set_user_color, 
    get_all_user_colors 
)
import random
from streamlit_cookies_manager import EncryptedCookieManager
import altair as alt
import re

# Initialize cookie manager
cookies = EncryptedCookieManager(
    prefix="wt_",  # optional, to avoid conflicts
    password="super-secret-password"  # use a strong secret in production!
)
if not cookies.ready():
    st.stop()

# Session-Init
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""

# Restore session from cookies if available
if st.session_state.user_id is None and cookies.get("user_id"):
    st.session_state.user_id = int(cookies.get("user_id"))
    st.session_state.username = cookies.get("username")

# Testnutzer einmalig registrieren
try:
    register_test_users()
except Exception as e:
    st.warning(f"Fehler beim Anlegen von Testusern: {e}")

st.title("🤖 Marvin’s Tages-Challenge")

# Login/Registrierung
if st.session_state.user_id is None:
    st.subheader("🔐 Login")

    tab1, tab2 = st.tabs(["Login", "Registrieren"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            login_submitted = st.form_submit_button("Login")
            if login_submitted:
                user_id = authenticate_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    cookies["user_id"] = str(user_id)
                    cookies["username"] = username
                    st.success(f"Eingeloggt als {username}")
                    st.rerun()
                else:
                    st.error("Ungültige Zugangsdaten.")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Neuer Benutzername")
            new_password = st.text_input("Neues Passwort", type="password")
            register_submitted = st.form_submit_button("Registrieren")
            if register_submitted:
                if register_user(new_username, new_password):
                    st.success("Benutzer registriert. Bitte einloggen.")
                else:
                    st.error("Benutzername existiert bereits.")
else:
    init_challenge_table()
    today = date.today()
    # 🧠 Marvin der Fitness-Coach
    def get_marvin_challenge():
        challenges = [
            # Bestehende Challenges
            "Heute: 5 Kniebeugen. Oder wenigstens 3. Oder denk einfach intensiv an Bewegung.",
            "Setz dich 3x bewusst gerade hin. Das zählt als Sport. Behauptet jedenfalls mein Rückenmodul.",
            "Stell dich 20 Sekunden lang auf ein Bein. Marvin'sche Balance-Challenge.",
            "Trink heute 2 Gläser Wasser extra. Flüssigkeit ist die Grundlage allen Daseins. Leider.",
            "Geh 10 Minuten spazieren. Oder lauf einfach davon.",
            "Mach 3 Liegestütze. Oder 1 und fall dramatisch um.",
            "Atme heute einmal tief durch. Ja, das ist auch eine Challenge.",
            "Räume ein Regal auf. Marvin würde es nicht tun. Sei besser als Marvin.",
            "Bewege dich 2 Minuten zur Musik. Auch Kopfnicken zählt.",
            "Geh heute eine Treppe, statt den Aufzug. Wenn’s sein muss auch rückwärts. Für den Spaß.",
            "Schreib jemandem in der Gruppe 'Du schaffst das!'. Motivation teilen zählt auch.",
            "Versuche 30 Sekunden lang keinen sarkastischen Gedanken zu haben. Das ist die eigentliche Challenge.",
            "Schau 60 Sekunden lang aus dem Fenster und tu... nichts. Willkommen im Marvin-Modus.",
            "Benutze heute keine Ausrede. Außer natürlich: 'Marvin hat gesagt, ich darf.'",

            # Neue Nerd-Challenges
            "Star Wars-Modus: Mach einen Jedi-Ausfallschritt. Oder heb einfach die Hand und tu so, als ob du die Macht benutzt.",
            "Zähle heute rückwärts von 88. Wenn du bei 1 ankommst, überleg, ob du schnell genug für 1.21 Gigawatt bist.",
            "How I Met Your Mother sagt: Sag heute 1x 'Challenge accepted' – und tu dann wenigstens irgendwas.",
            "Sheldon würde sagen: Mach 3 Schritte im Uhrzeigersinn um deinen Platz. Nenn es: Kreis der Motivation.",
            "Scrubs-Style: Wenn du heute scheiterst, mach es wenigstens mit einem inneren Monolog und epischer Musik.",
            "Star Wars: Tu so, als würdest du einem Yoda auf der Schulter zuhören. Er wird sagen: 'Bewege dich, du musst!'",
            "Dr. Cox wäre enttäuscht, wenn du heute *nicht* wenigstens ein Glas Wasser trinkst. Oder alle.",
            "BTTF-Modus: Geh rückwärts 10 Schritte. Nenn es Zeitreise. Oder Gleichgewichtstraining.",
            "Heute keine Ausrede, es sei denn, du wurdest vom dunklen Lord der Couch gezwungen.",
            "Zähl deine Schritte so, als wärst du ein imperialer Marsch-Roboter. Dum Dum Da Da Dum.",
            "Stell dir vor, du bist Ted. Erzähl jemandem heute eine Geschichte, bei der du dich am Ende bewegst.",
            "Wie Sheldon: Setz dich heute bewusst auf *nicht* deinen Lieblingsplatz. Überrasch deinen Hintern.",
            "Mach heute 3 Hampelmänner. Nenn es den 'Bazinga-Booster'.",
            "Wenn du heute aus Versehen Sport machst – nenn es eine *origin story* wie in einer schlechten Sitcom.",
        ]
        return random.choice(challenges)

    st.divider()
    with st.container():
        if has_completed_challenge(st.session_state.user_id, today):
            st.success("Challenge bereits erledigt! Marvin ist... na ja... weniger unzufrieden.")
        else:
            st.markdown(f"*{get_marvin_challenge()}*")
            if st.button("✅ Challenge erledigt"):
                log_challenge_completion(st.session_state.user_id, today)
                st.success("Challenge gespeichert! Marvin ist leicht weniger deprimiert.")
                st.rerun()

    # Challenge Übersicht
    st.subheader("👀 Challenge-Erfüllung heute")
    status_list = get_challenge_status_all_users(today)
    status_df = pd.DataFrame(status_list, columns=["User", "Erledigt"])
    status_df["Erledigt"] = status_df["Erledigt"].map({True: "✅", False: "❌"})
    st.table(status_df)

    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = ""
        cookies["user_id"] = ""
        cookies["username"] = ""
        st.rerun()
