import os
import sys
from datetime import datetime, timedelta
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
# Uniquement la dernière saison en cours
MES_SAISONS = ["2526"]

@dag(
    schedule_interval="0 3 * * 1",  # Tous les lundis à 03:00 AM
    start_date=datetime(2025, 1, 1),  # Date passée pour activer le scheduler
    catchup=False,
    tags=['football', 'etl', 'weekly'],
    description="Pipeline de mise à jour hebdomadaire des statistiques de la saison en cours"
)
def football_etl_weekly_update():

    @task
    def extraction(leagues, seasons) -> str:
        logger.info(f"Début de l'extraction Hebdo. Ligues: {leagues}, Saisons: {seasons}")
        orchestrator = FootballDataOrchestrator(leagues=leagues, seasons=seasons)
        df_raw = orchestrator.run_full_extraction()
        
        if df_raw.empty:
            raise ValueError("L'extraction n'a renvoyé aucune donnée pour la mise à jour hebdo.")
        
        data_dir = '/opt/airflow/data/datasets'
        os.makedirs(data_dir, exist_ok=True)
        raw_path = os.path.join(data_dir, "raw_data_weekly.csv")
        df_raw.to_csv(raw_path, index=False)
        return raw_path

    @task
    def transformation(raw_path: str) -> tuple:
        import pandas as pd
        logger.info("Début de la transformation Hebdo...")
        df_raw = pd.read_csv(raw_path)
        transformer = DataTransformer()
        feature_engineer = FeatureEngineer()
        
        df_clean = transformer.clean_data(df_raw)
        df_final = feature_engineer.apply_all_features(df_clean)
        
        clean_path = raw_path.replace("raw", "clean")
        df_final.to_csv(clean_path, index=False)
        return raw_path, clean_path

    @task
    def loading(paths: tuple):
        import pandas as pd
        logger.info("Chargement en base de données (UPSERT hebdo)...")
        raw_path, clean_path = paths
        df_raw = pd.read_csv(raw_path)
        df_final = pd.read_csv(clean_path)
        
        db = DatabaseManager()
        loader = FootballLoader(db)
        
        # Pour le run hebdo, on update directement les dimensions et les faits
        # La BD supportera les UPSERT proprement via nos fonctions
        loader.load_raw_data_current_season(df_raw)
        loader.load_dimensions_current_season(df_final)
        logger.info("Mise à jour Hebdo terminée.")

    # Définition des dépendances
    raw_path = extraction(MES_LIGUES, MES_SAISONS)
    transformed_paths = transformation(raw_path)
    loading(transformed_paths)

_ = football_etl_weekly_update()
