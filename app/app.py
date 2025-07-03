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
    get_weights_for_user
)
import random
from streamlit_cookies_manager import EncryptedCookieManager

# Initialize cookie manager
cookies = EncryptedCookieManager(
    prefix="wt_",  # optional, to avoid conflicts
    password="super-secret-password"  # use a strong secret in production!
)
if not cookies.ready():
    st.stop()

st.set_page_config(page_title="Weight Tracker", layout="centered")

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

st.title("🏋️ Project42 – Weight Tracker")

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
    st.success(f"Eingeloggt als {st.session_state.username}")
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = ""
        cookies["user_id"] = ""
        cookies["username"] = ""
        st.rerun()
    # Challenge Tracking vorbereiten
    init_challenge_table()
    today = date.today()
    

    # 🧠 Marvin der Fitness-Coach
    def get_marvin_challenge():
        challenges = [
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
          ]

        return random.choice(challenges)

    st.divider()
    with st.container():
        st.markdown("### 🤖 Marvin’s Tages-Challenge")
        st.markdown(f"*{get_marvin_challenge()}*")

        if has_completed_challenge(st.session_state.user_id, today):
            st.success("Challenge bereits erledigt! Marvin ist... na ja... weniger unzufrieden.")
        else:
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



    # Hole die bisherigen Einträge des Users
    weight_entries = get_weights_for_user(st.session_state.user_id)

    # Ermittle den letzten Eintrag, falls vorhanden
    if weight_entries:
        # Annahme: Liste ist sortiert nach Datum (falls nicht, bitte sortieren)
        last_weight = weight_entries[-1][2]  # Index 2 corresponds to the weight
    else:
        last_weight = 70.0  # Fallback-Wert, z. B. Mittelwert oder Standard

    with st.form("weight_form"):
        weight = st.number_input(
            "Dein Gewicht (kg)",
            min_value=20.0,
            max_value=300.0,
            step=0.1,
            value=last_weight
        )
        entry_date = st.date_input("Datum", value=date.today())
        note = st.text_input("Notiz (optional)")  # <-- NEW
        submitted = st.form_submit_button("Eintragen")

        if submitted:
            insert_weight(st.session_state.user_id, entry_date.isoformat(), weight, note)  # <-- Pass note
            st.success("Gewicht gespeichert!")



    # Öffentlicher Verlauf
    st.subheader("📊 Gewichtsentwicklung aller Teilnehmer")
    all_data = get_all_weights_for_all_users()
    if all_data:
        df_all = pd.DataFrame(all_data, columns=["User", "Date", "Weight"])
        df_all["Date"] = pd.to_datetime(df_all["Date"])

        # Auswahlmaske für User
        all_users = sorted(df_all["User"].unique())
        selected_users = st.multiselect("Teilnehmer auswählen", options=all_users, default=all_users)

        # Gefilterte Daten
        filtered_df = df_all[df_all["User"].isin(selected_users)]

        # Anzeige
        st.dataframe(filtered_df.sort_values(["Date", "User"], ascending=[False, True]))

        if not filtered_df.empty:
            st.line_chart(filtered_df.pivot(index="Date", columns="User", values="Weight"))
        else:
            st.info("Keine Daten für die ausgewählten Teilnehmer.")
    else:
        st.info("Noch keine Einträge vorhanden.")
        # 🗑️ Eigene Gewichtseinträge löschen
    st.subheader("🗑️ Eigene Einträge löschen")

    # When displaying user's own entries
    my_entries = get_weights_for_user(st.session_state.user_id)

    if my_entries:
        df = pd.DataFrame(my_entries, columns=["ID", "Datum", "Gewicht", "Notiz", "Erstellt am"])  # <-- Add columns
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.date
        df["Erstellt am"] = pd.to_datetime(df["Erstellt am"])  # Format as needed
        df["Label"] = df["Datum"].astype(str) + " – " + df["Gewicht"].astype(str) + " kg" + df["Notiz"].fillna("").apply(lambda n: f" ({n})" if n else "")

        entry_to_delete = st.selectbox(
            "Eintrag auswählen",
            options=df["ID"],
            format_func=lambda x: df[df["ID"] == x]["Label"].values[0]
        )

        if st.button("Eintrag löschen"):
            delete_weight_entry(entry_to_delete, st.session_state.user_id)
            st.success("Eintrag gelöscht!")
            st.rerun()
    else:
        st.info("Du hast noch keine Einträge.")

