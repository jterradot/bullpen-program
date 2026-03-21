
from pybaseball import playerid_lookup, statcast_batter, statcast_pitcher, pitching_stats
player_id = 681882

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

print(get_reliable_season(player_id))