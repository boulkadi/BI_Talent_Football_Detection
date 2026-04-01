from src.extract.understat_extractor import UnderstatExtractor
from src.extract.sofascore_client import SofaScoreClient


# Test Understat
extractor = UnderstatExtractor(
    league="ESP-La Liga",
    season="2526"
)

df = extractor.extract()

print(df.head())


# Test SofaScore
client = SofaScoreClient()

player = client.get_player_info("Pedri")

print(player)
