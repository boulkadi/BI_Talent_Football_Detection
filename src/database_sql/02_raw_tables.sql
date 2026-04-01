-- =========================================================
-- RAW LAYER  –  Ingestion brute (Understat + SofaScore)
-- Objectif : stocker les données telles qu'elles arrivent
--            sans transformation ni contrainte métier.
-- Conventions :
--   • Toutes les colonnes stats sont TEXT (pas de rejet à l'insertion)
--   • Colonnes de tracking préfixées par "_"
--   • Clé naturelle (league, season_id, player, team) pour déduplication
-- =========================================================

-- ---------------------------------------------------------
-- raw.player_stats
-- Table centrale du raw : une ligne = un joueur × une saison
-- Sources fusionnées : Understat (soccerdata) + SofaScore
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.player_stats (

    -- ── Clé technique ──────────────────────────────────────
    id                              BIGSERIAL       PRIMARY KEY,

    -- ── Tracking de la pipeline ────────────────────────────
    _extracted_at                   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    _batch_id                       UUID            NOT NULL DEFAULT gen_random_uuid(),
    _source                         TEXT            NOT NULL DEFAULT 'understat+sofascore',

    -- ── Clé naturelle (Understat) ──────────────────────────
    -- Sert à détecter les doublons lors du chargement en staging
    league                          TEXT,           -- e.g. "FRA-Ligue 1"
    league_id                       TEXT,           -- identifiant unique de la league chez Understat
    season                          TEXT,           -- e.g. "2223"  (label de season)
    season_id                       TEXT,           -- e.g. "2022"  (année de début)
    player                          TEXT,           -- nom Understat
    player_id                       TEXT,      -- identifiant unique du joueur chez Undrstat
    team                            TEXT,           -- nom de l'équipe
    team_id                         TEXT,      -- identifiant unique de l'équipe chez Understat

    -- ── Statistiques de volume (Understat) ─────────────────
    matches                         TEXT,
    minutes                         TEXT,
    goals                           TEXT,
    assists                         TEXT,
    shots                           TEXT,
    key_passes                      TEXT,
    yellow_cards                    TEXT,
    red_cards                       TEXT,

    -- ── Métriques xG (Understat) ───────────────────────────
    xg                              TEXT,           -- expected goals
    xa                              TEXT,           -- expected assists
    xg_chain                        TEXT,           -- xG sur toutes les actions de la chaîne
    xg_buildup                      TEXT,           -- xG sur les actions de construction
    np_goals                        TEXT,           -- goals hors penalty
    np_xg                           TEXT,           -- xG hors penalty

    -- ── Données biographiques (SofaScore) ──────────────────
    name_sofascore                  TEXT,           -- nom canonique SofaScore
    birth_ts                        TEXT,           -- timestamp Unix (secondes)
    height                          TEXT,           -- cm
    weight                          TEXT,           -- kg
    preferred_foot                  TEXT,           -- "right" | "left" | "both"
    nationality                     TEXT,

    -- ── Position (Understat) ───────────────────────────────
    position                        TEXT,           -- code brut Understat (ex: "M S")

    -- ── Position (SofaScore) ───────────────────────────────
    position_current                TEXT,           -- code brut SofaScore (ex: "M")
    detailed_positions_current      TEXT,           -- liste JSON sérialisée

    -- ── Valeur & popularité (SofaScore) ────────────────────
    market_value_current            TEXT,           -- valeur marchande en €
    contract_until_ts_current       TEXT,           -- timestamp fin de contrat
    popularity_score_current        TEXT            -- userCount SofaScore

);

-- ---------------------------------------------------------
-- Index d'unicité fonctionnelle (pas UNIQUE pour tolérer
-- les re-chargements) : utilisé par la staging pour le merge
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_raw_player_stats_natural_key
    ON raw.player_stats (league, season_id, player, team);

CREATE INDEX IF NOT EXISTS idx_raw_player_stats_batch
    ON raw.player_stats (_batch_id);

CREATE INDEX IF NOT EXISTS idx_raw_player_stats_extracted_at
    ON raw.player_stats (_extracted_at);

-- ---------------------------------------------------------
-- Commentaires métier
-- ---------------------------------------------------------
COMMENT ON TABLE  raw.player_stats                          IS 'Données brutes fusionnées Understat + SofaScore – une ligne par joueur × saison';
COMMENT ON COLUMN raw.player_stats._batch_id                IS 'Identifiant du batch d''extraction, permet de rejouer ou d''annuler un lot';
COMMENT ON COLUMN raw.player_stats.season_id                IS 'Année de début de saison (ex: 2022 = saison 2022/23)';
COMMENT ON COLUMN raw.player_stats.xg_chain                 IS 'xG cumulé sur toutes les actions auxquelles le joueur a participé';
COMMENT ON COLUMN raw.player_stats.detailed_positions_current IS 'Liste JSON des positions détaillées retournées par SofaScore';
