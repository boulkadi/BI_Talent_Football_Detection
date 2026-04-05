"""
Script de diagnostic pour vérifier les données dans la base de données.
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin parent pour importer DatabaseManager
sys.path.append(str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
import pandas as pd

def diagnose():
    """Diagnostic complet de la base de données."""
    
    print("=" * 60)
    print("🔍 DIAGNOSTIC - Base de Données Football")
    print("=" * 60)
    print()
    
    db = DatabaseManager()
    
    # 1. Vérifier les tables raw
    print("📊 1. TABLE RAW")
    print("-" * 60)
    query_raw = "SELECT COUNT(*) as total FROM raw.player_stats"
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(query_raw, conn)
            print(f"✅ raw.player_stats: {result['total'].iloc[0]} lignes")
    except Exception as e:
        print(f"❌ Erreur raw.player_stats: {e}")
    print()
    
    # 2. Vérifier les dimensions staging
    print("📊 2. DIMENSIONS STAGING")
    print("-" * 60)
    
    dimensions = [
        "staging.dim_league",
        "staging.dim_season", 
        "staging.dim_team",
        "staging.dim_player"
    ]
    
    for dim in dimensions:
        query = f"SELECT COUNT(*) as total FROM {dim}"
        try:
            with db.engine.connect() as conn:
                result = pd.read_sql(query, conn)
                print(f"✅ {dim}: {result['total'].iloc[0]} lignes")
        except Exception as e:
            print(f"❌ Erreur {dim}: {str(e)[:50]}")
    print()
    
    # 3. Vérifier fact_performance
    print("📊 3. TABLE DE FAITS")
    print("-" * 60)
    query_fact = """
    SELECT 
        COUNT(*) as total_lignes,
        COUNT(DISTINCT player_id) as total_joueurs,
        SUM(goals) as total_goals,
        SUM(assists) as total_assists,
        AVG(goals_per_90) as avg_goals_per_90,
        COUNT(CASE WHEN goals > 0 THEN 1 END) as lignes_avec_goals
    FROM staging.fact_performance
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(query_fact, conn)
            print(f"✅ staging.fact_performance:")
            print(f"   - Total lignes: {result['total_lignes'].iloc[0]}")
            print(f"   - Joueurs uniques: {result['total_joueurs'].iloc[0]}")
            print(f"   - Total goals: {result['total_goals'].iloc[0]}")
            print(f"   - Total assists: {result['total_assists'].iloc[0]}")
            print(f"   - Moy. goals/90: {result['avg_goals_per_90'].iloc[0]:.2f}")
            print(f"   - Lignes avec goals > 0: {result['lignes_avec_goals'].iloc[0]}")
    except Exception as e:
        print(f"❌ Erreur fact_performance: {e}")
    print()
    
    # 4. Vérifier les vues mart
    print("📊 4. VUES MART")
    print("-" * 60)
    
    vues = [
        "mart.vw_player_scouting_profile",
        "mart.vw_undervalued_talents",
        "mart.vw_team_offensive_efficiency"
    ]
    
    for vue in vues:
        query = f"SELECT COUNT(*) as total FROM {vue}"
        try:
            with db.engine.connect() as conn:
                result = pd.read_sql(query, conn)
                print(f"✅ {vue}: {result['total'].iloc[0]} lignes")
        except Exception as e:
            print(f"❌ Erreur {vue}: {str(e)[:80]}")
    print()
    
    # 5. Échantillon de données
    print("📊 5. ÉCHANTILLON DE DONNÉES")
    print("-" * 60)
    query_sample = """
    SELECT 
        p.player,
        p.position_standard,
        f.goals,
        f.assists,
        f.minutes,
        f.goals_per_90
    FROM staging.fact_performance f
    JOIN staging.dim_player p ON f.player_id = p.player_id
    LIMIT 10
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(query_sample, conn)
            if len(result) > 0:
                print("✅ Échantillon de 10 joueurs:")
                print(result.to_string(index=False))
            else:
                print("⚠️ Aucune donnée trouvée dans fact_performance")
    except Exception as e:
        print(f"❌ Erreur échantillon: {e}")
    print()
    
    # 6. Vérifier les filtres du dashboard
    print("📊 6. TEST DES FILTRES DU DASHBOARD")
    print("-" * 60)
    query_filtered = """
    SELECT COUNT(*) as total
    FROM mart.vw_player_scouting_profile
    WHERE minutes >= 450
      AND goals > 0
      AND position IS NOT NULL
      AND nationality IS NOT NULL
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(query_filtered, conn)
            print(f"Avec filtres du dashboard: {result['total'].iloc[0]} joueurs")
            
            # Sans les filtres restrictifs
            query_no_filter = "SELECT COUNT(*) as total FROM mart.vw_player_scouting_profile WHERE minutes >= 450"
            result_no_filter = pd.read_sql(query_no_filter, conn)
            print(f"Sans filtres goals/position: {result_no_filter['total'].iloc[0]} joueurs")
    except Exception as e:
        print(f"❌ Erreur test filtres: {e}")
    print()
    
    print("=" * 60)
    print("✅ Diagnostic terminé")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()
