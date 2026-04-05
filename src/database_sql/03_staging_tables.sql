-- =========================================================
-- STAGING LAYER  –  Dimensions et table de faits
-- Extrait du backup pgAdmin du 2026-04-04 15:00:17 UTC
-- =========================================================

-- =========================================================
-- DIMENSION – Ligues
-- =========================================================
CREATE TABLE IF NOT EXISTS staging.dim_league (
    league_id text NOT NULL,
    league text NOT NULL,
    country text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT dim_league_pkey PRIMARY KEY (league_id),
    CONSTRAINT dim_league_league_key UNIQUE (league)
);

-- =========================================================
-- DIMENSION – Saisons
-- =========================================================
CREATE TABLE IF NOT EXISTS staging.dim_season (
    season_id integer NOT NULL,
    season text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT dim_season_pkey PRIMARY KEY (season_id)
);

-- =========================================================
-- DIMENSION – Équipes
-- =========================================================
CREATE TABLE IF NOT EXISTS staging.dim_team (
    team_id integer NOT NULL,
    team text NOT NULL,
    country text,
    league_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT dim_team_pkey PRIMARY KEY (team_id),
    CONSTRAINT uq_dim_team_name_league UNIQUE (team, league_id),
    CONSTRAINT dim_team_league_id_fkey FOREIGN KEY (league_id) REFERENCES staging.dim_league(league_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_team_league_id ON staging.dim_team USING btree (league_id);

-- =========================================================
-- DIMENSION – Joueurs
-- =========================================================
CREATE TABLE IF NOT EXISTS staging.dim_player (
    player_id bigint NOT NULL,
    player text NOT NULL,
    name_sofascore text,
    nationality text,
    birth_year integer,
    height smallint,
    weight smallint,
    preferred_foot text,
    position_standard text,
    position_description text,
    detailed_positions_current text,
    position_current text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT dim_player_pkey PRIMARY KEY (player_id),
    CONSTRAINT dim_player_position_standard_check CHECK ((position_standard = ANY (ARRAY['Goalkeeper'::text, 'Defender'::text, 'Midfielder'::text, 'Forward'::text])))
);

CREATE INDEX IF NOT EXISTS idx_dim_player_age ON staging.dim_player USING btree (birth_year);
CREATE INDEX IF NOT EXISTS idx_dim_player_name_sofascore ON staging.dim_player USING btree (name_sofascore);
CREATE INDEX IF NOT EXISTS idx_dim_player_nationality ON staging.dim_player USING btree (nationality);
CREATE INDEX IF NOT EXISTS idx_dim_player_position ON staging.dim_player USING btree (position_standard);

-- =========================================================
-- TABLE DE FAITS – Performances par saison
-- Grain : 1 ligne = 1 joueur × 1 équipe × 1 saison × 1 ligue
-- =========================================================
CREATE SEQUENCE IF NOT EXISTS staging.fact_performance_performance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS staging.fact_performance (
    performance_id bigint DEFAULT nextval('staging.fact_performance_performance_id_seq'::regclass) NOT NULL,
    player_id bigint NOT NULL,
    team_id integer NOT NULL,
    season_id integer NOT NULL,
    league_id text NOT NULL,
    matches smallint DEFAULT 0 NOT NULL,
    minutes integer DEFAULT 0 NOT NULL,
    goals smallint DEFAULT 0 NOT NULL,
    assists smallint DEFAULT 0 NOT NULL,
    shots smallint DEFAULT 0 NOT NULL,
    key_passes smallint DEFAULT 0 NOT NULL,
    yellow_cards smallint DEFAULT 0,
    red_cards smallint DEFAULT 0,
    np_goals smallint DEFAULT 0,
    xg numeric(8,4) DEFAULT 0 NOT NULL,
    xa numeric(8,4) DEFAULT 0 NOT NULL,
    xg_chain numeric(8,4) DEFAULT 0,
    xg_buildup numeric(8,4) DEFAULT 0,
    np_xg numeric(8,4) DEFAULT 0,
    goals_per_90 numeric(6,3),
    xg_per_90 numeric(6,3),
    np_goals_per_90 numeric(6,3),
    np_xg_per_90 numeric(6,3),
    assists_per_90 numeric(6,3),
    xa_per_90 numeric(6,3),
    shots_per_90 numeric(6,3),
    key_passes_per_90 numeric(6,3),
    involvement_per_90 numeric(6,3),
    finishing_efficiency numeric(8,4),
    np_finishing_efficiency numeric(8,4),
    playmaking_efficiency numeric(8,4),
    shot_conversion numeric(8,4),
    involvement_index numeric(10,3),
    direct_contribution smallint,
    expected_contribution numeric(8,3),
    offensive_volume smallint,
    player_age_at_season smallint,
    market_value_current numeric(15,2),
    popularity_score_current integer,
    contract_end_date_current date,
    value_per_goal numeric(15,2),
    value_per_xg numeric(15,2),
    value_per_contribution numeric(15,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT fact_performance_assists_check CHECK ((assists >= 0)),
    CONSTRAINT fact_performance_goals_check CHECK ((goals >= 0)),
    CONSTRAINT fact_performance_key_passes_check CHECK ((key_passes >= 0)),
    CONSTRAINT fact_performance_matches_check CHECK ((matches >= 0)),
    CONSTRAINT fact_performance_minutes_check CHECK ((minutes >= 0)),
    CONSTRAINT fact_performance_np_goals_check CHECK ((np_goals >= 0)),
    CONSTRAINT fact_performance_red_cards_check CHECK ((red_cards >= 0)),
    CONSTRAINT fact_performance_shots_check CHECK ((shots >= 0)),
    CONSTRAINT fact_performance_yellow_cards_check CHECK ((yellow_cards >= 0)),
    CONSTRAINT fact_performance_pkey PRIMARY KEY (performance_id),
    CONSTRAINT uq_fact_performance_grain UNIQUE (player_id, team_id, season_id, league_id),
    CONSTRAINT fact_performance_league_id_fkey FOREIGN KEY (league_id) REFERENCES staging.dim_league(league_id) ON DELETE CASCADE,
    CONSTRAINT fact_performance_player_id_fkey FOREIGN KEY (player_id) REFERENCES staging.dim_player(player_id) ON DELETE CASCADE,
    CONSTRAINT fact_performance_season_id_fkey FOREIGN KEY (season_id) REFERENCES staging.dim_season(season_id) ON DELETE CASCADE,
    CONSTRAINT fact_performance_team_id_fkey FOREIGN KEY (team_id) REFERENCES staging.dim_team(team_id) ON DELETE CASCADE
);

ALTER SEQUENCE staging.fact_performance_performance_id_seq OWNED BY staging.fact_performance.performance_id;

-- Indexes analytiques
CREATE INDEX IF NOT EXISTS idx_fact_goals_per_90 ON staging.fact_performance USING btree (goals_per_90 DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_fact_league_id ON staging.fact_performance USING btree (league_id);
CREATE INDEX IF NOT EXISTS idx_fact_league_season ON staging.fact_performance USING btree (league_id, season_id);
CREATE INDEX IF NOT EXISTS idx_fact_minutes ON staging.fact_performance USING btree (minutes);
CREATE INDEX IF NOT EXISTS idx_fact_player_id ON staging.fact_performance USING btree (player_id);
CREATE INDEX IF NOT EXISTS idx_fact_player_team ON staging.fact_performance USING btree (player_id, team_id);
CREATE INDEX IF NOT EXISTS idx_fact_season_id ON staging.fact_performance USING btree (season_id);
CREATE INDEX IF NOT EXISTS idx_fact_season_player ON staging.fact_performance USING btree (season_id, player_id);
CREATE INDEX IF NOT EXISTS idx_fact_team_id ON staging.fact_performance USING btree (team_id);
CREATE INDEX IF NOT EXISTS idx_fact_xg_per_90 ON staging.fact_performance USING btree (xg_per_90 DESC NULLS LAST);

-- Foreign Keys already included in CREATE TABLE
