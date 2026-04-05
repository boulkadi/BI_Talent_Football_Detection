-- =========================================================
-- MART LAYER  –  Vues analytiques et procédures stockées
-- Extrait du backup pgAdmin du 2026-04-04 15:00:17 UTC
-- =========================================================

-- =========================================================
-- PROCÉDURE STOCKÉE – Rafraîchissement des statistiques
-- =========================================================
CREATE OR REPLACE PROCEDURE mart.refresh_analytical_marts()
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Objectif : Recalcul et optimisation des tables du Mart
    -- Cette procédure simule le rafraîchissement d'un entrepôt de données.
    -- Si nous utilisions des Materialized Views, la syntaxe serait :
    -- REFRESH MATERIALIZED VIEW mart.mv_player_scouting_profile;
    
    -- Pour notre cas avec vue standards (VIEW), nous forçons 
    -- la mise à jour des statistiques de l'optimiseur Postgres 
    -- pour garantir que nos nouvelles jointures soient performantes :
    ANALYZE staging.fact_performance;
    ANALYZE staging.dim_player;
    ANALYZE staging.dim_team;
    
    RAISE NOTICE 'Analytics Mart indexes and statistics refreshed successfully at %', NOW();
END;
$$;

-- =========================================================
-- VUE – Profil de scouting des joueurs
-- =========================================================
CREATE OR REPLACE VIEW mart.vw_player_scouting_profile AS
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

-- =========================================================
-- VUE – Talents sous-évalués
-- =========================================================
CREATE OR REPLACE VIEW mart.vw_undervalued_talents AS
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

-- =========================================================
-- VUE – Efficacité offensive des équipes
-- =========================================================
CREATE OR REPLACE VIEW mart.vw_team_offensive_efficiency AS
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
