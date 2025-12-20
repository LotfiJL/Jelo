import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# =========================
# CONFIGURATION PAGE
# =========================
st.set_page_config(page_title="Dashboard Impact & Rupture", layout="wide")

# =========================
# INITIALISATION SESSION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =========================
# AUTHENTIFICATION SIMPLE
# =========================
def login():
    st.sidebar.title("🔐 Connexion")
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    if st.sidebar.button("Se connecter"):
        if username == "Lotfi" and password == "Jellali":
            st.session_state.logged_in = True
        else:
            st.sidebar.error("❌ Identifiant ou mot de passe incorrect")

# =========================
# DASHBOARD
# =========================
def run_dashboard():

    # =========================
    # SIDEBAR IMAGE & FILTRES
    # =========================
    st.sidebar.image("Lotfi.png", width=80)
    st.sidebar.title("Filtres")

    # =========================
    # CHARGEMENT DATA
    # =========================
    df = pd.read_csv("Jelo.csv", sep=";", encoding="latin1")
    df.columns = df.columns.str.strip()

    num_cols = [
        "Besoin","Dispo_TIS","PDP","DISPO_IDL",
        "Stock_restant_IDL","SS","LeadTime_Semaine","CA_unitaire"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.sort_values(["Référence","Semaine"])

    # =========================
    # CALCUL STOCK_RESTANT_IDL
    # =========================
    def calcul_stock_idl(df):
        df = df.sort_values(["Référence","Semaine"]).copy()
        stock_idl_dict = {}
        for idx, row in df.iterrows():
            ref = row["Référence"]
            besoin = row["Besoin"]
            if ref not in stock_idl_dict:
                stock_idl_dict[ref] = 0

            stock_arrive = 0
            idx_pos = df.index.get_loc(idx)
            if idx_pos > 0:
                prev_row = df.iloc[idx_pos - 1]
                if prev_row["Référence"] == ref:
                    stock_arrive = prev_row["PDP"] + prev_row["Dispo_TIS"]

            stock_idl = stock_idl_dict[ref] + stock_arrive - besoin
            df.loc[idx, "Stock_restant_IDL"] = stock_idl
            stock_idl_dict[ref] = stock_idl

        return df

    df = calcul_stock_idl(df)

    # =========================
    # COMMENTAIRES & STATUT
    # =========================
    def get_status(row):
        if row["Stock_restant_IDL"] < 0:
            return "⛔ Arrêt client"
        elif row["Stock_restant_IDL"] < row["SS"]:
            return "⚠️ SS non couvert"
        else:
            return "✅ OK"

    df["Statut"] = df.apply(get_status, axis=1)

    # =========================
    # FILTRES AVEC OPTION "TOUT"
    # =========================
    def multiselect_with_all(label, options):
        all_label = "✅ Tout"
        display_options = [all_label] + list(options)
        selected = st.sidebar.multiselect(label, display_options, default=display_options)
        if all_label in selected:
            return list(options)  # Retourne toutes les options réelles
        else:
            return selected

    ref_selected = multiselect_with_all("Référence", df["Référence"].unique())
    client_selected = multiselect_with_all("Client", df["Client"].unique())
    semaine_selected = multiselect_with_all("Semaine", df["Semaine"].unique())

    df_f = df[
        df["Référence"].isin(ref_selected) &
        df["Client"].isin(client_selected) &
        df["Semaine"].isin(semaine_selected)
    ]

    # =========================
    # HEADER
    # =========================
    st.title("📊 Dashboard Impact & Rupture – Analyse Planning & PDP")

    # =========================
    # KPI
    # =========================
    st.subheader("📈 Indicateurs clés")
    c1, c2, c3 = st.columns(3)
    c1.metric("Besoin total", int(df_f["Besoin"].sum()))
    c2.metric("Stock restant total", int(df_f["Stock_restant_IDL"].sum()))
    c3.metric("Refs en alerte", int((df_f["Statut"] != "✅ OK").sum()))

    # =========================
    # SYNTHESE ETAT PAR SEMAINE
    # =========================
    st.subheader("📊 État des références par semaine")
    df_etat = (
        df_f
        .groupby(["Semaine", "Statut"])
        .agg(Nb_refs=("Référence", "nunique"))
        .reset_index()
        .pivot(index="Semaine", columns="Statut", values="Nb_refs")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    st.dataframe(df_etat, use_container_width=True)

    # =========================
    # TABLE DETAILLEE
    # =========================
    st.subheader("📋 Détail Planning & Impact")
    cols = [
        "Référence","Semaine","Client","Besoin",
        "Dispo_TIS","PDP","Stock_restant_IDL","SS","Statut"
    ]
    st.dataframe(df_f[cols].sort_values(["Référence","Semaine"]), use_container_width=True)

    # =========================
    # GRAPHIQUE STOCK
    # =========================
    st.subheader("📊 Stock restant vs SS")
    fig_stock = px.line(
        df_f, x="Semaine", y="Stock_restant_IDL",
        color="Référence", markers=True
    )
    fig_stock.add_hline(y=df_f["SS"].max(), line_dash="dash", line_color="red")
    st.plotly_chart(fig_stock, use_container_width=True)

    st.success("🎯 Pilotage hebdomadaire clair : OK / SS non couvert / Arrêt client.")

# =========================
# MAIN
# =========================
if not st.session_state.logged_in:
    login()
else:
    run_dashboard()
