import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Format attendu dans le .env : 
        # postgresql://user:password@host:port/dbname
        # self.db_url = os.getenv('DATABASE_URL') or "postgresql://football_user:football_pass@localhost:5432/football_db"
        # Sécurité : Par défaut, on se connecte à la base "sandbox" (football_airflow_db) 
        # exposée sur le port 5433 de la machine locale, pour ne jamais polluer la prod par erreur.
        self.db_url = os.getenv('DATABASE_URL') or "postgresql://airflow_worker:airflow_pass@localhost:5433/football_airflow_db"
        if not self.db_url:
            raise ValueError("Erreur : DATABASE_URL non trouvée dans le fichier .env")

        self.engine = create_engine(
            self.db_url,
            # Configuration optimisée pour Postgres
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )

    @contextmanager
    def session_scope(self):
        """Gestionnaire de transaction atomique (Tout ou rien)."""
        with self.engine.begin() as conn:  # .begin() gère le commit/rollback automatiquement
            try:
                yield conn
            except SQLAlchemyError as e:
                print(f"❌ Erreur SQL détectée : {e}")
                raise 

    def load_df(self, df, table_name, schema='public', if_exists='append'):
        """Chargement optimisé de DataFrame vers Postgres."""
        try:
            df.to_sql(
                name=table_name,
                con=self.engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                chunksize=1000,
                method='multi'  # Très important pour la vitesse sous Postgres
            )
            print(f" {len(df)} lignes insérées dans {schema}.{table_name}")
        except Exception as e:
            print(f" Échec du chargement : {e}")
            raise

    def upsert_df(self, df, table_name, schema, unique_keys):
        """
        Inserts data into Postgres using ON CONFLICT DO UPDATE.
        Creates a temporary table, loads data, then executes the upsert.
        Automatically adapts to the columns available in the DataFrame.
        """
        if df.empty:
            return
            
        temp_table = f"temp_{table_name}"
        
        # 1. Load into temp table
        df.to_sql(name=temp_table, con=self.engine, schema=schema, if_exists='replace', index=False)
        
        # 2. Build UPSERT query
        columns = [f'"{col}"' for col in df.columns]
        columns_str = ", ".join(columns)
        
        # Build SET clause for updates, excluding unique keys
        update_cols = [col for col in df.columns if col not in unique_keys]
        if update_cols:
            set_clause = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in update_cols])
            conflict_action = f"DO UPDATE SET {set_clause}"
        else:
            conflict_action = "DO NOTHING"
            
        unique_keys_str = ", ".join([f'"{key}"' for key in unique_keys])
        
        upsert_query = f"""
            INSERT INTO {schema}.{table_name} ({columns_str})
            SELECT {columns_str} FROM {schema}.{temp_table}
            ON CONFLICT ({unique_keys_str}) {conflict_action};
        """
        
        with self.session_scope() as conn:
            conn.execute(text(upsert_query))
            conn.execute(text(f"DROP TABLE IF EXISTS {schema}.{temp_table}"))
        print(f" UPSERT de {len(df)} lignes dans {schema}.{table_name} terminé.")

    def run_sql_file(self, filepath):
        """Exécute un fichier .sql (Initialisation de ton projet)."""
        with open(filepath, 'r') as f:
            query = f.read()
        with self.session_scope() as conn:
            conn.execute(text(query))
            print(f" Script exécuté avec succès : {filepath}")