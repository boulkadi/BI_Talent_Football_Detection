--
-- PostgreSQL database dump
--

\restrict Z9bx7a0OnRlTUA5Nq2LVnq3VKf6puK0UDZgnZKzFGty2DUjZoXYWT61p42nHSap

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.15

-- Started on 2026-04-04 15:00:17 UTC

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 8 (class 2615 OID 16387)
-- Name: mart; Type: SCHEMA; Schema: -; Owner: football_user
--

CREATE SCHEMA mart;


ALTER SCHEMA mart OWNER TO football_user;

--
-- TOC entry 3520 (class 0 OID 0)
-- Dependencies: 8
-- Name: SCHEMA mart; Type: COMMENT; Schema: -; Owner: football_user
--

COMMENT ON SCHEMA mart IS 'Couche analytique optimisée pour le scouting et la BI';


--
-- TOC entry 6 (class 2615 OID 16385)
-- Name: raw; Type: SCHEMA; Schema: -; Owner: football_user
--

CREATE SCHEMA raw;


ALTER SCHEMA raw OWNER TO football_user;

--
-- TOC entry 3521 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA raw; Type: COMMENT; Schema: -; Owner: football_user
--

COMMENT ON SCHEMA raw IS 'Données brutes directement importées du scraping';


--
-- TOC entry 7 (class 2615 OID 16386)
-- Name: staging; Type: SCHEMA; Schema: -; Owner: football_user
--

CREATE SCHEMA staging;


ALTER SCHEMA staging OWNER TO football_user;

--
-- TOC entry 3522 (class 0 OID 0)
-- Dependencies: 7
-- Name: SCHEMA staging; Type: COMMENT; Schema: -; Owner: football_user
--

COMMENT ON SCHEMA staging IS 'Données nettoyées, typées et validées';


--
-- TOC entry 227 (class 1255 OID 16573)
-- Name: refresh_analytical_marts(); Type: PROCEDURE; Schema: mart; Owner: football_user
--

CREATE PROCEDURE mart.refresh_analytical_marts()
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Objectif : Recalcul et optimisation des tables du Mart
    -- Cette procÃ©dure simule le rafraÃ®chissement d'un entrepÃ´t de donnÃ©es.
    -- Si nous utilisions des Materialized Views, la syntaxe serait :
    -- REFRESH MATERIALIZED VIEW mart.mv_player_scouting_profile;
    
    -- Pour notre cas avec vue standards (VIEW), nous forÃ§ons 
    -- la mise Ã  jour des statistiques de l'optimiseur Postgres 
    -- pour garantir que nos nouvelles jointures soient performantes :
    ANALYZE staging.fact_performance;
    ANALYZE staging.dim_player;
    ANALYZE staging.dim_team;
    
    RAISE NOTICE 'Analytics Mart indexes and statistics refreshed successfully at %', NOW();
END;
$$;


ALTER PROCEDURE mart.refresh_analytical_marts() OWNER TO football_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 217 (class 1259 OID 16403)
-- Name: dim_league; Type: TABLE; Schema: staging; Owner: football_user
--

CREATE TABLE staging.dim_league (
    league_id text NOT NULL,
    league text NOT NULL,
    country text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE staging.dim_league OWNER TO football_user;

--
-- TOC entry 220 (class 1259 OID 16440)
-- Name: dim_player; Type: TABLE; Schema: staging; Owner: football_user
--

CREATE TABLE staging.dim_player (
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
    CONSTRAINT dim_player_position_standard_check CHECK ((position_standard = ANY (ARRAY['Goalkeeper'::text, 'Defender'::text, 'Midfielder'::text, 'Forward'::text])))
);


ALTER TABLE staging.dim_player OWNER TO football_user;

--
-- TOC entry 218 (class 1259 OID 16414)
-- Name: dim_season; Type: TABLE; Schema: staging; Owner: football_user
--

CREATE TABLE staging.dim_season (
    season_id integer NOT NULL,
    season text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE staging.dim_season OWNER TO football_user;

--
-- TOC entry 219 (class 1259 OID 16423)
-- Name: dim_team; Type: TABLE; Schema: staging; Owner: football_user
--

CREATE TABLE staging.dim_team (
    team_id integer NOT NULL,
    team text NOT NULL,
    country text,
    league_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE staging.dim_team OWNER TO football_user;

--
-- TOC entry 222 (class 1259 OID 16454)
-- Name: fact_performance; Type: TABLE; Schema: staging; Owner: football_user
--

CREATE TABLE staging.fact_performance (
    performance_id bigint NOT NULL,
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
    CONSTRAINT fact_performance_yellow_cards_check CHECK ((yellow_cards >= 0))
);


ALTER TABLE staging.fact_performance OWNER TO football_user;

--
-- TOC entry 223 (class 1259 OID 16558)
-- Name: vw_player_scouting_profile; Type: VIEW; Schema: mart; Owner: football_user
--

CREATE VIEW mart.vw_player_scouting_profile AS
 WITH player_stats AS (
         SELECT f.player_id,
            f.team_id,
            f.league_id,
            f.season_id,
            sum(f.matches) AS matches,
            sum(f.minutes) AS minutes,
            sum(f.goals) AS goals,
            sum(f.assists) AS assists,
            sum(f.xg) AS xg,
            sum(f.xa) AS xa,
            sum(f.yellow_cards) AS yellow_cards,
            sum(f.red_cards) AS red_cards,
            max(f.market_value_current) AS market_value_current,
            sum((f.goals + f.assists)) AS direct_contributions,
            sum((f.xg + f.xa)) AS expected_contributions,
            (((sum((f.goals + f.assists)))::numeric - sum((f.xg + f.xa))))::numeric(8,2) AS contribution_margin,
            ((((sum(f.goals))::numeric / (NULLIF(sum(f.minutes), 0))::numeric) * (90)::numeric))::numeric(5,2) AS goals_p90,
            (((sum(f.xg) / (NULLIF(sum(f.minutes), 0))::numeric) * (90)::numeric))::numeric(5,2) AS xg_p90
           FROM staging.fact_performance f
          WHERE ((f.player_id IS NOT NULL) AND (f.minutes > 0))
          GROUP BY f.player_id, f.team_id, f.league_id, f.season_id
        )
 SELECT p.player AS player_name,
    p.nationality,
    (EXTRACT(year FROM CURRENT_DATE) - (p.birth_year)::numeric) AS estimated_age,
    p.position_standard AS "position",
    t.team AS team_name,
    l.league AS league_name,
    s.season AS season_name,
    ps.matches,
    ps.minutes,
    ps.goals,
    ps.assists,
    ps.xg,
    ps.xa,
    ps.direct_contributions,
    ps.expected_contributions,
    ps.contribution_margin,
        CASE
            WHEN (ps.xg > (0)::numeric) THEN (((ps.goals)::numeric / ps.xg))::numeric(5,2)
            ELSE (0)::numeric
        END AS finishing_efficiency,
    ((((ps.yellow_cards + (ps.red_cards * 2)))::numeric / (NULLIF(ps.matches, 0))::numeric))::numeric(5,2) AS discipline_penalty_index,
    ps.market_value_current,
        CASE
            WHEN (((EXTRACT(year FROM CURRENT_DATE) - (p.birth_year)::numeric) <= (23)::numeric) AND (ps.contribution_margin > (0)::numeric) AND (ps.minutes >= 900)) THEN 'Top Prospect'::text
            WHEN (((EXTRACT(year FROM CURRENT_DATE) - (p.birth_year)::numeric) > (23)::numeric) AND (ps.contribution_margin > (2)::numeric)) THEN 'Elite Performer'::text
            WHEN (ps.contribution_margin < ('-2'::integer)::numeric) THEN 'Underperforming'::text
            ELSE 'Standard'::text
        END AS talent_category
   FROM ((((player_stats ps
     JOIN staging.dim_player p ON ((ps.player_id = p.player_id)))
     JOIN staging.dim_team t ON ((ps.team_id = t.team_id)))
     JOIN staging.dim_league l ON ((ps.league_id = l.league_id)))
     JOIN staging.dim_season s ON ((ps.season_id = s.season_id)));


ALTER TABLE mart.vw_player_scouting_profile OWNER TO football_user;

--
-- TOC entry 225 (class 1259 OID 16568)
-- Name: vw_team_offensive_efficiency; Type: VIEW; Schema: mart; Owner: football_user
--

CREATE VIEW mart.vw_team_offensive_efficiency AS
 WITH team_stats AS (
         SELECT l.league_id,
            l.league AS league_name,
            s.season_id,
            s.season AS season_name,
            t.team AS team_name,
            sum(f.goals) AS team_goals,
            sum(f.xg) AS team_xg,
            sum(f.shots) AS team_shots
           FROM (((staging.fact_performance f
             JOIN staging.dim_team t ON ((f.team_id = t.team_id)))
             JOIN staging.dim_league l ON ((f.league_id = l.league_id)))
             JOIN staging.dim_season s ON ((f.season_id = s.season_id)))
          GROUP BY l.league_id, l.league, s.season_id, s.season, t.team
        ), league_avg AS (
         SELECT team_stats.league_id,
            team_stats.season_id,
            avg(team_stats.team_goals) AS avg_league_goals,
            avg(team_stats.team_xg) AS avg_league_xg
           FROM team_stats
          GROUP BY team_stats.league_id, team_stats.season_id
        )
 SELECT ts.league_name,
    ts.season_name,
    ts.team_name,
    ts.team_goals,
    ts.team_xg,
    ts.team_shots,
        CASE
            WHEN (ts.team_shots > 0) THEN (((ts.team_goals)::numeric / (ts.team_shots)::numeric))::numeric(4,2)
            ELSE (0)::numeric
        END AS shot_conversion_rate,
    (la.avg_league_goals)::numeric(6,2) AS avg_league_goals,
    (((ts.team_goals)::numeric - la.avg_league_goals))::numeric(6,2) AS goals_vs_average,
        CASE
            WHEN (((ts.team_goals)::numeric > la.avg_league_goals) AND ((ts.team_goals)::numeric > ts.team_xg)) THEN 'Overperforming & Above Average'::text
            WHEN (((ts.team_goals)::numeric > la.avg_league_goals) AND ((ts.team_goals)::numeric <= ts.team_xg)) THEN 'Underperforming but Above Average'::text
            WHEN ((ts.team_goals)::numeric < la.avg_league_goals) THEN 'Below Average'::text
            ELSE 'Average'::text
        END AS team_performance_status
   FROM (team_stats ts
     JOIN league_avg la ON (((ts.league_id = la.league_id) AND (ts.season_id = la.season_id))))
  ORDER BY ts.league_name, ts.season_name, ts.team_goals DESC;


ALTER TABLE mart.vw_team_offensive_efficiency OWNER TO football_user;

--
-- TOC entry 224 (class 1259 OID 16563)
-- Name: vw_undervalued_talents; Type: VIEW; Schema: mart; Owner: football_user
--

CREATE VIEW mart.vw_undervalued_talents AS
 SELECT p.player AS player_name,
    p.position_standard AS "position",
    t.team AS current_team,
    sum(f.minutes) AS total_minutes,
    sum((f.goals + f.assists)) AS total_direct_contributions,
    sum((f.xg + f.xa)) AS total_expected_contributions,
    max(f.market_value_current) AS known_market_value,
        CASE
            WHEN (sum((f.goals + f.assists)) > 0) THEN ((max(f.market_value_current) / (sum((f.goals + f.assists)))::numeric))::numeric(15,2)
            ELSE NULL::numeric
        END AS cost_per_contribution
   FROM ((staging.fact_performance f
     JOIN staging.dim_player p ON ((f.player_id = p.player_id)))
     JOIN staging.dim_team t ON ((f.team_id = t.team_id)))
  WHERE (p.position_standard <> 'Goalkeeper'::text)
  GROUP BY p.player_id, p.player, p.position_standard, t.team
 HAVING (((sum((f.goals + f.assists)) >= 10) OR (sum((f.xg + f.xa)) >= (10)::numeric)) AND (max(f.market_value_current) IS NOT NULL))
  ORDER BY
        CASE
            WHEN (sum((f.goals + f.assists)) > 0) THEN ((max(f.market_value_current) / (sum((f.goals + f.assists)))::numeric))::numeric(15,2)
            ELSE NULL::numeric
        END;


ALTER TABLE mart.vw_undervalued_talents OWNER TO football_user;

--
-- TOC entry 226 (class 1259 OID 16596)
-- Name: player_stats; Type: TABLE; Schema: raw; Owner: football_user
--

CREATE TABLE raw.player_stats (
    league text,
    season text,
    team text,
    player text,
    league_id text,
    season_id bigint,
    team_id bigint,
    player_id bigint,
    "position" text,
    matches bigint,
    minutes bigint,
    goals bigint,
    xg double precision,
    np_goals bigint,
    np_xg double precision,
    assists bigint,
    xa double precision,
    shots bigint,
    key_passes bigint,
    yellow_cards bigint,
    red_cards bigint,
    xg_chain double precision,
    xg_buildup double precision,
    name_sofascore text,
    birth_ts double precision,
    height double precision,
    weight double precision,
    preferred_foot text,
    nationality text,
    position_current text,
    detailed_positions_current text,
    market_value_current double precision,
    contract_until_ts_current double precision,
    popularity_score_current double precision
);


ALTER TABLE raw.player_stats OWNER TO football_user;

--
-- TOC entry 221 (class 1259 OID 16453)
-- Name: fact_performance_performance_id_seq; Type: SEQUENCE; Schema: staging; Owner: football_user
--

CREATE SEQUENCE staging.fact_performance_performance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE staging.fact_performance_performance_id_seq OWNER TO football_user;

--
-- TOC entry 3523 (class 0 OID 0)
-- Dependencies: 221
-- Name: fact_performance_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: staging; Owner: football_user
--

ALTER SEQUENCE staging.fact_performance_performance_id_seq OWNED BY staging.fact_performance.performance_id;


--
-- TOC entry 3307 (class 2604 OID 16457)
-- Name: fact_performance performance_id; Type: DEFAULT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance ALTER COLUMN performance_id SET DEFAULT nextval('staging.fact_performance_performance_id_seq'::regclass);


--
-- TOC entry 3335 (class 2606 OID 16413)
-- Name: dim_league dim_league_league_key; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_league
    ADD CONSTRAINT dim_league_league_key UNIQUE (league);


--
-- TOC entry 3337 (class 2606 OID 16411)
-- Name: dim_league dim_league_pkey; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_league
    ADD CONSTRAINT dim_league_pkey PRIMARY KEY (league_id);


--
-- TOC entry 3346 (class 2606 OID 16449)
-- Name: dim_player dim_player_pkey; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_player
    ADD CONSTRAINT dim_player_pkey PRIMARY KEY (player_id);


--
-- TOC entry 3339 (class 2606 OID 16422)
-- Name: dim_season dim_season_pkey; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_season
    ADD CONSTRAINT dim_season_pkey PRIMARY KEY (season_id);


--
-- TOC entry 3341 (class 2606 OID 16431)
-- Name: dim_team dim_team_pkey; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_team
    ADD CONSTRAINT dim_team_pkey PRIMARY KEY (team_id);


--
-- TOC entry 3352 (class 2606 OID 16486)
-- Name: fact_performance fact_performance_pkey; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT fact_performance_pkey PRIMARY KEY (performance_id);


--
-- TOC entry 3344 (class 2606 OID 16433)
-- Name: dim_team uq_dim_team_name_league; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_team
    ADD CONSTRAINT uq_dim_team_name_league UNIQUE (team, league_id);


--
-- TOC entry 3364 (class 2606 OID 16488)
-- Name: fact_performance uq_fact_performance_grain; Type: CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT uq_fact_performance_grain UNIQUE (player_id, team_id, season_id, league_id);


--
-- TOC entry 3347 (class 1259 OID 16556)
-- Name: idx_dim_player_age; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_dim_player_age ON staging.dim_player USING btree (birth_year);


--
-- TOC entry 3348 (class 1259 OID 16452)
-- Name: idx_dim_player_name_sofascore; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_dim_player_name_sofascore ON staging.dim_player USING btree (name_sofascore);


--
-- TOC entry 3349 (class 1259 OID 16450)
-- Name: idx_dim_player_nationality; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_dim_player_nationality ON staging.dim_player USING btree (nationality);


--
-- TOC entry 3350 (class 1259 OID 16451)
-- Name: idx_dim_player_position; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_dim_player_position ON staging.dim_player USING btree (position_standard);


--
-- TOC entry 3342 (class 1259 OID 16439)
-- Name: idx_dim_team_league_id; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_dim_team_league_id ON staging.dim_team USING btree (league_id);


--
-- TOC entry 3353 (class 1259 OID 16516)
-- Name: idx_fact_goals_per_90; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_goals_per_90 ON staging.fact_performance USING btree (goals_per_90 DESC NULLS LAST);


--
-- TOC entry 3354 (class 1259 OID 16512)
-- Name: idx_fact_league_id; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_league_id ON staging.fact_performance USING btree (league_id);


--
-- TOC entry 3355 (class 1259 OID 16513)
-- Name: idx_fact_league_season; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_league_season ON staging.fact_performance USING btree (league_id, season_id);


--
-- TOC entry 3356 (class 1259 OID 16557)
-- Name: idx_fact_minutes; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_minutes ON staging.fact_performance USING btree (minutes);


--
-- TOC entry 3357 (class 1259 OID 16509)
-- Name: idx_fact_player_id; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_player_id ON staging.fact_performance USING btree (player_id);


--
-- TOC entry 3358 (class 1259 OID 16555)
-- Name: idx_fact_player_team; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_player_team ON staging.fact_performance USING btree (player_id, team_id);


--
-- TOC entry 3359 (class 1259 OID 16511)
-- Name: idx_fact_season_id; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_season_id ON staging.fact_performance USING btree (season_id);


--
-- TOC entry 3360 (class 1259 OID 16514)
-- Name: idx_fact_season_player; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_season_player ON staging.fact_performance USING btree (season_id, player_id);


--
-- TOC entry 3361 (class 1259 OID 16510)
-- Name: idx_fact_team_id; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_team_id ON staging.fact_performance USING btree (team_id);


--
-- TOC entry 3362 (class 1259 OID 16515)
-- Name: idx_fact_xg_per_90; Type: INDEX; Schema: staging; Owner: football_user
--

CREATE INDEX idx_fact_xg_per_90 ON staging.fact_performance USING btree (xg_per_90 DESC NULLS LAST);


--
-- TOC entry 3365 (class 2606 OID 16434)
-- Name: dim_team dim_team_league_id_fkey; Type: FK CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.dim_team
    ADD CONSTRAINT dim_team_league_id_fkey FOREIGN KEY (league_id) REFERENCES staging.dim_league(league_id) ON DELETE SET NULL;


--
-- TOC entry 3366 (class 2606 OID 16504)
-- Name: fact_performance fact_performance_league_id_fkey; Type: FK CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT fact_performance_league_id_fkey FOREIGN KEY (league_id) REFERENCES staging.dim_league(league_id) ON DELETE CASCADE;


--
-- TOC entry 3367 (class 2606 OID 16489)
-- Name: fact_performance fact_performance_player_id_fkey; Type: FK CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT fact_performance_player_id_fkey FOREIGN KEY (player_id) REFERENCES staging.dim_player(player_id) ON DELETE CASCADE;


--
-- TOC entry 3368 (class 2606 OID 16499)
-- Name: fact_performance fact_performance_season_id_fkey; Type: FK CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT fact_performance_season_id_fkey FOREIGN KEY (season_id) REFERENCES staging.dim_season(season_id) ON DELETE CASCADE;


--
-- TOC entry 3369 (class 2606 OID 16494)
-- Name: fact_performance fact_performance_team_id_fkey; Type: FK CONSTRAINT; Schema: staging; Owner: football_user
--

ALTER TABLE ONLY staging.fact_performance
    ADD CONSTRAINT fact_performance_team_id_fkey FOREIGN KEY (team_id) REFERENCES staging.dim_team(team_id) ON DELETE CASCADE;


-- Completed on 2026-04-04 15:00:18 UTC

--
-- PostgreSQL database dump complete
--

\unrestrict Z9bx7a0OnRlTUA5Nq2LVnq3VKf6puK0UDZgnZKzFGty2DUjZoXYWT61p42nHSap

