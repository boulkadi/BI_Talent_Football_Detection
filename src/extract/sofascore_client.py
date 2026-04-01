import os
import json
import requests

# On récupère le chemin racine pour stocker le cache au même endroit que Understat
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SofaScoreClient:
    """
    Client for retrieving player information with local JSON caching.
    """

    BASE_URL = "https://www.sofascore.com/api/v1"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.sofascore.com/"
    }

    def __init__(self):
        # Initialisation du chemin du fichier de cache
        self.cache_path = os.path.join(BASE_DIR, "data", "sofascore_cache.json")
        self.cache = self._load_cache()
        
    def _load_cache(self):
        """Charge le cache depuis le fichier JSON. S'assure que le dossier existe."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Sauvegarde le cache en local."""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)

    def search_player(self, player_name: str):
        url = f"{self.BASE_URL}/search/all?q={player_name}"
        res = requests.get(url, headers=self.HEADERS, timeout=5)
        if res.status_code != 200:
            return None
        results = res.json().get("results", [])
        for r in results:
            if r.get("type") == "player":
                return r["entity"]["id"]
        return None

    def get_player_details(self, player_id: int):
        url = f"{self.BASE_URL}/player/{player_id}"
        res = requests.get(url, headers=self.HEADERS, timeout=5)
        if res.status_code != 200:
            return None
        return res.json().get("player", None)

    def get_player_info(self, player_name: str):
        """
        Récupère les infos, en vérifiant d'abord dans le cache local.
        """
        # 1. Vérification dans le cache (clé = nom du joueur)
        if player_name in self.cache:
            return self.cache[player_name]

        # 2. Si pas dans le cache, on fait l'appel API
        player_id = self.search_player(player_name)
        if not player_id:
            return None

        p_data = self.get_player_details(player_id)
        if not p_data:
            return None

        # 3. Préparation des données
        info = {
            'name_sofascore': p_data.get('name'),
            'birth_ts': p_data.get('dateOfBirthTimestamp'),
            'height': p_data.get('height'),
            'weight': p_data.get('weight'),
            'preferred_foot': p_data.get('preferredFoot'),
            'nationality': p_data.get('country', {}).get('name'),
            'position_current': p_data.get('position'),
            'detailed_positions_current': p_data.get('positionsDetailed', []),
            'market_value_current': p_data.get('proposedMarketValue'),
            'contract_until_ts_current': p_data.get('contractUntilTimestamp'),
            'popularity_score_current': p_data.get('userCount')
        }

        # 4. Mise à jour du cache et sauvegarde
        self.cache[player_name] = info
        self._save_cache()
        
        return info