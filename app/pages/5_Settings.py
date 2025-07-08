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

st.set_page_config(
    page_title="Project42 - Tracker",  # This will be the sidebar/main page name
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

st.title("⚙️ User Settings")

st.divider()

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
    # --- User Color Picker (Collapsible) ---
    st.subheader("🎨 Benutzerdefinierte Farbe für den Verlauf")
    with st.expander("🎨 Farbe auswählen"):
        current_color = get_user_color(st.session_state.user_id) or "#004b9c"
        color_input = st.color_picker("Wähle deine Farbe für den Verlauf", value=current_color)
        # Validate hex code (must be #RRGGBB)
        hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6})$")
        if st.button("Farbe speichern"):
            if hex_pattern.match(color_input):
                set_user_color(st.session_state.user_id, color_input)
                st.success("Farbe gespeichert! Aktualisiere die Seite, um die Änderung zu sehen.")
            else:
                st.error("Bitte gib einen gültigen Hex-Code ein (z.B. #1a2b3c).")
    
    # Passwort ändern
    st.subheader("🔑 Account Einstellungen")
    with st.expander("🔑 Passwort ändern"):
        with st.form("change_password_form"):
            old_pw = st.text_input("Altes Passwort", type="password")
            new_pw = st.text_input("Neues Passwort", type="password")
            new_pw2 = st.text_input("Neues Passwort wiederholen", type="password")
            pw_submit = st.form_submit_button("Passwort ändern")
            if pw_submit:
                if not authenticate_user(st.session_state.username, old_pw):
                    st.error("Altes Passwort ist falsch.")
                elif new_pw != new_pw2:
                    st.error("Die neuen Passwörter stimmen nicht überein.")
                elif len(new_pw) < 6:
                    st.error("Das neue Passwort muss mindestens 6 Zeichen lang sein.")
                else:
                    if change_password(st.session_state.user_id, new_pw):
                        st.success("Passwort erfolgreich geändert.")
                    else:
                        st.error("Fehler beim Ändern des Passworts.")

    # 🗑️ Eigene Gewichtseinträge löschen
    st.subheader("🗑️ Einträge löschen")

    # When displaying user's own entries
    with st.expander("🗑️ Wähle Datensätze"):
        my_entries = get_weights_for_user(st.session_state.user_id)
        df = pd.DataFrame(my_entries, columns=["ID", "Datum", "Gewicht", "Notiz", "Erstellt am"])

        if my_entries:
            # Show timestamp and note in the table
            df["Erstellt am"] = pd.to_datetime(df["Erstellt am"])
            df["Label"] = (
                df["Erstellt am"].dt.strftime("%Y-%m-%d %H:%M") +  # Show timestamp
                " – " + df["Gewicht"].astype(str) + " kg" +
                df["Notiz"].fillna("").apply(lambda n: f" ({n})" if n else "")
            )

            entry_to_delete = st.selectbox(
                "Eintrag auswählen",
                options=df["ID"],
                format_func=lambda x: df[df["ID"] == x]["Label"].values[0]
            )

            # Display all entries with timestamp and note (user's own entries)
            st.dataframe(
                df[["Datum", "Gewicht", "Notiz", "Erstellt am"]]
                .sort_values("Erstellt am", ascending=False)
                .rename(columns={"Datum": "Datum Gewicht","Gewicht": "Gewicht (kg)", "Notiz": "Notiz","Erstellt am": "Eingetragen am"})
                .assign(**{"Gewicht (kg)": lambda x: x["Gewicht (kg)"].round(1)}),  # round to 1 decimal
                hide_index=True,
                use_container_width=True
            )

            if st.button("Eintrag löschen"):
                delete_weight_entry(entry_to_delete, st.session_state.user_id)
                st.success("Eintrag gelöscht!")
                st.rerun()
        else:
            st.info("Du hast noch keine Einträge.")
    
    
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = ""
        cookies["user_id"] = ""
        cookies["username"] = ""
        st.rerun()
    # Challenge Tracking vorbereiten
    init_challenge_table()
    today = date.today()

