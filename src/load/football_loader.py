import pandas as pd
import os
from sqlalchemy import text
from src.database.db_manager import DatabaseManager

CURRENT_SEASON = os.getenv('CURRENT_SEASON') or 2025 

class FootballLoader:
    def __init__(self, db: DatabaseManager):
        self.db = db
        
    def _filter_df_for_table(self, df, schema, table_name):
        """Filtre le DataFrame pour ne garder que les colonnes qui existent dans la table SQL."""
        query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = '{table_name}'
        """
        with self.db.engine.connect() as conn:
            valid_columns = [row[0] for row in conn.execute(text(query)).fetchall()]
            
        # Garder uniquement les colonnes du DF qui existent en base
        cols_to_keep = [col for col in df.columns if col in valid_columns]
        return df[cols_to_keep].copy()

    def load_raw_data(self, df_raw):
        """Remplit la table brute."""
        df_target = self._filter_df_for_table(df_raw, 'raw', 'player_stats')
        self.db.load_df(df_target, 'player_stats', schema='raw', if_exists='replace')

    def load_raw_data_current_season(self, df_raw):
        """Mise à jour des données brutes de la saison actuelle."""
        with self.db.session_scope() as conn:
            # On supprime les anciennes données de cette saison dans le raw
            conn.execute(
                text("DELETE FROM raw.player_stats WHERE season_id = :s"),
                {"s": str(CURRENT_SEASON)}
            )
        # On insère les nouvelles
        df_target = self._filter_df_for_table(df_raw, 'raw', 'player_stats')
        self.db.load_df(df_target, 'player_stats', schema='raw', if_exists='append')

    def load_dimensions(self, df_clean):
        """Remplit les dimensions staging en utilisant UPSERT pour éviter les doublons."""
        # --- DIM_LEAGUE ---
        if 'league_id' in df_clean.columns and 'league' in df_clean.columns:
            cols = ['league_id', 'league']
            if 'country' in df_clean.columns: cols.append('country')
            
            # On drop_duplicates sur l'ensemble de ces colonnes pour avoir une liste restreinte très rapide
            df_league = df_clean[cols].drop_duplicates().copy()
            df_league = df_league.dropna(subset=['league_id']).drop_duplicates(subset=['league_id'], keep='last')
            df_league = self._filter_df_for_table(df_league, 'staging', 'dim_league')
            if not df_league.empty:
                self.db.upsert_df(df_league, 'dim_league', schema='staging', unique_keys=['league_id'])

        # --- DIM_SEASON ---
        if 'season_id' in df_clean.columns and 'season' in df_clean.columns:
            # On prend juste un couple (id, nom) unique
            df_season = df_clean[['season_id', 'season']].drop_duplicates().copy()
            df_season = df_season.dropna(subset=['season_id'])
            df_season = self._filter_df_for_table(df_season, 'staging', 'dim_season')
            if not df_season.empty:
                self.db.upsert_df(df_season, 'dim_season', schema='staging', unique_keys=['season_id'])

        # --- DIM_TEAM ---
        if 'team_id' in df_clean.columns and 'team' in df_clean.columns:
            cols = ['team_id', 'team']
            if 'league_id' in df_clean.columns: cols.append('league_id')
            if 'country' in df_clean.columns: cols.append('country')
                
            df_team = df_clean[cols].drop_duplicates().copy()
            df_team = df_team.dropna(subset=['team_id']).drop_duplicates(subset=['team_id'], keep='last')
            df_team = self._filter_df_for_table(df_team, 'staging', 'dim_team')
            if not df_team.empty:
                self.db.upsert_df(df_team, 'dim_team', schema='staging', unique_keys=['team_id'])

        # --- DIM_PLAYER ---
        if 'player_id' in df_clean.columns and 'player' in df_clean.columns:
            player_cols = ['player_id', 'player', 'name_sofascore', 'nationality', 'birth_year', 'height', 'weight', 'preferred_foot', 'position_standard', 'position_description', 'detailed_positions_current', 'position_current']
            available_player_cols = [c for c in player_cols if c in df_clean.columns]
            
            df_player = df_clean[available_player_cols].drop_duplicates().copy()
            df_player = df_player.dropna(subset=['player_id']).drop_duplicates(subset=['player_id'], keep='last')
            df_player = self._filter_df_for_table(df_player, 'staging', 'dim_player')
            if not df_player.empty:
                self.db.upsert_df(df_player, 'dim_player', schema='staging', unique_keys=['player_id'])
        
        # --- FACT_PERFORMANCE ---
        # Exclure les dimensions statiques qui vont dans les autres tables, on garde tout le reste (notamment toutes les stats du df)
        exclude = ['league', 'season','player', 'team',  'position', 'name_sofascore', 'nationality', 'preferred_foot', 'position_standard', 'position_description', 'detailed_positions_current', 'country', 'birth_year', 'height', 'weight']
        fact_cols = [c for c in df_clean.columns if c not in exclude]
        
        df_fact = df_clean[fact_cols].copy()
        df_fact = self._filter_df_for_table(df_fact, 'staging', 'fact_performance')
        
        # Unique keys pour facts: player_id, team_id, season_id, league_id
        unique_keys = ['player_id', 'team_id', 'season_id', 'league_id']
        
        # S'assurer que les clés uniques nécessaires sont là pour l'upsert
        if all(key in df_fact.columns for key in unique_keys):
            # Ensure unique grain avant l'UPSERT
            df_fact = df_fact.dropna(subset=unique_keys).drop_duplicates(subset=unique_keys, keep='last')
            self.db.upsert_df(df_fact, 'fact_performance', schema='staging', unique_keys=unique_keys)

    def load_dimensions_current_season(self, df_clean):
        """Idem que load_dimensions, le UPSERT gère nativement la mise à jour (DO UPDATE)."""
        self.load_dimensions(df_clean)