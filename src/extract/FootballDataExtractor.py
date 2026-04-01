import pandas as pd
import time
import os
from src.extract.understat_extractor import UnderstatExtractor
from src.extract.sofascore_client import SofaScoreClient
from tqdm import tqdm

class FootballDataOrchestrator:
    """
    Orchestre l'extraction multi-sources, multi-ligues et multi-saisons
    avec gestion intelligente du cache.
    """

    def __init__(self, leagues: list, seasons: list):
        self.leagues = leagues
        self.seasons = seasons
        # Le client SofaScore gère désormais son propre cache interne
        self.sofascore_client = SofaScoreClient()

    def _enrich_players(self, df_performance: pd.DataFrame) -> pd.DataFrame:
        """
        Enrichit les statistiques Understat avec les données stables de SofaScore.
        """
        sofa_details = []
        total = len(df_performance)
        
        # On utilise tqdm pour visualiser l'avancement
        for index, row in tqdm(df_performance.iterrows(), total=total, desc="Enrichissement SofaScore"):
            player_name = row['player']
            
            # Vérification si le joueur est déjà dans le cache du client
            # (get_player_info s'occupe de vérifier le JSON local)
            info = self.sofascore_client.get_player_info(player_name)
            
            if info:
                sofa_details.append(info)
            else:
                sofa_details.append({})
            
            # On ne fait une pause QUE si on a dû interroger l'API (pas dans le cache)
            if player_name not in self.sofascore_client.cache:
                time.sleep(0.5)

        df_sofa = pd.DataFrame(sofa_details)
        
        # Concaténation propre en ignorant les index de ligne originaux
        return pd.concat([df_performance.reset_index(drop=True), df_sofa], axis=1)

    def run_full_extraction(self) -> pd.DataFrame:
        """
        Boucle sur toutes les ligues et saisons demandées avec barre de progression.
        """
        all_dfs = []

        total_combinations = len(self.leagues) * len(self.seasons)
        
        # On peut aussi ajouter un tqdm global pour les ligues/saisons
        with tqdm(total=total_combinations, desc="Extraction Globale") as pbar:
            for league in self.leagues:
                for season in self.seasons:
                    tqdm.write(f"\n--- [START] {league} | Saison {season} ---")
                    
                    try:
                        # 1. Extraction Understat
                        extractor = UnderstatExtractor(league, season)
                        df_step = extractor.extract()
                        
                        if df_step is None or df_step.empty:
                            tqdm.write(f"Pas de données pour {league} {season}.")
                            pbar.update(1)
                            continue

                        # 2. Enrichissement SofaScore (avec cache)
                        df_final_step = self._enrich_players(df_step)
                        all_dfs.append(df_final_step)
                        tqdm.write(f"--- [OK] {len(df_final_step)} joueurs traités ---\n")
                        
                    except Exception as e:
                        tqdm.write(f"Erreur majeure sur {league}/{season} : {e}")
                    
                    pbar.update(1)

        if not all_dfs:
            return pd.DataFrame()

        # Fusion finale de tous les championnats/saisons
        return pd.concat(all_dfs, ignore_index=True)