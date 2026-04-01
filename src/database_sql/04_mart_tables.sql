-- =========================================================
-- MART LAYER  –  Schéma en étoile analytique
-- Objectif : couche optimisée pour le scouting et la BI.
--
--                    dim_player
--                         |
--                         |
--   dim_team ──── fact_performance ──── dim_season
--                         |
--                         |
--                    dim_league
--
-- Conventions :
--   • Clés de substitution (surrogate keys) BIGSERIAL
--   • Clés naturelles préservées pour les lookups ETL
--   • SCD Type 1 (écrasement) sauf indication contraire
--   • Indexes sur FK et colonnes de filtrage fréquent
-- =========================================================

-- =========================================================
-- MART LAYER  – Schéma en étoile analytique
-- Objectif : couche optimisée pour le scouting et la BI.
-- =========================================================

-- =========================================================
-- DIMENSION – Ligues
-- =========================================================
CREATE TABLE IF NOT EXISTS mart.dim_league (
    league_id       TEXT       PRIMARY KEY,
    league          TEXT            NOT NULL UNIQUE,
    country         TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- =========================================================
-- DIMENSION – Saisons
-- =========================================================
CREATE TABLE IF NOT EXISTS mart.dim_season (
    season_id       TEXT       PRIMARY KEY,
    season_label    TEXT            NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- =========================================================
-- DIMENSION – Équipes
-- =========================================================
CREATE TABLE IF NOT EXISTS mart.dim_team (
    team_id         TEXT       PRIMARY KEY,
    team            TEXT            NOT NULL,
    country         TEXT,
    league_id       TEXT          REFERENCES mart.dim_league(league_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dim_team_name_league UNIQUE(team, league_id)
);

CREATE INDEX IF NOT EXISTS idx_dim_team_league_id ON mart.dim_team(league_id);

-- =========================================================
-- DIMENSION – Joueurs
-- =========================================================
CREATE TABLE IF NOT EXISTS mart.dim_player (
    player_id           TEXT       PRIMARY KEY,
    player              TEXT            NOT NULL,
    name_sofascore      TEXT,
    nationality         TEXT,
    birth_year          INTEGER,
    height              SMALLINT        CHECK (height BETWEEN 140 AND 230),
    weight              SMALLINT        CHECK (weight BETWEEN 40 AND 150),
    preferred_foot      TEXT            
    position_standard   TEXT            CHECK (position_standard IN ('Goalkeeper','Defender','Midfielder','Forward')),
    position_description TEXT,
    detailed_positions  TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dim_player_name UNIQUE(player)
);

CREATE INDEX IF NOT EXISTS idx_dim_player_nationality      ON mart.dim_player(nationality);
CREATE INDEX IF NOT EXISTS idx_dim_player_position         ON mart.dim_player(position_standard);
CREATE INDEX IF NOT EXISTS idx_dim_player_name_sofascore   ON mart.dim_player(name_sofascore);

-- =========================================================
-- TABLE DE FAITS – Performances par saison
-- Grain : 1 ligne = 1 joueur × 1 équipe × 1 saison × 1 ligue
-- =========================================================
CREATE TABLE IF NOT EXISTS mart.fact_performance (
    performance_id          BIGSERIAL   PRIMARY KEY,

    -- Clés dimensions
    player_id               TEXT      NOT NULL REFERENCES mart.dim_player(player_id) ON DELETE CASCADE,
    team_id                 TEXT      NOT NULL REFERENCES mart.dim_team(team_id) ON DELETE CASCADE,
    season_id               TEXT      NOT NULL REFERENCES mart.dim_season(season_id) ON DELETE CASCADE,
    league_id               TEXT      NOT NULL REFERENCES mart.dim_league(league_id) ON DELETE CASCADE,

    -- Statistiques de volume
    matches                 SMALLINT    NOT NULL DEFAULT 0 CHECK(matches >= 0),
    minutes                 INTEGER     NOT NULL DEFAULT 0 CHECK(minutes >= 0),
    goals                   SMALLINT    NOT NULL DEFAULT 0 CHECK(goals >= 0),
    assists                 SMALLINT    NOT NULL DEFAULT 0 CHECK(assists >= 0),
    shots                   SMALLINT    NOT NULL DEFAULT 0 CHECK(shots >= 0),
    key_passes              SMALLINT    NOT NULL DEFAULT 0 CHECK(key_passes >= 0),
    yellow_cards            SMALLINT             DEFAULT 0 CHECK(yellow_cards >= 0),
    red_cards               SMALLINT             DEFAULT 0 CHECK(red_cards >= 0),
    np_goals                SMALLINT             DEFAULT 0 CHECK(np_goals >= 0),

    -- Métriques xG
    xg                      NUMERIC(8,4)   NOT NULL DEFAULT 0,
    xa                      NUMERIC(8,4)   NOT NULL DEFAULT 0,
    xg_chain                NUMERIC(8,4)   DEFAULT 0,
    xg_buildup              NUMERIC(8,4)   DEFAULT 0,
    np_xg                   NUMERIC(8,4)   DEFAULT 0,

    -- KPIs per-90
    goals_per_90            NUMERIC(6,3),
    xg_per_90               NUMERIC(6,3),
    np_goals_per_90         NUMERIC(6,3),
    np_xg_per_90            NUMERIC(6,3),
    assists_per_90          NUMERIC(6,3),
    xa_per_90               NUMERIC(6,3),
    shots_per_90            NUMERIC(6,3),
    key_passes_per_90       NUMERIC(6,3),
    involvement_per_90      NUMERIC(6,3),

    -- KPIs efficacité
    finishing_efficiency    NUMERIC(8,4),
    np_finishing_efficiency NUMERIC(8,4),
    playmaking_efficiency   NUMERIC(8,4),
    shot_conversion         NUMERIC(8,4),

    -- KPIs collectifs
    involvement_index       NUMERIC(10,3),
    direct_contribution     SMALLINT,
    expected_contribution   NUMERIC(8,3),
    offensive_volume        SMALLINT,

    -- Contexte joueur
    player_age_at_season    SMALLINT    CHECK(player_age_at_season BETWEEN 10 AND 60),
    market_value_current    NUMERIC(15,2),
    popularity_score_current INTEGER    CHECK(popularity_score_current >= 0),
    contract_end_date_current DATE,

    -- Tracking
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unicité du grain
    CONSTRAINT uq_fact_performance_grain
        UNIQUE(player_id, team_id, season_id, league_id)
);

-- Indexes analytiques
CREATE INDEX IF NOT EXISTS idx_fact_player_id       ON mart.fact_performance(player_id);
CREATE INDEX IF NOT EXISTS idx_fact_team_id         ON mart.fact_performance(team_id);
CREATE INDEX IF NOT EXISTS idx_fact_season_id       ON mart.fact_performance(season_id);
CREATE INDEX IF NOT EXISTS idx_fact_league_id       ON mart.fact_performance(league_id);
CREATE INDEX IF NOT EXISTS idx_fact_league_season   ON mart.fact_performance(league_id, season_id);
CREATE INDEX IF NOT EXISTS idx_fact_season_player   ON mart.fact_performance(season_id, player_id);
CREATE INDEX IF NOT EXISTS idx_fact_xg_per_90       ON mart.fact_performance(xg_per_90 DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_fact_goals_per_90    ON mart.fact_performance(goals_per_90 DESC NULLS LAST);
