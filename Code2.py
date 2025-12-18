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
        if username == "admin" and password == "motdepasse":
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

    # Conversion en numérique
    num_cols = ["Besoin","Dispo_TIS","PDP","DISPO_IDL","Stock_restant_IDL","SS","LeadTime_Semaine","CA_unitaire"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.sort_values(["Référence","Semaine"])

    # =========================
    # CALCUL STOCK_RESTANT_IDL CUMULATIF
    # =========================
    def calcul_stock_idl(df):
        df = df.sort_values(["Référence","Semaine"]).copy()
        stock_idl_dict = {}
        for idx, row in df.iterrows():
            ref = row["Référence"]
            besoin = row["Besoin"]
            dispo_tis = row["Dispo_TIS"]
            pdp = row["PDP"]
            lead_client = int(row["LeadTime_Semaine"])

            if ref not in stock_idl_dict:
                stock_idl_dict[ref] = {"last_stock": 0}

            # Stock disponible à l'arrivée cette semaine
            stock_arrive = 0
            semaine_idx = df.index.get_loc(idx)
            if semaine_idx > 0:
                prev_row = df.iloc[semaine_idx - 1]
                if prev_row["Référence"] == ref:
                    stock_arrive = prev_row["PDP"] + prev_row["Dispo_TIS"]

            stock_prev = stock_idl_dict[ref]["last_stock"]
            stock_idl = stock_prev + stock_arrive - besoin

            df.loc[idx, "Stock_restant_IDL"] = stock_idl
            stock_idl_dict[ref]["last_stock"] = stock_idl

        return df

    df = calcul_stock_idl(df)

    # =========================
    # COMMENTAIRES ET ALERTES
    # =========================
    def get_comment(row):
        if row["Stock_restant_IDL"] < 0:
            return f"⛔ Arrêt client : produire davantage"
        elif row["Stock_restant_IDL"] < row["SS"]:
            besoin_lancer = row["SS"] - row["Stock_restant_IDL"]
            return f"⚠️ Rupture : lancer {int(besoin_lancer)} pcs pour couvrir SS"
        else:
            return "✅ OK"

    df["Commentaire"] = df.apply(get_comment, axis=1)

    # =========================
    # FILTRES
    # =========================
    ref = st.sidebar.multiselect("Référence", df["Référence"].unique(), default=df["Référence"].unique())
    client = st.sidebar.multiselect("Client", df["Client"].unique(), default=df["Client"].unique())
    semaine = st.sidebar.multiselect("Semaine", df["Semaine"].unique(), default=df["Semaine"].unique())

    df_f = df[df["Référence"].isin(ref) & df["Client"].isin(client) & df["Semaine"].isin(semaine)]

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
    c3.metric("Ruptures / Alertes", int((df_f["Stock_restant_IDL"] < df_f["SS"]).sum()))

    # =========================
    # TABLE DETAILLEE
    # =========================
    st.subheader("📋 Tableau synthétique Planning & Impact")
    cols = ["Référence","Semaine","Client","Besoin","Dispo_TIS","PDP","DISPO_IDL","Stock_restant_IDL","SS","Commentaire","LeadTime_Semaine","CA_unitaire"]
    st.dataframe(df_f[cols].sort_values(["Référence","Semaine"]), use_container_width=True)

    # =========================
    # GRAPHIQUES
    # 1️⃣ Stock restant vs SS
    st.subheader("📊 Stock restant vs SS")
    fig_stock = px.line(df_f, x="Semaine", y="Stock_restant_IDL", color="Référence",
                        markers=True, hover_data=["Besoin","PDP","SS"],
                        title="Stock restant IDL par semaine")
    fig_stock.add_hline(y=df_f["SS"].max(), line_dash="dash", line_color="red", annotation_text="SS max", annotation_position="top right")
    st.plotly_chart(fig_stock, use_container_width=True)

    # 2️⃣ Besoin vs Dispo_TIS
    st.subheader("📊 Besoin vs Dispo_TIS")
    fig_besoin = px.line(df_f, x="Semaine", y=["Besoin","Dispo_TIS"], color="Référence", markers=True,
                         title="Besoin client vs Dispo TIS")
    st.plotly_chart(fig_besoin, use_container_width=True)

    # 3️⃣ Alertes Stock
    st.subheader("⚠️ Alertes Stock")
    df_alert = df_f[df_f["Stock_restant_IDL"] < df_f["SS"]].copy()
    fig_alert = px.line(df_alert, x="Semaine", y="Stock_restant_IDL", color="Référence", markers=True,
                        title="Alertes : Stock inférieur au SS")
    st.plotly_chart(fig_alert, use_container_width=True)

    st.success("🎯 Dashboard prêt : identifiez rapidement où le planning est impacté et quelles ruptures nécessitent action.")

# =========================
# MAIN LOGIC
# =========================
if not st.session_state.logged_in:
    login()
else:
    run_dashboard()
