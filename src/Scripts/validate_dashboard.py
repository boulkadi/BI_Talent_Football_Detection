"""
Script de validation du dashboard avant lancement.
Vérifie les imports, syntaxe, et connexion DB.
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("🔍 VALIDATION DU DASHBOARD")
print("=" * 60)
print()

# 1. Vérifier les imports
print("1️⃣ Vérification des imports...")
try:
    import streamlit
    print("   ✅ streamlit")
except ImportError as e:
    print(f"   ❌ streamlit: {e}")
    print("   → Installez avec: pip install streamlit")

try:
    import pandas
    print("   ✅ pandas")
except ImportError as e:
    print(f"   ❌ pandas: {e}")

try:
    import plotly
    print("   ✅ plotly")
except ImportError as e:
    print(f"   ❌ plotly: {e}")
    print("   → Installez avec: pip install plotly")

try:
    sys.path.append(str(Path(__file__).parent.parent))
    from database.db_manager import DatabaseManager
    print("   ✅ DatabaseManager")
except ImportError as e:
    print(f"   ❌ DatabaseManager: {e}")

print()

# 2. Vérifier la syntaxe du dashboard
print("2️⃣ Vérification de la syntaxe...")
dashboard_path = Path(__file__).parent / "dashboard" / "talent_dashboard.py"

if not dashboard_path.exists():
    print(f"   ❌ Fichier non trouvé: {dashboard_path}")
else:
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            compile(f.read(), str(dashboard_path), 'exec')
        print(f"   ✅ Syntaxe Python valide")
    except SyntaxError as e:
        print(f"   ❌ Erreur de syntaxe: {e}")
        print(f"      Ligne {e.lineno}: {e.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

print()

# 3. Vérifier la connexion à la base de données
print("3️⃣ Vérification de la connexion PostgreSQL...")
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from database.db_manager import DatabaseManager
    
    db = DatabaseManager()
    with db.engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("   ✅ Connexion PostgreSQL réussie")
except Exception as e:
    print(f"   ❌ Erreur de connexion: {e}")
    print("   → Assurez-vous que PostgreSQL est lancé: docker-compose up -d")

print()

# 4. Vérifier les vues mart
print("4️⃣ Vérification des vues mart...")
try:
    from database.db_manager import DatabaseManager
    import pandas as pd
    
    db = DatabaseManager()
    vues = [
        "mart.vw_player_scouting_profile",
        "mart.vw_undervalued_talents",
        "mart.vw_team_offensive_efficiency"
    ]
    
    for vue in vues:
        try:
            with db.engine.connect() as conn:
                result = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {vue}", conn)
                count = result['cnt'].iloc[0]
                print(f"   ✅ {vue}: {count} lignes")
        except Exception as e:
            print(f"   ❌ {vue}: {str(e)[:50]}")
            
except Exception as e:
    print(f"   ❌ Impossible de vérifier les vues: {e}")

print()

# 5. Résumé
print("=" * 60)
print("📋 RÉSUMÉ")
print("=" * 60)
print()
print("✅ Si tous les tests passent, lancez le dashboard avec:")
print("   streamlit run src/dashboard/talent_dashboard.py")
print()
print("❌ Si des erreurs apparaissent:")
print("   1. Installez les dépendances manquantes")
print("   2. Lancez PostgreSQL: cd docker && docker-compose up -d")
print("   3. Créez les vues mart: python src/Scripts/run_sql_file.py src/database_sql/04_mart_tables.sql")
print()
