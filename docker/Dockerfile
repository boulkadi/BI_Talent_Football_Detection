# Utilisation de Python 3.12 avec Airflow 2.9.1
FROM apache/airflow:2.9.1-python3.12

USER root
# Dépendances système pour psycopg2, lxml et les outils de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Installation de UV (le gestionnaire que tu utilises)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

USER airflow
WORKDIR /opt/airflow

# Copie des fichiers de dépendances depuis la racine (via le contexte de build)
COPY pyproject.toml uv.lock ./

# Installation synchronisée : --system installe dans le python 3.12 du container
RUN uv pip install --system -r pyproject.toml