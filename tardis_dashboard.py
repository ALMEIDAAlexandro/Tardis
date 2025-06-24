import streamlit as st
import pandas as pd
import joblib
from collections import defaultdict
from datetime import datetime

# --- Configuration de la page ---
st.set_page_config(
    page_title="TARDIS - Dashboard SNCF",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Chargement des données et modèle ---
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_dataset.csv", sep=";")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
        df["hour"] = df["date"].dt.hour
    return df


@st.cache_resource
def load_model():
    return joblib.load("tardis_best_model.pkl")


df = load_data()
model = load_model()

# --- Sidebar avec navigation et feedback ---
st.sidebar.title("Navigation")
pages = [
    "Statistiques des retards",
    "Gares avec plus de retards",
    "Gares les plus fiables",
    "Simulateur de retard",
    "Conseils voyageurs",
]
page = st.sidebar.radio("", pages)

# Widget de feedback dans la sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Votre avis nous intéresse")
rating = st.sidebar.slider("Notez ce dashboard (⭐)", 1, 5, 3)
feedback = st.sidebar.text_input("Commentaire (optionnel)")
if st.sidebar.button("Envoyer mon avis"):
    st.sidebar.success("Merci pour votre feedback!")
    # Ici vous pourriez enregistrer le feedback dans un fichier ou base de données


# --- Fonctions utilitaires ---
def group_delay_reasons_by_date(df):
    date_reasons = defaultdict(list)
    for _, row in df.dropna(subset=["arrival_delay_comments"]).iterrows():
        date_str = (
            row["date"].strftime("%Y-%m-%d")
            if "date" in df.columns
            else "Date inconnue"
        )
        reasons = [
            r.strip()
            for r in str(row["arrival_delay_comments"]).split("\n")
            if r.strip()
        ]
        for reason in reasons:
            if reason not in date_reasons[date_str]:
                date_reasons[date_str].append(reason)
    return date_reasons


def display_delay_metrics(avg_delay, delay_std, punctuality_rate):
    st.markdown(
        """
    <style>
        .metric-box {
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            background-color: #f0f2f6;
            margin: 10px 0;
        }
        .metric-title {
            color: #6c757d;
            font-size: 1rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #000000;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="metric-title">Retard moyen</div>
            <div class="metric-value">{avg_delay:.1f} min</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="metric-title">Variabilité des retards</div>
            <div class="metric-value">{delay_std:.1f} min</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="metric-title">Ponctualité (<5min)</div>
            <div class="metric-value">{punctuality_rate:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def calculate_reliability_score(delay):
    if delay <= 2:
        return 5
    elif delay <= 5:
        return 4
    elif delay <= 10:
        return 3
    elif delay <= 15:
        return 2
    else:
        return 1


# --- Page: Statistiques des retards ---
if page == "Statistiques des retards":
    st.title("📊 Statistiques des retards par trajet")
    st.info(
        "💡 Conseil: Les retards sont généralement plus importants aux heures de pointe (7h-9h et 17h-19h)"
    )

    # Filtres
    col1, col2 = st.columns(2)

    # Liste complète de toutes les gares
    all_departures = ["Toutes"] + sorted(df["departure_station"].dropna().unique())
    all_arrivals = ["Toutes"] + sorted(df["arrival_station"].dropna().unique())

    # Initialisation des sélections
    if "selected_depart" not in st.session_state:
        st.session_state.selected_depart = "Toutes"
    if "selected_arrivee" not in st.session_state:
        st.session_state.selected_arrivee = "Toutes"

    # Premier selectbox pour la gare de départ
    selected_depart = col1.selectbox(
        "Gare de départ", all_departures, key="depart_select"
    )

    # Filtrer les gares d'arrivée possibles en fonction du départ sélectionné
    if selected_depart != "Toutes":
        possible_arrivals = ["Toutes"] + sorted(
            df[df["departure_station"] == selected_depart]["arrival_station"]
            .dropna()
            .unique()
        )
    else:
        possible_arrivals = all_arrivals

    # Deuxième selectbox pour la gare d'arrivée (filtrée)
    selected_arrivee = col2.selectbox(
        "Gare d'arrivée", possible_arrivals, key="arrivee_select"
    )

    # Si l'arrivée change, on filtre aussi les départs possibles
    if selected_arrivee != "Toutes":
        possible_departures = ["Toutes"] + sorted(
            df[df["arrival_station"] == selected_arrivee]["departure_station"]
            .dropna()
            .unique()
        )
        # On met à jour le selectbox des départs si nécessaire
        if selected_depart != "Toutes" and selected_depart not in possible_departures:
            selected_depart = "Toutes"
            st.session_state.selected_depart = "Toutes"
            st.experimental_rerun()
    else:
        possible_departures = all_departures

    # Application des filtres
    df_filtered = df.copy()
    if selected_depart != "Toutes":
        df_filtered = df_filtered[df_filtered["departure_station"] == selected_depart]
    if selected_arrivee != "Toutes":
        df_filtered = df_filtered[df_filtered["arrival_station"] == selected_arrivee]

    # KPI
    if len(df_filtered) > 0:
        avg_delay = df_filtered["avg_arr_delay"].mean()
        delay_std = df_filtered["avg_arr_delay"].std()
        punctuality_rate = (df_filtered["avg_arr_delay"] <= 5).mean() * 100

        display_delay_metrics(avg_delay, delay_std, punctuality_rate)

        # Météo des retards
        delay_status = (
            "bonne" if avg_delay < 5 else "moyenne" if avg_delay < 15 else "mauvaise"
        )
        st.subheader(f"Situation actuelle: {delay_status.capitalize()}")
        if delay_status == "mauvaise":
            st.warning("Privilégiez les transports alternatifs aujourd'hui")

        # Top 3 des raisons de retard
        if "arrival_delay_comments" in df_filtered.columns:
            reasons = df_filtered["arrival_delay_comments"].value_counts().head(3)
            if len(reasons) > 0:
                st.subheader("🔍 Top 3 des causes de retard")
                for reason, count in reasons.items():
                    st.write(f"- {reason} ({count} occurrences)")
    else:
        st.warning("Aucune donnée disponible pour cette sélection de gares.")

# --- Page: Gares avec plus de retards ---
elif page == "Gares avec plus de retards":
    st.title("⚠️ Gares avec les plus gros retards")

    # Filtre par année si disponible
    year_filter = "Toutes"
    if "year" in df.columns:
        years = ["Toutes"] + sorted(df["year"].unique())
        year_filter = st.selectbox("Filtrer par année", years)

    # Calcul des classements
    df_ranking = df.copy()
    if year_filter != "Toutes":
        df_ranking = df_ranking[df_ranking["year"] == year_filter]

    top_departure = (
        df_ranking.groupby("departure_station")["avg_dep_delay"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(
            columns={"departure_station": "Gare", "avg_dep_delay": "Retard moyen (min)"}
        )
    )

    top_arrival = (
        df_ranking.groupby("arrival_station")["avg_arr_delay"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(
            columns={"arrival_station": "Gare", "avg_arr_delay": "Retard moyen (min)"}
        )
    )

    # Style CSS amélioré
    st.markdown(
        """
    <style>
        .card {
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            transition: 0.3s;
            display: flex;
            flex-direction: column;
        }
        .card:hover {
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
        }
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .gold {
            background-color: #FFF9C4;
            border-left: 5px solid #FFD700;
        }
        .silver {
            background-color: #F5F5F5;
            border-left: 5px solid #C0C0C0;
        }
        .bronze {
            background-color: #FFECB3;
            border-left: 5px solid #CD7F32;
        }
        .other {
            background-color: #E3F2FD;
            border-left: 5px solid #64B5F6;
        }
        .rank-1 {
            font-size: 2.5rem;
            font-weight: 900;
            color: #FFD700;
            margin-right: 15px;
        }
        .rank-2 {
            font-size: 2.2rem;
            font-weight: 700;
            color: #C0C0C0;
            margin-right: 15px;
        }
        .rank-3 {
            font-size: 2rem;
            font-weight: 600;
            color: #CD7F32;
            margin-right: 15px;
        }
        .rank-4 {
            font-size: 1.8rem;
            font-weight: 500;
            color: #000000;
            margin-right: 15px;
        }
        .station-name {
            font-size: 1.5rem;
            font-weight: bold;
            color: #000000;
        }
        .delay-value {
            font-size: 1.2rem;
            color: #333;
            margin-top: auto;
            align-self: flex-start;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Affichage des classements
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 départs")
        for i, row in top_departure.iterrows():
            rank_class = f"rank-{i + 1}" if i < 4 else "rank-4"
            card_class = (
                "gold"
                if i == 0
                else "silver"
                if i == 1
                else "bronze"
                if i == 2
                else "other"
            )

            st.markdown(
                f"""
                <div class="card {card_class}">
                    <div class="card-header">
                        <div class="{rank_class}">{i + 1}</div>
                        <div class="station-name">{row["Gare"]}</div>
                    </div>
                    <div class="delay-value">Retard moyen: {row["Retard moyen (min)"]:.1f} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        st.subheader("Top 10 arrivées")
        for i, row in top_arrival.iterrows():
            rank_class = f"rank-{i + 1}" if i < 4 else "rank-4"
            card_class = (
                "gold"
                if i == 0
                else "silver"
                if i == 1
                else "bronze"
                if i == 2
                else "other"
            )

            st.markdown(
                f"""
                <div class="card {card_class}">
                    <div class="card-header">
                        <div class="{rank_class}">{i + 1}</div>
                        <div class="station-name">{row["Gare"]}</div>
                    </div>
                    <div class="delay-value">Retard moyen: {row["Retard moyen (min)"]:.1f} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# --- Page: Gares les plus fiables ---
elif page == "Gares les plus fiables":
    st.title("⭐ Gares les plus fiables")

    # Filtre par année si disponible
    year_filter = "Toutes"
    if "year" in df.columns:
        years = ["Toutes"] + sorted(df["year"].unique())
        year_filter = st.selectbox("Filtrer par année", years)

    # Calcul de la fiabilité
    df_reliability = df.copy()
    if year_filter != "Toutes":
        df_reliability = df_reliability[df_reliability["year"] == year_filter]

    # Calcul pour les gares de départ
    departure_reliability = (
        df_reliability.groupby("departure_station")["avg_dep_delay"]
        .mean()
        .reset_index()
        .rename(
            columns={"departure_station": "Gare", "avg_dep_delay": "Retard moyen (min)"}
        )
    )
    departure_reliability["Fiabilité"] = departure_reliability[
        "Retard moyen (min)"
    ].apply(calculate_reliability_score)

    # Calcul pour les gares d'arrivée
    arrival_reliability = (
        df_reliability.groupby("arrival_station")["avg_arr_delay"]
        .mean()
        .reset_index()
        .rename(
            columns={"arrival_station": "Gare", "avg_arr_delay": "Retard moyen (min)"}
        )
    )
    arrival_reliability["Fiabilité"] = arrival_reliability["Retard moyen (min)"].apply(
        calculate_reliability_score
    )

    # Top 10 des gares les plus fiables (départ)
    top_reliable_departure = departure_reliability.sort_values(
        "Fiabilité", ascending=False
    ).head(10)

    # Top 10 des gares les plus fiables (arrivée)
    top_reliable_arrival = arrival_reliability.sort_values(
        "Fiabilité", ascending=False
    ).head(10)

    # Style CSS pour les cartes de fiabilité
    st.markdown(
        """
    <style>
        .reliability-card {
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
            background-color: #f8f9fa;
            border-left: 5px solid #4CAF50;
            display: flex;
            flex-direction: column;
            min-height: 140px;
        }
        .reliability-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .reliability-stars {
            font-size: 2rem;
            color: #FFD700;
            margin-right: 20px;
        }
        .reliability-station {
            font-weight: bold;
            font-size: 2rem;
            color: #2c3e50;
            line-height: 1.2;
        }
        .reliability-delay {
            font-size: 1.4rem;
            color: #7f8c8d;
            margin-top: auto;
            align-self: flex-start;
        }
        .reliability-columns {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        @media (max-width: 768px) {
            .reliability-columns {
                grid-template-columns: 1fr;
            }
            .reliability-station {
                font-size: 1.8rem;
            }
            .reliability-stars {
                font-size: 1.8rem;
            }
            .reliability-delay {
                font-size: 1.2rem;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Affichage des résultats
    st.subheader("🚂 Top 10 des gares de départ les plus fiables")

    st.markdown('<div class="reliability-columns">', unsafe_allow_html=True)
    for i, row in top_reliable_departure.iterrows():
        stars = "⭐" * row["Fiabilité"]
        st.markdown(
            f"""
        <div class="reliability-card">
            <div class="reliability-header">
                <div class="reliability-stars">{stars}</div>
                <div class="reliability-station">{row["Gare"]}</div>
            </div>
            <div class="reliability-delay">Retard moyen: {row["Retard moyen (min)"]:.1f} min</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("🚉 Top 10 des gares d'arrivée les plus fiables")

    st.markdown('<div class="reliability-columns">', unsafe_allow_html=True)
    for i, row in top_reliable_arrival.iterrows():
        stars = "⭐" * row["Fiabilité"]
        st.markdown(
            f"""
        <div class="reliability-card">
            <div class="reliability-header">
                <div class="reliability-stars">{stars}</div>
                <div class="reliability-station">{row["Gare"]}</div>
            </div>
            <div class="reliability-delay">Retard moyen: {row["Retard moyen (min)"]:.1f} min</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Légende
    st.markdown("""
    **Légende:**
    - ⭐⭐⭐⭐⭐ : Exceptionnel (retard moyen ≤ 2 min)
    - ⭐⭐⭐⭐☆ : Très fiable (retard moyen ≤ 5 min)
    - ⭐⭐⭐☆☆ : Fiable (retard moyen ≤ 10 min)
    - ⭐⭐☆☆☆ : Moyen (retard moyen ≤ 15 min)
    - ⭐☆☆☆☆ : Peu fiable (retard moyen > 15 min)
    """)
elif page == "Simulateur de retard":
    st.title("🔮 Simulateur de retard à l'arrivée")

    with st.form("prediction_form"):
        col1, col2 = st.columns(2)

        # Paramètres simplifiés
        departure_station = col1.selectbox(
            "Gare de départ *", sorted(df["departure_station"].unique())
        )

        arrival_station = col2.selectbox(
            "Gare d'arrivée *", sorted(df["arrival_station"].unique())
        )

        month = col1.selectbox(
            "Mois *",
            range(1, 13),
            format_func=lambda x: datetime(2023, x, 1).strftime("%B"),
        )

        avg_dep_delay = col2.number_input(
            "Retard initial au départ (minutes) *",
            min_value=0.0,
            max_value=120.0,
            value=5.0,
            step=1.0,
        )

        submitted = st.form_submit_button("Estimer le retard")

        if submitted:
            # Construction de la route et calcul des features dérivées
            route = f"{departure_station} ➜ {arrival_station}"
            quarter = (month - 1) // 3 + 1
            major_stations = df["arrival_station"].value_counts().head(10).index
            is_major_arrival = 1 if arrival_station in major_stations else 0

            # Filtrage historique pour la ligne sélectionnée
            df_route = df[
                (df["departure_station"] == departure_station)
                & (df["arrival_station"] == arrival_station)
                & (df["month"] == month)
            ]

            # Calcul de delay_ratio avec moyenne agrégée (float)
            if not df_route.empty:
                delay_ratio = (df_route["avg_arr_delay"] / (df_route["avg_dep_delay"] + 0.1)).mean()
            else:
                delay_ratio = 0.2  # valeur par défaut

            # Préparation des features pour le modèle
            X_input = pd.DataFrame(
                {
                    "route": [route],
                    "avg_dep_delay": [avg_dep_delay],
                    "total_delay_points": [0],
                    "trains_delayed_15min": [0],
                    "trains_delayed_30min": [0],
                    "trains_delayed_60min": [0],
                    "month": [month],
                    "quarter": [quarter],
                    "is_major_arrival": [is_major_arrival],
                    "pct_delay_external": [0.1],
                    "delay_ratio": [delay_ratio],
                    "cancelled_trains": [0],
                }
            )

            try:
                prediction = max(0, model.predict(X_input)[0])

                # Affichage du résultat
                delay_level = (
                    "faible"
                    if prediction < 5
                    else "modéré"
                    if prediction < 15
                    else "important"
                )
                delay_color = (
                    "#28a745"
                    if prediction < 5
                    else "#ffc107"
                    if prediction < 15
                    else "#dc3545"
                )

                st.markdown(
                    f"""
                    <div style='border: 2px solid {delay_color}; border-radius: 10px; padding: 20px; margin: 20px 0;'>
                        <h3 style='color: {delay_color}; text-align: center;'>Retard estimé: {prediction:.1f} minutes</h3>
                        <p style='text-align: center;'>Niveau de retard: <strong>{delay_level}</strong></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Conseils personnalisés
                st.subheader("Conseils pour votre voyage")
                if prediction >= 15:
                    st.error("**Retard important prévu**")
                    st.markdown("""
                        - Prévoyez au moins 30 minutes de marge supplémentaire
                        - Évitez les rendez-vous importants juste après votre arrivée
                        - Vérifiez les alternatives de transport avant de partir
                    """)
                elif prediction >= 5:
                    st.warning("**Retard modéré prévu**")
                    st.markdown("""
                        - Prévoyez 15-20 minutes de marge
                        - Surveillez les informations en temps réel pendant votre voyage
                        - Identifiez les correspondances alternatives en gare
                    """)
                else:
                    st.success("**Retard minime prévu**")
                    st.markdown("""
                        - Votre trajet devrait se dérouler normalement
                        - Une marge de 5-10 minutes est suffisante
                        - Bon voyage !
                    """)

            except Exception as e:
                st.error(f"Erreur lors de la prédiction : {str(e)}")
                st.info(
                    "Assurez-vous que toutes les informations sont correctement renseignées"
                )


# --- Page: Conseils voyageurs ---
elif page == "Conseils voyageurs":
    st.title("💡 Conseils pour éviter les retards")

    st.header("📌 Choisir le bon créneau")
    st.write("""
    - **Meilleurs horaires** : Privilégiez les trains avant 7h ou entre 10h et 16h
    - **À éviter** : Les heures de pointe (8h-9h et 17h-19h) sont plus sujettes aux retards
    """)

    st.header("🚄 Choisir le bon trajet")
    st.write("""
    - **Trajets directs** : Moins de risques de retard que les trajets avec correspondance
    - **Gares majeures** : Les grandes gares ont souvent moins de retards que les petites
    """)

    st.header("⏱ Gérer les retards")
    st.write("""
    - **Marge de sécurité** : Prévoyez toujours 15-30 minutes de marge pour vos rendez-vous
    - **Applications utiles** : Téléchargez l'application SNCF pour les alertes en temps réel
    - **Droits voyageurs** : En cas de retard important, vous pouvez être éligible à une compensation
    """)

    st.header("🚆 Alternatives")
    st.write("""
    - **Transports alternatifs** : Bus, covoiturage ou TER peuvent être plus fiables selon les trajets
    - **Horaires flexibles** : Si possible, choisissez des billets modifiables sans frais
    """)
