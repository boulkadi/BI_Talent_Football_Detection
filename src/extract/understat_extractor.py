import os
from pathlib import Path
import soccerdata as sd
import pandas as pd

# On définit BASE_DIR par rapport à l'emplacement de ce fichier .py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class UnderstatExtractor:
    """
    Extracteur de statistiques Understat optimisé pour Airflow.
    """

    def __init__(self, league: str, season: str):
        self.league = league
        self.season = season
        
        # --- FIX RÉSEAU (IMPORTANT POUR AIRFLOW) ---
        # Nettoyage des variables d'environnement proxy pour éviter les timeouts
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            os.environ.pop(key, None)

        # --- GESTION DU CACHE ---
        # soccerdata exige un Path (pathlib) et non un str pour data_dir
        self.data_dir = BASE_DIR / "data" / "soccerdata_cache"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def extract(self) -> pd.DataFrame:
        """
        Récupère les stats et gère les erreurs potentielles.
        """
        understat = sd.Understat(
            leagues=self.league,
            seasons=self.season,
            data_dir=self.data_dir
        )

        try:
            # Extraction des données
            df = understat.read_player_season_stats().reset_index()
            return df
        except Exception as e:
            # Log précis pour le monitoring Airflow
            print(f"Erreur d'extraction Understat pour {self.league} {self.season}: {e}")
            raise