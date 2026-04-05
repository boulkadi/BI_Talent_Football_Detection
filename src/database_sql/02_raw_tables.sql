-- =========================================================
-- RAW LAYER  –  Ingestion brute (Understat + SofaScore)
-- Extrait du backup pgAdmin du 2026-04-04 15:00:17 UTC
-- =========================================================

CREATE TABLE IF NOT EXISTS raw.player_stats (
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
