import os
import sys
from datetime import datetime
from airflow.decorators import dag, task
import logging

# Ajout du chemin racine pour que Airflow trouve les modules src.*
sys.path.append('/opt/airflow')

from src.extract.FootballDataExtractor import FootballDataOrchestrator
from src.transform.football_transformer import DataTransformer, FeatureEngineer
from src.load.football_loader import FootballLoader
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

MES_LIGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "ITA-Serie A",
    "GER-Bundesliga",
    "FRA-Ligue 1"
]
MES_SAISONS = ["2122", "2223", "2324", "2425", "2526"]

@dag(
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['football', 'etl', 'all_seasons'],
    description="Pipeline ETL complet pour toutes les saisons (Exécution Manuelle)"
)
def football_etl_all_seasons():

    @task
    def extraction(leagues, seasons) -> str:
        logger.info(f"Début de l'extraction. Ligues: {leagues}, Saisons: {seasons}")
        orchestrator = FootballDataOrchestrator(leagues=leagues, seasons=seasons)
        df_raw = orchestrator.run_full_extraction()
        
        if df_raw.empty:
            raise ValueError("L'extraction a échoué ou aucune donnée n'a été récupérée.")
        
        data_dir = '/opt/airflow/data/datasets'
        os.makedirs(data_dir, exist_ok=True)
        raw_path = os.path.join(data_dir, "raw_data_all_seasons.csv")
        df_raw.to_csv(raw_path, index=False)
        
        logger.info(f"Extraction terminée avec succès. {len(df_raw)} lignes récupérées.")
        return raw_path

    @task
    def transformation(raw_path: str) -> tuple:
        import pandas as pd
        logger.info("Début de la transformation des données...")
        df_raw = pd.read_csv(raw_path)
        transformer = DataTransformer()
        feature_engineer = FeatureEngineer()
        
        df_clean = transformer.clean_data(df_raw)
        df_final = feature_engineer.apply_all_features(df_clean)
        
        clean_path = raw_path.replace("raw_data", "clean_data")
        df_final.to_csv(clean_path, index=False)
        
        logger.info(f"Transformation terminée. {len(df_final)} lignes prêtes pour le chargement.")
        return raw_path, clean_path

    @task
    def loading(paths: tuple):
        import pandas as pd
        logger.info("Début du chargement en base de données...")
        raw_path, clean_path = paths
        df_raw = pd.read_csv(raw_path)
        df_final = pd.read_csv(clean_path)
        
        db = DatabaseManager()
        loader = FootballLoader(db)
        
        logger.info("Chargement des données brutes...")
        loader.load_raw_data(df_raw)
        
        logger.info("Chargement dans les tables de dimensions (UPSERT)...")
        loader.load_dimensions(df_final)
        logger.info("Chargement terminé.")

    # Définition des dépendances
    raw_path = extraction(MES_LIGUES, MES_SAISONS)
    transformed_paths = transformation(raw_path)
    loading(transformed_paths)

_ = football_etl_all_seasons()
