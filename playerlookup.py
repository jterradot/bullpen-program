
import requests
response = requests.get("https://statsapi.mlb.com/api/v1/teams/144/roster?rosterType=fullRoster&season=2025")
roster = response.json()
for player in roster["roster"]:
    print(player["person"]["fullName"].lower())