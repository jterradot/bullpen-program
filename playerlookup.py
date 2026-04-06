
import requests

r = requests.get("https://statsapi.mlb.com/api/v1/teams/147/stats?stats=season&group=pitching&season=2025")
data = r.json()
print(data["stats"][0]["splits"][0])
