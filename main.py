import requests
from datetime import datetime, date
from pybaseball import statcast_batter, statcast_pitcher, pitching_stats

 

teams = {
    "arizona diamondbacks": 109,
    "atlanta braves": 144,
    "baltimore orioles": 110,
    "boston red sox": 111,
    "chicago white sox": 145,
    "chicago cubs": 112,
    "cincinnati reds": 113,
    "cleveland guardians": 114,
    "colorado rockies": 115,
    "detroit tigers": 116,
    "houston astros": 117,
    "kansas city royals": 118,
    "los angeles angels": 108,
    "los angeles dodgers": 119,
    "miami marlins": 146,
    "milwaukee brewers": 158,
    "minnesota twins": 142,
    "new york mets": 121,
    "new york yankees": 147,
    "oakland athletics": 133,
    "philadelphia phillies": 143,
    "pittsburgh pirates": 134,
    "san diego padres": 135,
    "san francisco giants": 137,
    "seattle mariners": 136,
    "st. louis cardinals": 138,
    "tampa bay rays": 139,
    "texas rangers": 140,
    "toronto blue jays": 141,
    "washington nationals": 120
}

pteam_input = input("Enter bullpen team name: ").lower()
pteam_id = teams[pteam_input]

bteam_input = input("Enter batters team name: ").lower()
bteam_id = teams[bteam_input]

presponse = requests.get(f"https://statsapi.mlb.com/api/v1/teams/{pteam_id}/roster?rosterType=fullRoster&season=2025")
proster = presponse.json()

bresponse = requests.get(f"https://statsapi.mlb.com/api/v1/teams/{bteam_id}/roster?rosterType=fullRoster&season=2025")
broster = bresponse.json()

batter_inputs = [
  input("Enter batter 1 (First Last): ").lower(),
  input("Enter batter 2 (First Last): ").lower(),
  input("Enter batter 3 (First Last): ").lower()
]

batter_ids = []
for name in batter_inputs:
    for player in broster["roster"]:
        if player["person"]["fullName"].lower() == name:
            batter_ids.append(player["person"]["id"])
            break

batter1_id = batter_ids[0]
batter2_id = batter_ids[1]
batter3_id = batter_ids[2]

from pybaseball import pitching_stats
stats = pitching_stats(2025, 2025, qual=1)


def get_reliable_season(player_id):
    pyeardata = statcast_pitcher('2025-03-27', '2025-09-28', player_id=player_id)
    if len(pyeardata) >= 400:
        return pyeardata
    pyeardata = statcast_pitcher('2024-03-28', '2024-09-29', player_id=player_id)
    if len(pyeardata) >= 400:
        return pyeardata
    pyeardata = statcast_pitcher('2023-03-29', '2023-09-30', player_id=player_id)
    if len(pyeardata) >= 400:
        return pyeardata
    return None

def get_batter_profile(player_id):
    bdata = statcast_batter('2025-03-27', '2025-09-28', player_id=player_id)

    outside = bdata[bdata["zone"].isin([11, 12, 13, 14])]
    outside_swings = outside[outside["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"])]
    bchase_rate = len(outside_swings) / len(outside)
    bchase_norm = bchase_rate

    bwhiffs = bdata[bdata["description"].isin(["swinging_strike", "swinging_strike_blocked"])]
    swings = bdata[bdata["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"])]
    bwhiffs_by_zone = bwhiffs.groupby("zone").size()
    swings_by_zone = swings.groupby("zone").size()
    bwhiff_percent_by_zone = bwhiffs_by_zone / swings_by_zone

    bwoba_data = bdata[bdata["woba_denom"] == 1]
    bxwoba_by_zone = bwoba_data.groupby("zone")["estimated_woba_using_speedangle"].mean()

    bxwoba_norm = 1 - (bxwoba_by_zone - bxwoba_by_zone.min()) / (bxwoba_by_zone.max() - bxwoba_by_zone.min())

    bwhiff_norm = (bwhiff_percent_by_zone - bwhiff_percent_by_zone.min()) / (bwhiff_percent_by_zone.max() - bwhiff_percent_by_zone.min())

    return bxwoba_norm, bwhiff_norm, bchase_norm


def get_pitcher_profile(player_id):
    pdata = get_reliable_season(player_id)
    if pdata is None:
        return None, None, None

    outside = pdata[pdata["zone"].isin([11, 12, 13, 14])]
    outside_swings = outside[outside["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"])]
    pchase_rate = len(outside_swings) / len(outside)
    pchase_norm = pchase_rate

    pwhiffs = pdata[pdata["description"].isin(["swinging_strike", "swinging_strike_blocked"])]
    swings = pdata[pdata["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"])]
    pwhiffs_by_zone = pwhiffs.groupby("zone").size()
    swings_by_zone = swings.groupby("zone").size()
    pwhiff_percent_by_zone = pwhiffs_by_zone / swings_by_zone

    pwoba_data = pdata[pdata["woba_denom"] == 1]
    pxwoba_by_zone = pwoba_data.groupby("zone")["estimated_woba_using_speedangle"].mean()

    pxwoba_norm = 1 - ((pxwoba_by_zone - pxwoba_by_zone.min()) / (pxwoba_by_zone.max() - pxwoba_by_zone.min()))

    pwhiff_norm = (pwhiff_percent_by_zone - pwhiff_percent_by_zone.min()) / (pwhiff_percent_by_zone.max() - pwhiff_percent_by_zone.min())

    return pxwoba_norm, pwhiff_norm, pchase_norm



def matchup_score(bxwoba_norm, bwhiff_norm, bchase_norm, pxwoba_norm, pwhiff_norm, pchase_norm):
    zone_score = (bxwoba_norm * pxwoba_norm) + (bwhiff_norm * pwhiff_norm)
    chase_contribution = (bchase_norm * pchase_norm)
    return zone_score.sum() + chase_contribution



bxwoba_norm1, bwhiff_norm1, bchase_norm1 = get_batter_profile(batter1_id)
bxwoba_norm2, bwhiff_norm2, bchase_norm2 = get_batter_profile(batter2_id)
bxwoba_norm3, bwhiff_norm3, bchase_norm3 = get_batter_profile(batter3_id)


all_players_response = requests.get("https://statsapi.mlb.com/api/v1/sports/1/players?season=2025")
all_players = all_players_response.json()
hand_lookup = {p["id"]: p["pitchHand"]["code"] for p in all_players["people"]}



results = []

for player in proster["roster"]:
 if player["position"]["name"] == "Pitcher":
  player_id = player["person"]["id"]
  player_stats = stats[stats["Name"] == player["person"]["fullName"]]
  if not player_stats.empty:
   if player_stats["GS"].values[0] == player_stats["G"].values[0]:
    continue
  response = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&group=pitching&season=2025")
  data = response.json()
  last_outing = data["stats"][0]["splits"][-1]
  last_pitched = datetime.strptime(last_outing["date"], "%Y-%m-%d").date()
  days_ago = (date.today() - last_pitched).days
  total_pitches = last_outing["stat"]["numberOfPitches"]
  if days_ago > 3:
   availability = "green"
  elif 3 >= days_ago > 1:
   if 40 >= total_pitches >= 0:
    availability = "green"
   elif 60 >= total_pitches > 40:
    availability = "yellow"
   else:
    availability = "red"
  else:
   if 15 >= total_pitches >= 0:
    availability = "yellow"
   else:
    availability = "red"
  pxwoba_norm, pwhiff_norm, pchase_norm = get_pitcher_profile(player_id)
  if pxwoba_norm is None:
    print("Not enough data for this pitcher")
    continue
  score1 = matchup_score(bxwoba_norm1, bwhiff_norm1, bchase_norm1, pxwoba_norm, pwhiff_norm, pchase_norm)
  score2 = matchup_score(bxwoba_norm2, bwhiff_norm2, bchase_norm2, pxwoba_norm, pwhiff_norm, pchase_norm)
  score3 = matchup_score(bxwoba_norm3, bwhiff_norm3, bchase_norm3, pxwoba_norm, pwhiff_norm, pchase_norm)
  total_score = (score1 + score2 * 0.65 + score3 * 0.40) / 2.05
  results.append((
    player["jerseyNumber"],
    player["person"]["fullName"],
    hand_lookup[player_id],
    availability,
    total_score
))


results.sort(reverse=True, key=lambda x: x[4])
for jersey, name, hand, availability, score in results:
    print(f"#{jersey} {name} {hand} {availability} {round(score, 3)}")