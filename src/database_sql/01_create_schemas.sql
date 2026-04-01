-- =========================================================
-- FOOTBALL TALENT DETECTION - POSTGRESQL SCHEMAS
-- =========================================================

-- Création des schémas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;

-- Commentaires sur les schémas
COMMENT ON SCHEMA raw IS 'Données brutes directement importées du scraping';
COMMENT ON SCHEMA staging IS 'Données nettoyées, typées et validées';
COMMENT ON SCHEMA mart IS 'Couche analytique optimisée pour le scouting et la BI';
