import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataTransformer:
    """Nettoyage et standardisation des données fusionnées."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataTransformer")

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline de nettoyage complet."""
        if df.empty: return df
        df = df.copy()

        # 1. Doublons (Clé unique : Joueur + Saison + Club)
        initial_len = len(df)
        df = df.drop_duplicates(subset=["player_id", "season_id", "team_id"], keep="last")
        self.logger.info(f"Doublons supprimés: {initial_len - len(df)}")

        # 2. Types String
        str_cols = ["league", "season", "team", "player", "league_id", "position"]
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype("string")

        # 3. Types Numériques (Int64)
        int_cols = [
            "season_id", "team_id", "player_id",
            "matches", "minutes", "goals", "np_goals", "assists", "shots", 
            "key_passes", "yellow_cards", "red_cards", "height", "weight"
        ]
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("Int64")

        # 4. Types Décimaux (Float64)
        float_cols = ["xg", "np_xg", "xa", "xg_chain", "xg_buildup", "market_value_current", "popularity_score_current"]
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).round(4).astype("Float64")

        # 4. Standardisation des positions (Basé sur ton mapping)
        df = self._standardize_positions(df)

        # 5. Calcul de l'âge, contrat et detailed_positions
        df = self._process_metrics(df)

        return df

    def _standardize_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mappe les codes Understat/SofaScore vers des catégories claires."""
        """Standardise les codes de position."""
        if "position" not in df.columns:
            return df
        
        position_mapping = {
            "GK": {
                "primary_position": "Goalkeeper",
                "description": "Goalkeeper (starter)"
            },
            "GK S": {
                "primary_position": "Goalkeeper",
                "description": "Goalkeeper (substitute/secondary)"
            },
            "D": {
                "primary_position": "Defender",
                "description": "Defender (generic)"
            },
            "D S": {
                "primary_position": "Defender",
                "description": "Defender (secondary role / versatile)"
            },
            "D M": {
                "primary_position": "Defender",
                "description": "Defender / Midfielder (versatile)"
            },
            "D M S": {
                "primary_position": "Defender",
                "description": "Defender / Defensive Midfielder"
            },
            "D F M S": {
                "primary_position": "Defender",
                "description": "Defender / versatile (can play Midfield/Forward)"
            },
            "M": {
                "primary_position": "Midfielder",
                "description": "Midfielder (central)"
            },
            "M S": {
                "primary_position": "Midfielder",
                "description": "Midfielder (secondary/attacking)"
            },
            "F": {
                "primary_position": "Forward",
                "description": "Forward (generic)"
            },
            "F S": {
                "primary_position": "Forward",
                "description": "Striker / Centre Forward"
            },
            "F M": {
                "primary_position": "Forward",
                "description": "Forward / Midfielder (versatile)"
            },
            "F M S": {
                "primary_position": "Forward",
                "description": "Forward / Winger / Attacking Midfielder"
            },
            "S": {
                "primary_position": "Forward",
                "description": "Striker"
            }
        }
        
        def get_fallback_primary(pos):
            if not isinstance(pos, str): return "Midfielder"
            if "GK" in pos: return "Goalkeeper"
            if pos.startswith("F") or pos.startswith("S"): return "Forward"
            if pos.startswith("M"): return "Midfielder"
            if pos.startswith("D"): return "Defender"
            return "Midfielder"

        # Extraction de la position principale
        df["position_standard"] = df["position"].map(
            lambda x: position_mapping.get(x, {}).get("primary_position", get_fallback_primary(x))
        )
        
        # Extraction de la description détaillée
        df["position_description"] = df["position"].map(
            lambda x: position_mapping.get(x, {}).get("description", str(x))
        )
        
        return df
    

    def _process_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule l'âge,contrat et detailed_positions par rapport à la saison en une seule fois."""
        if "birth_ts" in df.columns and "season_id" in df.columns:
            # Conversion timestamp -> année de naissance
            # birth_ts est en secondes (SofaScore)
            df["birth_year"] = pd.to_datetime(df["birth_ts"], unit='s').dt.year
            
            # Calcul : Année de la saison (ex: 2024) - Année de naissance
            df["player_age_at_season"] = df["season_id"].astype(int) - df["birth_year"]
            
            # Nettoyage
            df = df.drop(columns=["birth_year"])
            # "ENG-Premier League" -> "ENG"
            df["country"] = df["league"].str.split("-").str[0]

        if "contract_until_ts_current" in df.columns:
            df["contract_end_date_current"] = pd.to_datetime(
                df["contract_until_ts_current"],
                unit="s",
                errors="coerce"
            ).dt.date
        
        if "detailed_positions_current" in df.columns:
            df["detailed_positions_current"] = df["detailed_positions_current"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

        return df
    

class FeatureEngineer:
    """Calcul des KPIs pour la détection de talents."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FeatureEngineer")
    
    def calculate_per_90_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule toutes les métriques par 90 minutes.
        
        Args:
            df: DataFrame avec colonnes minutes, goals, xg, etc.
        """
        df = df.copy()
        
        # Éviter division par zéro
        minutes_safe = df["minutes"].replace(0, np.nan)
        
        # Métriques per 90
        metrics_per_90 = {
            "goals_per_90": "goals",
            "xg_per_90": "xg",
            "np_goals_per_90": "np_goals",
            "np_xg_per_90": "np_xg",
            "assists_per_90": "assists",
            "xa_per_90": "xa",
            "shots_per_90": "shots",
            "key_passes_per_90": "key_passes"
        }
        
        for new_col, source_col in metrics_per_90.items():
            if source_col in df.columns:
                df[new_col] = (df[source_col] / minutes_safe * 90).round(3)
        
        # Involvement per 90
        if "xg_chain" in df.columns and "xg_buildup" in df.columns:
            df["involvement_per_90"] = (
                (df["xg_chain"] + df["xg_buildup"]) / minutes_safe * 90
            ).round(3)
        
        self.logger.info("Métriques per 90 calculées")
        return df
    
    def calculate_efficiency_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs d'efficacité."""
        df = df.copy()
        
        # Finishing efficiency
        if "goals" in df.columns and "xg" in df.columns:
            df["finishing_efficiency"] = (
                df["goals"] / df["xg"].replace(0, np.nan)
            ).round(3)
        
        # Non-penalty finishing
        if "np_goals" in df.columns and "np_xg" in df.columns:
            df["np_finishing_efficiency"] = (
                df["np_goals"] / df["np_xg"].replace(0, np.nan)
            ).round(3)
        
        # Playmaking efficiency
        if "assists" in df.columns and "xa" in df.columns:
            df["playmaking_efficiency"] = (
                df["assists"] / df["xa"].replace(0, np.nan)
            ).round(3)
        
        # Shot conversion
        if "goals" in df.columns and "shots" in df.columns:
            df["shot_conversion"] = (
                df["goals"] / df["shots"].replace(0, np.nan)
            ).round(3)
        
        self.logger.info("Métriques d'efficacité calculées")
        return df
    
    def calculate_collective_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs d'impact collectif."""
        df = df.copy()
        
        # Involvement index
        if "xg_chain" in df.columns and "xg_buildup" in df.columns:
            df["involvement_index"] = (df["xg_chain"] + df["xg_buildup"]).round(3)
        
        # Direct contribution
        if "goals" in df.columns and "assists" in df.columns:
            df["direct_contribution"] = df["goals"] + df["assists"]
        
        # Expected contribution
        if "xg" in df.columns and "xa" in df.columns:
            df["expected_contribution"] = (df["xg"] + df["xa"]).round(3)
        
        # Offensive volume
        if "shots" in df.columns and "key_passes" in df.columns:
            df["offensive_volume"] = df["shots"] + df["key_passes"]
        
        self.logger.info("Métriques collectives calculées")
        return df
    
    def calculate_value_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques de valeur marché."""
        df = df.copy()
        
        if "market_value_current" not in df.columns:
            return df
        
        mv_safe = df["market_value_current"].replace(0, np.nan)
        
        # Value per goal
        if "goals" in df.columns:
            df["value_per_goal"] = (mv_safe / df["goals"].replace(0, np.nan)).round(0)
        
        # Value per xG
        if "xg" in df.columns:
            df["value_per_xg"] = (mv_safe / df["xg"].replace(0, np.nan)).round(0)
        
        # Value per contribution
        if "direct_contribution" in df.columns:
            df["value_per_contribution"] = (
                mv_safe / df["direct_contribution"].replace(0, np.nan)
            ).round(0)
        
        self.logger.info("Métriques de valeur calculées")
        return df
    
    def apply_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applique toutes les transformations de features."""
        if df.empty: return df
        df = self.calculate_per_90_metrics(df)
        df = self.calculate_efficiency_metrics(df)
        df = self.calculate_collective_metrics(df)
        df = self.calculate_value_metrics(df)
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        return df
