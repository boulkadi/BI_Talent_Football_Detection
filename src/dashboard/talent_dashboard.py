"""

🏆 Football Talent Detection Dashboard

=====================================

Dashboard interactif pour la détection de talents football.

Se connecte directement à la base de données PostgreSQL pour des données en temps réel.

"""



import streamlit as st

import pandas as pd

import plotly.express as px

import plotly.graph_objects as go

from plotly.subplots import make_subplots

import sys

import os



# Ajouter le chemin parent pour importer le DatabaseManager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager



# =========================================================

# Configuration de la page

# =========================================================

st.set_page_config(

    page_title="🏆 Football Talent Detection",

    page_icon="⚽",

    layout="wide",

    initial_sidebar_state="expanded"

)



# =========================================================

# Connexion à la base de données

# =========================================================

@st.cache_resource

def get_db_connection():

    """Connexion persistante à la base de données."""

    return DatabaseManager()



@st.cache_data(ttl=60)  # Cache de 60 secondes pour rafraîchissement automatique

def load_data(query: str) -> pd.DataFrame:

    """Charge les données depuis PostgreSQL."""

    db = get_db_connection()

    with db.engine.connect() as conn:

        return pd.read_sql(query, conn)



# =========================================================

# Requêtes SQL

# =========================================================



QUERY_PLAYERS = """

SELECT

    -- =========================

    -- CONTEXTE

    -- =========================

    l.league,

    s.season_id,

    t.team,



    -- =========================

    -- PROFIL JOUEUR

    -- =========================

    p.player_id,

    p.player,

    p.nationality,

    p.position_standard,

    p.position_current,

    p.detailed_positions_current,

    p.position_description,

    p.preferred_foot,

    f.player_age_at_season,



    -- =========================

    -- TEMPS DE JEU (IMPORTANT)

    -- =========================

    f.matches,

    f.minutes,

    (f.minutes / 90.0) AS matches_equivalent_90,



    -- =========================

    -- PRODUCTION OFFENSIVE

    -- =========================

    f.goals,

    f.assists,

    f.np_goals,

    f.xg,

    f.xa,

    f.np_xg,



    -- =========================

    -- METRICS PER 90 (CORE SCOUTING)

    -- =========================

    f.goals_per_90,

    f.xg_per_90,

    f.np_goals_per_90,

    f.np_xg_per_90,

    f.assists_per_90,

    f.xa_per_90,

    f.shots_per_90,

    f.key_passes_per_90,



    -- =========================

    -- IMPLICATION DANS LE JEU

    -- =========================

    f.xg_chain,

    f.xg_buildup,

    f.involvement_per_90,

    f.involvement_index,



    -- =========================

    -- EFFICIENCY (TRÈS IMPORTANT)

    -- =========================

    f.finishing_efficiency,

    f.np_finishing_efficiency,

    f.playmaking_efficiency,

    f.shot_conversion,



    -- =========================

    -- CONTRIBUTION GLOBALE

    -- =========================

    f.direct_contribution,

    f.expected_contribution,

    f.offensive_volume,



    -- =========================

    -- VALEUR & MARCHÉ

    -- =========================

    f.market_value_current,

    f.value_per_goal,

    f.value_per_xg,

    f.value_per_contribution,

    f.contract_end_date_current,



    -- =========================

    -- INDICATEURS DÉRIVÉS (SCOUTING)

    -- =========================

    

    -- Surperformance (finition)

    (f.goals - f.xg) AS finishing_overperformance,



    -- Création vs finition

    (f.xa + f.xg) AS total_expected_output,



    -- Volume offensif réel

    (f.goals + f.assists) AS real_output,



    -- Ratio qualité/prix

    CASE 

        WHEN f.market_value_current > 0 

        THEN (f.expected_contribution / f.market_value_current)

        ELSE NULL

    END AS value_efficiency_score



FROM staging.fact_performance f



-- =========================

-- JOINTURES

-- =========================

JOIN staging.dim_player p 

    ON f.player_id = p.player_id



JOIN staging.dim_team t 

    ON f.team_id = t.team_id



JOIN staging.dim_league l 

    ON f.league_id = l.league_id



JOIN staging.dim_season s 

    ON f.season_id = s.season_id



-- =========================

-- FILTRES (OPTIONNELS MAIS RECOMMANDÉS)

-- =========================



"""

# =========================================================

# Fonctions utilitaires

# =========================================================

def format_currency(value):

    """Formate une valeur en euros."""

    if pd.isna(value) or value is None:

        return "N/A"

    if value >= 1_000_000:

        return f"€{value/1_000_000:.1f}M"

    elif value >= 1_000:

        return f"€{value/1_000:.0f}K"

    return f"€{value:.0f}"



def get_talent_emoji(category):

    """Retourne un emoji selon la catégorie de talent."""

    emojis = {

        'Top Prospect': '🌟',

        'Elite Performer': '🏆',

        'Standard': '📊',

        'Underperforming': '📉'

    }

    return emojis.get(category, '⚽')



# =========================================================

# Interface principale

# =========================================================

def main():

    # Titre principal

    st.title("🏆 Football Talent Detection Dashboard")

    st.markdown("*Analyse en temps réel connectée à la base de données PostgreSQL*")

    

    # Bouton de rafraîchissement

    col_refresh, col_info = st.columns([1, 5])

    with col_refresh:

        if st.button("🔄 Rafraîchir les données"):

            st.cache_data.clear()

            st.rerun()

    with col_info:

        st.caption("Les données sont automatiquement mises à jour toutes les 60 secondes")

    

    st.divider()

    

    # Chargement des données

    try:

        df_players = load_data(QUERY_PLAYERS)

        # Filtrer pour la saison en cours 2025

        df_players_new_season = df_players[df_players['season_id'] == 2025]



    except Exception as e:

        st.error(f"❌ Erreur de connexion à la base de données: {e}")

        st.info("Assurez-vous que le conteneur PostgreSQL est en cours d'exécution.")

        return

    

    # =========================================================

    # SIDEBAR - Filtres interactifs

    # =========================================================

    st.sidebar.header("🎛️ Filtres")

    

    # Filtre par ligue

    leagues = ['Toutes'] + sorted(df_players_new_season['league'].dropna().unique().tolist())

    selected_league = st.sidebar.selectbox("📍 Ligue", leagues)

    

    # Filtre par team

    teams = ['Toutes'] + sorted(df_players_new_season['team'].dropna().unique().tolist())

    selected_team = st.sidebar.selectbox("📍 Team", teams)

    

    # Filtre par âge

    age_range = st.sidebar.slider(

        "👤 Tranche d'âge",

        min_value=16,

        max_value=40,

        value=(16, 28),

        help="Filtrer les joueurs par âge"

    )

    

    # Filtre par minutes jouées minimum

    min_minutes = st.sidebar.slider(

        "⏱️ Minutes jouées (min)",

        min_value=0,

        max_value=3000,

        value=900,

        step=100

    )

    

    # Appliquer les filtres

    df_filtered = df_players_new_season.copy()

    

    # Filtrer seulement les valeurs None critiques (garder les 0 pour ne pas perdre de données)

    df_filtered = df_filtered[

        (df_filtered['player'].notna()) &

        (df_filtered['position_standard'].notna())

    ]

    

    if selected_league != 'Toutes':

        df_filtered = df_filtered[df_filtered['league'] == selected_league]

    if selected_team != 'Toutes':

        df_filtered = df_filtered[df_filtered['team'] == selected_team]

    df_filtered = df_filtered[

        (df_filtered['player_age_at_season'] >= age_range[0]) & 

        (df_filtered['player_age_at_season'] <= age_range[1]) &

        (df_filtered['minutes'] >= min_minutes)

    ]

    

    # =========================================================

    # KPIs - 5 indicateurs clés

    # =========================================================

    st.header("📊 Indicateurs Clés de Performance (KPIs)")

    

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    

    with kpi1:

        total_players = len(df_filtered)

        st.metric(

            label="👥 Joueurs analysés",

            value=f"{total_players:,}",

            delta=f"sur {len(df_players_new_season):,} total"

        )

    

    with kpi2:

        players_U23 = len(df_filtered[df_filtered['player_age_at_season'] <= 23])

        st.metric(

            label="🌟 Players U23",

            value=players_U23,

            delta=f"{(players_U23/max(total_players,1)*100):.1f}%"

        )

    

    with kpi3:

        # Calculer les elite performers basé sur les métriques disponibles

        elite_performers = len(df_filtered[

            (df_filtered['goals_per_90'] > df_filtered['goals_per_90'].quantile(0.75)) &

            (df_filtered['finishing_efficiency'] > 1.0)

        ]) if len(df_filtered) > 0 else 0

        st.metric(

            label="🏆 Elite Performers",

            value=elite_performers,

            delta=f"{(elite_performers/max(total_players,1)*100):.1f}%"

        )

    

    with kpi4:

        avg_contribution = df_filtered['direct_contribution'].mean() if len(df_filtered) > 0 else 0

        st.metric(

            label="🎯 contribution moy.",

            value=f"{avg_contribution:.2f}",

            help="Moyenne des contributions directes (goals + assists) par joueur"

        )

    

    with kpi5:

        avg_involvement_index = df_filtered['involvement_index'].mean() if len(df_filtered) > 0 else 0

        st.metric(

            label="📈 Création de jeu moy.",

            value=f"{avg_involvement_index:.2f}",

            help="Moyenne de l'indice d'implication dans le jeu (xg_chain + xg_buildup) par joueur"

        )

    

    st.divider()

    

    #Supprimer tous lignes contenat une valeur égale 0 pour player_age_at_season et market_value_current
    df_filtered = df_filtered[(df_filtered['player_age_at_season'] != 0) & (df_filtered['market_value_current'] != 0)]
    

    #Supprimer toutes les lignes contenant une valeur None

    df_filtered = df_filtered.dropna()

    # =========================================================

    # Apercu du des données des joueurs

    # =========================================================

    st.header("👀 Aperçu des Données Joueurs")

    # Afficher un aperçu des données filtrées qui ne contient aucun valeur nulle ou None ordonés par market_value_current (important pour le scouting) et contribution_margin (important pour la détection de talents)

    df_apercu = df_filtered.copy()

    df_apercu = df_apercu.dropna(subset=[

    'player', 'league', 'team', 'position_standard',

    'player_age_at_season', 'goals', 'assists',

    'xg_buildup', 'market_value_current'

])

    df_apercu = df_apercu.sort_values(by='market_value_current', ascending=False)

    #appliquer format_currency à market_value_current pour l'affichage

    df_apercu['market_value_current'] = df_apercu['market_value_current'].apply(format_currency)

    # conserver les 30 premiers joueurs pour l'affichage
    df_apercu = df_apercu.head(30)
    # changer l'ordre du player_id et market_value_current entre eux
    df_apercu = df_apercu[['player_id', 'market_value_current'] + [col for col in df_apercu.columns if col != 'player_id' and col != 'market_value_current']]



    if len(df_filtered) > 0:

        st.dataframe(

            df_apercu,

            hide_index=True,

            use_container_width=True

        )



    st.divider()

    # =========================================================

    #Aperçu des meilleurs des meilleurs talents d'attaquants

    # =========================================================

    st.header("🌟 Aperçu des Meilleurs Talents d'Attaquants")

    df_forwards = df_filtered[

    df_filtered['position_standard'] == 'Forward'].copy()

    # Nettoyage minimal

    df_forwards = df_forwards.dropna(subset=[

        'goals', 'xg', 

        'involvement_index', 'market_value_current'

    ])

    df_top_forwards = df_forwards.copy()



    # Score simple de talent (pondération)

    df_top_forwards['attack_talent_score'] = (

        df_top_forwards['goals_per_90'] * 0.4 +

        df_top_forwards['xg_per_90'] * 0.3 +

        df_top_forwards['involvement_per_90'] * 0.1+

        df_top_forwards['shots_per_90'] * 0.2

    )



    # Trier

    df_top_forwards = df_top_forwards.sort_values(

        by='attack_talent_score',

        ascending=False

    )


    df_undervalued_forwards = df_top_forwards[

        df_top_forwards['market_value_current'] > 0

    ]



    # 1. Calculer le seuil du top 25% (0.75 quantile)
    threshold_top_25 = df_undervalued_forwards['attack_talent_score'].quantile(0.90)

    # 2. Filtrer les joueurs supérieurs à ce seuil
    df_undervalued_forwards = df_undervalued_forwards[
        df_undervalued_forwards['attack_talent_score'] > threshold_top_25
    ]

    # Trier (market value la plus petite en premier)

    df_undervalued_forwards = df_undervalued_forwards.sort_values(

        by='market_value_current',

        ascending=True

    )



    tab1, tab2 = st.tabs([

    "🌟 Top Talents Attaquants",

    "💎 Attaquants Sous-évalués"

    ])

    with tab1:

        st.subheader("🌟 Meilleurs Attaquants (Talent)")



        df_display = df_top_forwards.head(40).copy()

        df_display['market_value_current'] = df_display['market_value_current'].apply(format_currency)



        st.dataframe(

            df_display[[

                'player', 'team', 'league','market_value_current',

                'player_age_at_season','detailed_positions_current','matches','goals','assists',
                'attack_talent_score','contract_end_date_current',

                'shots_per_90', 

                'goals_per_90','xg', 'xg_per_90','finishing_efficiency','shot_conversion',
                'value_per_goal','value_per_xg',

                'involvement_per_90',



            ]],

            hide_index=True,

            use_container_width=True

        )

        col1, col2 = st.columns(2)

        # =========================
        # 📈 Evolution du Talent Score
        # =========================
        with col1:
            top5_players = df_top_forwards.head(5)['player'].unique()

            df_evolution = df_players[
                (df_players['player'].isin(top5_players)) &
                (df_players['position_standard'] == 'Forward')
            ].copy()

            df_evolution['attack_talent_score'] = (
                df_evolution['goals_per_90'] * 0.4 +
                df_evolution['xg_per_90'] * 0.3 +
                df_evolution['involvement_per_90'] * 0.1 +
                df_evolution['shots_per_90'] * 0.2
            )

            df_evolution = df_evolution.sort_values('season_id')

            # 2. Créer la colonne de texte APRÈS le tri
            df_evolution['season_display'] = (
                df_evolution['season_id'].astype(str) + 
                '/' + 
                (df_evolution['season_id'] + 1).astype(str)
            )

            # 3. Créer le graphique (Plotly suivra l'ordre des lignes du DF trié)
            fig_evolution = px.line(
                df_evolution,
                x='season_display', 
                y='direct_contribution',
                color='player',
                markers=True,
                title="📈 Évolution de la contribution directe (Buts + Passes D.)",
                # On force Plotly à ne pas retrier les catégories par lui-même
                category_orders={"season_display": df_evolution['season_display'].tolist()}
            )

            fig_evolution.add_annotation(
            x=df_evolution['season_display'].max(), # Se place sur la dernière saison
            y=df_evolution['direct_contribution'].max(),
            text="⚠️ Saison 2025/2026 en cours",
            showarrow=True,
            arrowhead=1,
            ax=-30,
            ay=-30,
            font=dict(color="orange", size=11)
            )

            st.plotly_chart(fig_evolution, use_container_width=True)

        # =========================
        # 🕸️ Radar Chart
        # =========================
        with col2:
            metrics = [
                'goals_per_90',
                'xg_per_90',
                'shots_per_90',
                'key_passes_per_90',
                'involvement_per_90'
            ]

            df_radar = df_top_forwards.head(5).copy()

            # 🔥 Normalisation (important)
            df_radar[metrics] = df_radar[metrics] / df_radar[metrics].max()

            fig_radar = go.Figure()

            for _, row in df_radar.iterrows():
                values = [row[m] for m in metrics]
                values += [values[0]]

                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metrics + [metrics[0]],
                    fill='toself',
                    name=row['player']
                ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title="🕸️ Profil Radar Top 5 Attaquants"
            )

            st.plotly_chart(fig_radar, use_container_width=True)
        

    with tab2:

        st.subheader("💎 Attaquants Sous-évalués")



        df_display = df_undervalued_forwards.head(40).copy()

        df_display['market_value_current'] = df_display['market_value_current'].apply(format_currency)



        st.dataframe(

            df_display[[

                'player', 'team', 'league','market_value_current',

                'player_age_at_season','detailed_positions_current','matches','goals','assists',
                'attack_talent_score','contract_end_date_current',

                'shots_per_90', 

                'goals_per_90','xg', 'xg_per_90','finishing_efficiency','shot_conversion',
                'value_per_goal','value_per_xg',

                'involvement_per_90',



            ]],

            hide_index=True,

            use_container_width=True)
        
        col1, col2 = st.columns(2)

        # =========================
        # 📈 Evolution (Top 5 undervalued)
        # =========================
        with col1:
            top5_players = df_undervalued_forwards.head(5)['player'].unique()

            df_evolution = df_players[
                (df_players['player'].isin(top5_players)) &
                (df_players['position_standard'] == 'Forward')
            ].copy()

            df_evolution['attack_talent_score'] = (
                df_evolution['goals_per_90'] * 0.4 +
                df_evolution['xg_per_90'] * 0.3 +
                df_evolution['involvement_per_90'] * 0.1 +
                df_evolution['shots_per_90'] * 0.2
            )

            df_evolution = df_evolution.sort_values('season_id')

            df_evolution['season_display'] = (
                df_evolution['season_id'].astype(str) + 
                '/' + 
                (df_evolution['season_id'] + 1).astype(str)
            )

            fig_evolution = px.line(
                df_evolution,
                x='season_display', 
                y='direct_contribution',
                color='player',
                markers=True,
                title="📈 Évolution Contribution (Sous-évalués)",
                category_orders={"season_display": df_evolution['season_display'].tolist()}
            )

            fig_evolution.add_annotation(
                x=df_evolution['season_display'].max(),
                y=df_evolution['direct_contribution'].max(),
                text="⚠️ Saison en cours",
                showarrow=True,
                arrowhead=1,
                ax=-30,
                ay=-30,
                font=dict(color="orange", size=11)
            )

            st.plotly_chart(fig_evolution, use_container_width=True)

        # =========================
        # 🕸️ Radar Chart (Top 5 undervalued)
        # =========================
        with col2:
            metrics = [
                'goals_per_90',
                'xg_per_90',
                'shots_per_90',
                'key_passes_per_90',
                'involvement_per_90'
            ]

            df_radar = df_undervalued_forwards.head(5).copy()

            # 🔥 Normalisation
            df_radar[metrics] = df_radar[metrics] / df_radar[metrics].max()

            fig_radar = go.Figure()

            for _, row in df_radar.iterrows():
                values = [row[m] for m in metrics]
                values += [values[0]]

                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metrics + [metrics[0]],
                    fill='toself',
                    name=row['player']
                ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title="🕸️ Profil Radar Attaquants Sous-évalués"
            )

            st.plotly_chart(fig_radar, use_container_width=True)


if __name__ == "__main__":
    main()

