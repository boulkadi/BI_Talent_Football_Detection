-- =========================================================
-- STAGING LAYER  –  Données nettoyées, typées et validées
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.player_stats (

    -- ── Clé technique ──────────────────────────────────────
    id                              BIGSERIAL       PRIMARY KEY,

    -- ── Tracking de la pipeline ────────────────────────────
    _loaded_at                      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    _raw_batch_id                   UUID,

    -- ── Clé naturelle (contrainte UNIQUE pour UPSERT) ──────
    league                          TEXT            NOT NULL,
    league_id                       TEXT         NOT NULL,
    country                         TEXT,           NOT NULL,
    season_id                       TEXT         NOT NULL,
    player                          TEXT            NOT NULL,
    player_id                       TEXT         NOT NULL,
    team                            TEXT            NOT NULL,
    team_id                         TEXT         NOT NULL,

    -- ── Identité SofaScore ─────────────────────────────────
    name_sofascore                  TEXT,
    nationality                     TEXT,
    birth_year                      INTEGER,
    player_age_at_season            SMALLINT        CHECK (player_age_at_season BETWEEN 10 AND 60),
    height                          SMALLINT        CHECK (height BETWEEN 140 AND 230),
    weight                          SMALLINT        CHECK (weight BETWEEN 40 AND 150),
    preferred_foot                  TEXT,

    -- ── Position (standardisée) ────────────────────────────
    position_current                TEXT,
    position_standard               TEXT            CHECK (position_standard IN (
                                        'Goalkeeper', 'Defender', 'Midfielder', 'Forward'
                                    )),
    position_description            TEXT,
    detailed_positions_current      TEXT,

    -- ── Statistiques de volume ─────────────────────────────
    matches                         SMALLINT        NOT NULL DEFAULT 0 CHECK (matches >= 0),
    minutes                         INTEGER         NOT NULL DEFAULT 0 CHECK (minutes >= 0),
    goals                           SMALLINT        NOT NULL DEFAULT 0 CHECK (goals >= 0),
    assists                         SMALLINT        NOT NULL DEFAULT 0 CHECK (assists >= 0),
    shots                           SMALLINT        NOT NULL DEFAULT 0 CHECK (shots >= 0),
    key_passes                      SMALLINT        NOT NULL DEFAULT 0 CHECK (key_passes >= 0),
    yellow_cards                    SMALLINT        DEFAULT 0 CHECK (yellow_cards >= 0),
    red_cards                       SMALLINT        DEFAULT 0 CHECK (red_cards >= 0),
    np_goals                        SMALLINT        DEFAULT 0 CHECK (np_goals >= 0),

    -- ── Métriques xG ───────────────────────────────────────
    xg                              NUMERIC(8,4)   NOT NULL DEFAULT 0,
    xa                              NUMERIC(8,4)   NOT NULL DEFAULT 0,
    xg_chain                        NUMERIC(8,4)   DEFAULT 0,
    xg_buildup                      NUMERIC(8,4)   DEFAULT 0,
    np_xg                           NUMERIC(8,4)   DEFAULT 0,

    -- ── KPIs per-90 ───────────────────────────────────────
    goals_per_90                    NUMERIC(6,3),
    xg_per_90                       NUMERIC(6,3),
    np_goals_per_90                 NUMERIC(6,3),
    np_xg_per_90                    NUMERIC(6,3),
    assists_per_90                  NUMERIC(6,3),
    xa_per_90                       NUMERIC(6,3),
    shots_per_90                    NUMERIC(6,3),
    key_passes_per_90               NUMERIC(6,3),
    involvement_per_90              NUMERIC(6,3),

    -- ── KPIs d'efficacité ──────────────────────────────────
    finishing_efficiency            NUMERIC(8,4),
    np_finishing_efficiency         NUMERIC(8,4),
    playmaking_efficiency           NUMERIC(8,4),
    shot_conversion                 NUMERIC(8,4),

    -- ── KPIs collectifs ───────────────────────────────────
    involvement_index               NUMERIC(10,3),
    direct_contribution             SMALLINT,
    expected_contribution           NUMERIC(8,3),
    offensive_volume                SMALLINT,

    -- ── Données marché (SofaScore) ────────────────────────
    market_value_current            NUMERIC(15,2),
    popularity_score_current        INTEGER         CHECK (popularity_score_current >= 0),
    contract_end_date_current       DATE,

    -- ── Contrainte d'unicité métier ───────────────────────
    CONSTRAINT uq_staging_player_season
        UNIQUE (league, season_id, player, team)
);

-- ---------------------------------------------------------
-- Indexes pour performance
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_staging_player_stats_league_season
    ON staging.player_stats (league, season_id);

CREATE INDEX IF NOT EXISTS idx_staging_player_stats_player
    ON staging.player_stats (player);

CREATE INDEX IF NOT EXISTS idx_staging_player_stats_team
    ON staging.player_stats (team);

CREATE INDEX IF NOT EXISTS idx_staging_player_stats_position
    ON staging.player_stats (position_standard);

-- ---------------------------------------------------------
-- Commentaires métier
-- ---------------------------------------------------------
COMMENT ON TABLE  staging.player_stats                      IS 'Données nettoyées et typées prêtes pour la mart – sortie directe de DataTransformer + FeatureEngineer';
COMMENT ON COLUMN staging.player_stats._raw_batch_id        IS 'Référence au batch raw.player_stats._batch_id ayant produit cette ligne';
COMMENT ON COLUMN staging.player_stats.season_id            IS 'Année de début de saison (2022 = saison 2022/23)';
COMMENT ON COLUMN staging.player_stats.involvement_per_90   IS '(xg_chain + xg_buildup) / minutes * 90 – participation globale aux actions offensives';
COMMENT ON COLUMN staging.player_stats.finishing_efficiency IS 'goals / xg – mesure la sur/sous-performance face au but';
COMMENT ON COLUMN staging.player_stats.direct_contribution  IS 'goals + assists – contribution directe du joueur';
COMMENT ON COLUMN staging.player_stats.expected_contribution IS 'xg + xa – contribution attendue du joueur';
COMMENT ON COLUMN staging.player_stats.offensive_volume     IS 'shots + key_passes – volume offensif du joueur';
