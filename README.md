# Detect-Football-Talents

**Detect-Football-Talents** est une plateforme de data engineering avancée conçue pour l'extraction, la transformation, l'analyse et la visualisation des performances des joueurs de football en Europe. L'objectif de ce projet est de centraliser des données provenant de multiples sources (Understat, SofaScore) pour identifier des talents émergents ou sous-cotés via des indicateurs (KPIs) novateurs de performance.

---

## 🎬 Démonstration
 
Une présentation complète du pipeline ETL et du projet est disponible ici :
 
▶️ **[ETL Pipeline - Football Talent Detection (YouTube)](https://www.youtube.com/watch?v=JscKGW_byt4&t=129s)**
 
---

## 🏗️ Architecture
 
![Architecture & Stack Technique](.images_Football_Talents/project_workflow_stack_technique.svg)
 
---

## 📑 Table des matières
1. [Aperçu du Projet](#aperçu-du-projet)
2. [Stack Technique](#stack-technique)
3. [Architecture et Workflow ETL](#architecture-et-workflow-etl)
4. [Détail des Modules (Codebase)](#détail-des-modules-codebase)
5. [Schéma de Données (PostgreSQL)](#schéma-de-données-postgresql)
6. [Lancer le Projet (Docker / Local)](#lancer-le-projet-docker--local)
7. [Auteurs et Contributions](#auteurs-et-contributions)

---

## 🔍 Aperçu du Projet

Ce projet implémente un pipeline complet de la donnée (ETL) orchestré de bout en bout pour le traitement analytique : 
- **Extraction intelligente :** Moissonnage direct de statistiques avancées (xG, xA, etc.) via *Understat* et données contextuelles/financières via *SofaScore*.
- **Features Engineering :** Création d'indicateurs de performances rapportées à 90 minutes (Per 90 metrics), ratios d'efficacités (finishing, conversion), impact collectif et valeur marchande théorique.
- **Stockage de la donnée :** Un entrepôt de données robuste basé sur **PostgreSQL**, adoptant une modélisation en étoile (Star Schema) via clés de substitution (surrogates). 
- **Orchestration :** Gestion automatisée des rafraîchissements de données par **Apache Airflow** (Runs historiques et incrémentaux).
- **Dashboarding interactif :** Interface développée sous **Streamlit** pour la restitution visuelle de la donnée aux observateurs (scouts, fans, analystes).

---

## 🛠 Stack Technique

Le projet repose sur des outils modernes orientés Data Engineering, Analyse et Déploiement :

* **Langage principal :** Python (≥ 3.11)
* **Orchestration :** Apache Airflow (LocalExecutor)
* **Traitement & Analyse :** Pandas, Numpy, PyArrow
* **Extraction de données (Scraping/APIs) :** BeautifulSoup4, requests, lxml, soccerdata, cloudscraper
* **Base de données :** PostgreSQL (psycopg2, SQLAlchemy, asyncpg)
* **Visualisation :** Streamlit, Plotly
* **Infrastructure & Déploiement :** Docker, Docker Compose
* **Qualité de code (Dev) :** Black, Ruff, Pytest

---

## ⚙️ Architecture et Workflow ETL

Le workflow de données est conçu pour fonctionner de manière résiliente et est mis à jour par l'intermédiaire d'Airflow avec deux DAGs principaux :

1. **DAG - `football_etl_all_seasons` :** (Exécution manuelle) Permet le moissonnage et le chargement historique complet de l'ensemble des 5 grands championnats de la saison 2021/2022 à la saison en cours.
2. **DAG - `football_etl_weekly_update` :** (Automatisé chaque lundi à 03h00) Permet la mise à jour incrémentale (UPSERT) pour intégrer les matchs du week-end de la saison active.

### Les 3 phases de l'ETL :
1. **EXTRACT :** L'`Orchestrator` (`FootballDataOrchestrator`) récupère toutes les saisons et championnats depuis *Understat* puis enrichit individuellement chaque joueur depuis *SofaScore* en simulant un cache humain pour éviter les limites de requêtes. La donnée est stockée en brut (`raw_data.csv`).
2. **TRANSFORM :** Le `DataTransformer` normalise les chaînes, harmonise les positions (Regroupement des GKs, Midfielders, Attackers) et convertit les types. Ensuite, le `FeatureEngineer` ajoute les KPIs analytiques (goals_per_90, xg_per_90, finishing_efficiency, playmaking_efficiency, value_per_goal, etc.). La donnée est sauvegardée localement (`clean_data.csv`).
3. **LOAD :** Utilisation du `FootballLoader` associé au `DatabaseManager` pour s'insérer de manière propre (UPSERTS et Insertions standard) dans les tables relationnelles de la base PostgreSQL (Tables de Dimensions de de Faits).

---

## 📂 Détail des Modules (Codebase)

La structure de l'application (située principalement dans le dossier `src/`) est modulaire selon les principes du génie logiciel :

```text
detect-football-talents/
├── dags/                       # Scripts orchestrés par Apache Airflow
│   ├── etl_all_seasons_dag.py
│   └── etl_weekly_current_season_dag.py
├── data/                       # Espace conteneurisé géré par docker/Airflow (Cache/CSV temporaires)
├── docker/                     # Fichiers d'infrastructure
│   ├── docker-compose.yml      # Service Postgres, pgAdmin, Airflow Web/Scheduler/DB
│   └── Dockerfile
├── shemas.sql                  # Fichiers de définitions SQL (Création des bases)
├── src/
│   ├── database/               # Gestionnaire de connexion DB (`db_manager.py`)
│   ├── database_sql/           # Scripts SQL initiaux
│   ├── extract/                # Extractions APIs (SofaScore, Understat, Orchestrateur global)
│   ├── transform/              # Transformation des données et ingénierie de features (KPIs)
│   ├── load/                   # Import des données vers la BD via requêtes et ORM
│   ├── dashboard/              # Application Streamlit (`talent_dashboard.py`)
│   └── Scripts/                # Outils CLI pour valider ou exécuter manuellement l'ETL/les requêtes
└── pyproject.toml              # Dépendances Python et configurations (Black, Ruff)
```

---

## 📊 Schéma de Données (PostgreSQL)

La donnée finale est chargée dans des tables optimisées pour la lecture analytique :

* **`dim_league` :** Informations structurelles sur le championnat.
* **`dim_season` :** Informations de saisons footballistiques temporelles.
* **`dim_team` :** Données sur les équipes.
* **`dim_player` :** Données référentielles des joueurs, informations biographiques (naissance, etc.) et évaluations de marchés.
* **`fact_performance` :** Table des faits centralisée. Contient l'historique complet (et calculé) des performances des joueurs sur une saison donnée. Relie toutes les dimensions par des IDs et intègre les données avancées telles que `xg`, `xa`, `efficiency`, `per_90`, etc.

*Les tables utilisent un système d'UPSERT basé sur les identifiants originels du joueur/équipe pour maintenir une unicité parfaite tout en permettant les ajouts temps-réel.*

---

## 🚀 Lancer le Projet (Docker / Local)

Le système est déployé intégralement sur Docker pour éviter tout conflit de version local et monter les bases de données simultanément :

### 1. Démarrer l'infrastructure
Positionnez-vous dans le répertoire `docker` et lancez la suite applicative :
```bash
cd docker
docker-compose up -d --build
```
*Le flag `--build` assure que l'image Airflow contenant nos dépendances spécifiques se rafraîchisse.*

### 2. Services Accessibles
Une fois les conteneurs démarrés et la phase `airflow-init` terminée (prend environ une minute) :
* **Apache Airflow Webserver :** `http://localhost:8080/`
  *(Logins : admin / admin)*
* **PostgreSQL pgAdmin :** `http://localhost:8081/`
  *(Logins : admin@admin.com / admin)*

### 3. Exécuter via Airflow
Depuis l'interface Web Airflow, vous trouverez 2 DAGs.
Basculez le bouton afin d'activer le DAG `football_etl_all_seasons`, et cliquez sur "Trigger DAG" pour procéder à l'historisation d'une base vierge.

### 4. Lancer le Dashboard Streamlit (Indépendant)
Assurez-vous que l'environnement virtuel Python a les dépendances installées (`uv.lock` ou environnement existant). Configurez votre `DATABASE_URL` puis exécutez de façon classique :
```bash
streamlit run src/dashboard/talent_dashboard.py
```

---

## ✒️ Auteurs et Contributions
Projet maintenu et développé dans le cadre d'un workflow de détection des talents footballistiques moderne.
Les contributions, rapports de bugs et PRs sont les bienvenus via la gestion d'issues du repository.
