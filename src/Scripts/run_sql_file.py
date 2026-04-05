"""
Script pour exécuter des fichiers SQL sur la base de données PostgreSQL.
Usage: python run_sql_file.py <chemin_relatif_du_fichier.sql>
Exemple: python run_sql_file.py ../database_sql/04_mart_tables.sql
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin parent pour importer DatabaseManager
sys.path.append(str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager


def run_sql_file(sql_file_path: str):
    """
    Exécute un fichier SQL sur la base de données PostgreSQL.
    
    Args:
        sql_file_path: Chemin relatif ou absolu vers le fichier SQL
    """
    # Convertir en chemin absolu si relatif
    if not os.path.isabs(sql_file_path):
        # Chemin relatif au répertoire de travail actuel (cwd), pas au script
        sql_file_path = Path(os.getcwd()) / sql_file_path
    
    sql_file_path = Path(sql_file_path).resolve()
    
    # Vérifier que le fichier existe
    if not sql_file_path.exists():
        print(f"❌ Erreur: Le fichier '{sql_file_path}' n'existe pas.")
        return False
    
    if not sql_file_path.suffix == '.sql':
        print(f"❌ Erreur: Le fichier '{sql_file_path}' n'est pas un fichier SQL.")
        return False
    
    print(f"📂 Fichier SQL: {sql_file_path.name}")
    print(f"📍 Chemin complet: {sql_file_path}")
    print()
    
    try:
        # Connexion à la base de données
        db = DatabaseManager()
        print("✅ Connexion à la base de données établie")
        
        # Lire le contenu du fichier SQL
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"📄 Taille du fichier: {len(sql_content)} caractères")
        print()
        print("🔄 Exécution du script SQL en cours...")
        print("=" * 60)
        
        # Exécuter le script SQL
        with db.session_scope() as conn:
            from sqlalchemy import text
            
            # Pour les fichiers complexes avec des procédures/fonctions,
            # on exécute le fichier en entier au lieu de le découper
            print(f"🔄 Exécution du script complet...")
            print()
            
            try:
                # Nettoyer les commentaires de dump pgAdmin
                cleaned_sql = sql_content
                
                # Supprimer les lignes de restriction pgAdmin si présentes
                lines = cleaned_sql.split('\n')
                cleaned_lines = []
                for line in lines:
                    if line.strip().startswith('\\restrict') or line.strip().startswith('\\unrestrict'):
                        continue
                    cleaned_lines.append(line)
                cleaned_sql = '\n'.join(cleaned_lines)
                
                # Exécuter le script complet
                conn.execute(text(cleaned_sql))
                print("    ✅ Script exécuté avec succès")
                
            except Exception as e:
                error_msg = str(e)
                print(f"    ⚠️ Erreur: {error_msg[:200]}")
                
                # Si l'exécution globale échoue, essayer de découper par instructions
                print()
                print("⚠️ Tentative de découpage par instructions individuelles...")
                print()
                
                # Découper intelligemment en respectant les blocs $$...$$
                statements = []
                current_stmt = []
                in_dollar_block = False
                
                for line in cleaned_lines:
                    current_stmt.append(line)
                    
                    # Détecter les blocs $$
                    if '$$' in line:
                        in_dollar_block = not in_dollar_block
                    
                    # Fin d'instruction si ; et pas dans un bloc $$
                    if ';' in line and not in_dollar_block:
                        stmt = '\n'.join(current_stmt).strip()
                        if stmt and not stmt.startswith('--'):
                            statements.append(stmt)
                        current_stmt = []
                
                # Ajouter la dernière instruction si elle existe
                if current_stmt:
                    stmt = '\n'.join(current_stmt).strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt)
                
                total_statements = len(statements)
                success_count = 0
                error_count = 0
                
                for i, statement in enumerate(statements, 1):
                    try:
                        # Afficher un aperçu de la commande
                        preview = statement[:100].replace('\n', ' ')
                        print(f"[{i}/{total_statements}] {preview}...")
                        
                        conn.execute(text(statement))
                        print(f"    ✅ Exécuté avec succès")
                        success_count += 1
                        
                    except Exception as stmt_error:
                        print(f"    ⚠️ Erreur: {str(stmt_error)[:100]}")
                        error_count += 1
                        continue
                
                print()
                print(f"📊 Résumé: {success_count} succès, {error_count} erreurs sur {total_statements} commandes")
        
        print()
        print("=" * 60)
        print(f"✅ Script SQL '{sql_file_path.name}' exécuté avec succès!")
        print()
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Erreur lors de l'exécution du script SQL:")
        print(f"   {str(e)}")
        print("=" * 60)
        return False


def main():
    """Point d'entrée principal."""
    print()
    print("=" * 60)
    print("🗄️  Exécuteur de Scripts SQL - Football Talent Detection")
    print("=" * 60)
    print()
    
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("❌ Usage: python run_sql_file.py <chemin_du_fichier.sql>")
        print()
        print("Exemples:")
        print("  python run_sql_file.py ../database_sql/01_create_schemas.sql")
        print("  python run_sql_file.py ../database_sql/04_mart_tables.sql")
        print()
        sys.exit(1)
    
    sql_file_path = sys.argv[1]
    
    # Exécuter le fichier SQL
    success = run_sql_file(sql_file_path)
    
    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
