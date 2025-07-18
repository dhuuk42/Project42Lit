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

st.title("📊 Gewichtsentwicklung")
st.markdown("_Aller Teilnehmer im Vergleich_")
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
    # Hole die bisherigen Einträge des Users
    weight_entries = get_weights_for_user(st.session_state.user_id)

    # Öffentlicher Verlauf
    all_data = get_all_weights_for_all_users()
    if all_data:
        df_all = pd.DataFrame(all_data, columns=["User", "Date", "Weight"])
        df_all["Date"] = pd.to_datetime(df_all["Date"]).dt.date

        # --- Date Range Filter ---
        min_date = df_all["Date"].min()
        max_date = df_all["Date"].max()

        # Quick filter buttons
        col1, col2, col3= st.columns(3)
        with col1:
            quick_all = st.button("Gesamter Zeitraum")
        with col2:
            quick_month = st.button("Letzter Monat")
        with col3:
            quick_week = st.button("Letzte 7 Tage")

        # Default filter values
        filter_start = min_date
        filter_end = max_date

        # Apply quick filters
        if quick_month:
            filter_start = max(min_date, max_date - pd.Timedelta(days=30))
        elif quick_week:
            filter_start = max(min_date, max_date - pd.Timedelta(days=6))

        with st.expander("📅 Manuelle Datumsauswahl"):    # Manual date selection (overrides quick filters if changed)
            col5, col6 = st.columns(2)
            with col5:
                filter_start = st.date_input("Von", value=filter_start, min_value=min_date, max_value=max_date, key="filter_start")
            with col6:
                filter_end = st.date_input("Bis", value=filter_end, min_value=min_date, max_value=max_date, key="filter_end")

        # Get all user colors for the chart
        user_colors = get_all_user_colors()
        all_users = sorted(df_all["User"].unique())
        selected_users = st.multiselect("Teilnehmer auswählen", options=all_users, default=all_users)
     
        # Gefilterte Daten
        filtered_df = df_all[
            (df_all["User"].isin(selected_users)) &
            (df_all["Date"] >= filter_start) &
            (df_all["Date"] <= filter_end)
        ]

        # Interpolation: create a complete date range
        if not filtered_df.empty:
            all_dates = pd.date_range(filtered_df["Date"].min(), filtered_df["Date"].max())
            pivot = filtered_df.pivot(index="Date", columns="User", values="Weight")
            pivot = pivot.reindex(all_dates)  # fill missing dates
            interpolated = pivot.interpolate(method="linear", limit_direction="both")

            # --- Colors for users ---
            user_list = list(pivot.columns)
            def get_random_color():
                return "#{:06x}".format(random.randint(0, 0xFFFFFF))
            color_map = {user: user_colors.get(user) or get_random_color() for user in user_list}
            domain = user_list
            color_range = [color_map[user] for user in user_list]
            # ------------------------

            real_points = pivot.reset_index().melt(id_vars="index", var_name="User", value_name="Weight")
            real_points = real_points.dropna()
            real_points = real_points.rename(columns={"index": "Date"})
            chart = (
                alt.Chart(interpolated.reset_index().melt(id_vars="index", var_name="User", value_name="Weight"))
                .mark_line()
                .encode(
                    x="index:T",
                    y=alt.Y("Weight:Q", scale=alt.Scale(domain=[70, 130])),
                    color=alt.Color("User:N", scale=alt.Scale(domain=domain, range=color_range))
                )
                +
                alt.Chart(real_points)
                .mark_point(filled=True, size=60)
                .encode(
                    x="Date:T",
                    y=alt.Y("Weight:Q", scale=alt.Scale(domain=[70, 130])),
                    color=alt.Color("User:N", scale=alt.Scale(domain=domain, range=color_range))
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Keine Daten für die ausgewählten Teilnehmer.")
    else:
        st.info("Noch keine Einträge vorhanden.")
        filtered_df = pd.DataFrame(columns=["User", "Date", "Weight"])  # <--- HINZUGEFÜGT

    st.divider()
    # 🏆 Gewichtverlust-Rankings
    st.subheader("🏆 Top 3 Gewichtverlust (absolut & relativ)")

    all_data = get_all_weights_for_all_users()
    if all_data:
        df_all = pd.DataFrame(all_data, columns=["User", "Date", "Weight"])
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        # Find start and latest weight for each user
        start_weights = df_all.sort_values("Date").groupby("User").first().reset_index()
        latest_weights = df_all.sort_values("Date").groupby("User").last().reset_index()
        merged = pd.merge(
            start_weights[["User", "Weight"]],
            latest_weights[["User", "Weight"]],
            on="User",
            suffixes=("_start", "_latest")
        )
        merged["loss_abs"] = merged["Weight_start"] - merged["Weight_latest"]
        merged["loss_rel"] = merged["loss_abs"] / merged["Weight_start"] * 100

        # Round all weights and losses to 1 decimal
        merged["Weight_start"] = merged["Weight_start"].round(1)
        merged["Weight_latest"] = merged["Weight_latest"].round(1)
        merged["loss_abs"] = merged["loss_abs"].round(1)
        merged["loss_rel"] = merged["loss_rel"].round(1)

        # Absolute Ranking
        abs_rank = merged.sort_values("loss_abs", ascending=False).head(3)
        abs_rank = abs_rank[["User", "Weight_start", "Weight_latest", "loss_abs"]].rename(
            columns={"Weight_start": "Startgewicht", "Weight_latest": "Aktuell", "loss_abs": "Verlust (kg)"}
        )
        # Format to one decimal as string
        abs_rank["Startgewicht"] = abs_rank["Startgewicht"].map("{:.1f}".format)
        abs_rank["Aktuell"] = abs_rank["Aktuell"].map("{:.1f}".format)
        abs_rank["Verlust (kg)"] = abs_rank["Verlust (kg)"].map("{:.1f}".format)
        st.markdown("**Absolut (kg):**")
        st.table(abs_rank.reset_index(drop=True))

        # Relative Ranking
        rel_rank = merged.sort_values("loss_rel", ascending=False).head(3)
        rel_rank = rel_rank[["User", "Weight_start", "Weight_latest", "loss_rel"]].rename(
            columns={"Weight_start": "Startgewicht", "Weight_latest": "Aktuell", "loss_rel": "Verlust (%)"}
        )
        rel_rank["Startgewicht"] = rel_rank["Startgewicht"].map("{:.1f}".format)
        rel_rank["Aktuell"] = rel_rank["Aktuell"].map("{:.1f}".format)
        rel_rank["Verlust (%)"] = rel_rank["Verlust (%)"].map("{:.1f}".format)
        st.markdown("**Relativ (%):**")
        st.table(rel_rank.reset_index(drop=True))
    else:
        st.info("Noch keine Einträge für Rankings vorhanden.")

    if st.button("Logout"):
       st.session_state.user_id = None
       st.session_state.username = ""
       cookies["user_id"] = ""
       cookies["username"] = ""
       st.rerun()
