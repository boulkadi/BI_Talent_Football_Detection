import sys
import os
import logging
import pandas as pd

# S'assurer que le chemin racine du projet est dans le PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.extract.FootballDataExtractor import FootballDataOrchestrator
from src.transform.football_transformer import DataTransformer, FeatureEngineer
from src.load.football_loader import FootballLoader
from src.database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline():
    # Définition du périmètre de données
    mes_ligues = [
        "ENG-Premier League",
        "ESP-La Liga",
        "ITA-Serie A",
        "GER-Bundesliga",
        "FRA-Ligue 1"
    ]
    mes_saisons = ["2122","2223", "2324", "2425", "2526"]

    logger.info("=== 1. EXTRACT ===")
    logger.info(f"Début de l'extraction pour les ligues : {mes_ligues} et saisons : {mes_saisons}")
    
    orchestrator = FootballDataOrchestrator(leagues=mes_ligues, seasons=mes_saisons)
    df_raw = orchestrator.run_full_extraction()
    
    # Save raw data
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'datasets'))
    os.makedirs(data_dir, exist_ok=True)
    df_raw.to_csv(os.path.join(data_dir, "raw_data.csv"), index=False)
    
    if df_raw.empty:
        logger.error("L'extraction a échoué ou aucune donnée n'a été récupérée.")
        return
        
    logger.info(f"Extraction terminée avec succès. {len(df_raw)} lignes récupérées.")

    logger.info("=== 2. TRANSFORM ===")
    transformer = DataTransformer()
    feature_engineer = FeatureEngineer()
    
    df_clean = transformer.clean_data(df_raw)
    df_final = feature_engineer.apply_all_features(df_clean)
    df_final.to_csv(os.path.join(data_dir, "clean_data.csv"), index=False)
    
    logger.info(f"Transformation terminée. {len(df_final)} lignes prêtes pour le chargement.")

    logger.info("=== 3. LOAD ===")
    db = DatabaseManager()
    loader = FootballLoader(db)
    logger.info("Chargement des données brutes...")
    loader.load_raw_data(df_raw)
    # Remplir les données dimensionnelles (staging.dim_league, staging.dim_season, staging.dim_team, staging.dim_player)
    # Et les faits (staging.fact_performance)
    logger.info("Chargement dans les tables de dimensions (UPSERT)...")
    loader.load_dimensions(df_final)
    
    # Et potentiellement les raw data si on veut garder une trace
    # (optionnel suivant votre besoin, souvent on l'ignore vu qu'on a déjà extract/transform).
    # loader.load_raw_data(df_raw)
    
    logger.info("=== PIPELINE TERMINÉ AVEC SUCCÈS ===")

if __name__ == "__main__":
    run_pipeline()
