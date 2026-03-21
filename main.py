import requests
from datetime import datetime, date
from pybaseball import statcast_batter, statcast_pitcher, pitching_stats
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def pget_reliable_season(player_id):
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

def bget_reliable_season(player_id):
    byeardata = statcast_batter('2025-03-27', '2025-09-28', player_id=player_id)
    if len(byeardata) >= 400:
        return byeardata
    byeardata = statcast_batter('2024-03-28', '2024-09-29', player_id=player_id)
    if len(byeardata) >= 400:
        return byeardata
    byeardata = statcast_batter('2023-03-29', '2023-09-30', player_id=player_id)
    if len(byeardata) >= 400:
        return byeardata
    return None

def get_batter_profile(player_id):
    bdata = bget_reliable_season(player_id)
    if bdata is None:
        return None, None, None

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
    pdata = pget_reliable_season(player_id)
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



def process_pitcher(player):
    if player["position"]["name"] != "Pitcher":
        return None
    player_id = player["person"]["id"]
    player_stats = stats[stats["Name"] == player["person"]["fullName"]]
    if not player_stats.empty:
        if player_stats["GS"].values[0] == player_stats["G"].values[0]:
            return None
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
        return None
    weights = [1.0, 0.65, 0.40]
    total_score = 0
    for i, (bxwoba, bwhiff, bchase) in enumerate(batter_profiles):
        total_score += matchup_score(bxwoba, bwhiff, bchase, pxwoba_norm, pwhiff_norm, pchase_norm) * weights[i]
    total_score /= sum(weights[:len(batter_profiles)])
    return (
        player["jerseyNumber"],
        player["person"]["fullName"],
        hand_lookup[player_id],
        availability,
        total_score
    )
            

def run_analysis(pteam, bteam, batter1, batter2, batter3):
    global stats, batter_profiles, hand_lookup

    pteam_id = teams.get(pteam.lower().strip())
    if not pteam_id:
        return {"error": f"'{pteam}' is not a valid team name"}

    bteam_id = teams.get(bteam.lower().strip())
    if not bteam_id:
        return {"error": f"'{bteam}' is not a valid team name"}

    presponse = requests.get(f"https://statsapi.mlb.com/api/v1/teams/{pteam_id}/roster?rosterType=fullRoster&season=2025")
    proster = presponse.json()

    bresponse = requests.get(f"https://statsapi.mlb.com/api/v1/teams/{bteam_id}/roster?rosterType=fullRoster&season=2025")
    broster = bresponse.json()

    batter_ids = []
    for name in [batter1.lower().strip(), batter2.lower().strip(), batter3.lower().strip()]:
        found = False
        for player in broster["roster"]:
            if player["person"]["fullName"].lower() == name:
                batter_ids.append(player["person"]["id"])
                found = True
                break
        if not found:
            return {"error": f"'{name}' not found on {bteam} roster"}

    batter1_id = batter_ids[0]
    batter2_id = batter_ids[1]
    batter3_id = batter_ids[2]



    stats = pitching_stats(2025, 2025, qual=1)

    batter_profiles = []
    for bid in [batter1_id, batter2_id, batter3_id]:
        profile = get_batter_profile(bid)
        if profile[0] is not None:
            batter_profiles.append(profile)
        else:
            print(f"Not enough data for one batter, skipping")


    all_players_response = requests.get("https://statsapi.mlb.com/api/v1/sports/1/players?season=2025")
    all_players = all_players_response.json()
    hand_lookup = {p["id"]: p["pitchHand"]["code"] for p in all_players["people"]}

    results = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_pitcher, player) for player in proster["roster"]]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)


    results.sort(reverse=True, key=lambda x: x[4])
    return {"results": results}