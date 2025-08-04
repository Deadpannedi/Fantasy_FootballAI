# fantasy_draft_cli_interactive.py

from collections import defaultdict
import requests

def load_players_from_sleeper():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    all_players = response.json()

    #filter for only active players with a projection
    players = []
    for player_id, p in all_players.items():
        if (
            p.get("active")
            and p.get("position")in {"QB", "RB", "WR", "TE"}
            and p.get("fantasy_positions")
        ):
            players.append({
                "name": p.get("full_name") or p.get("last_name"),
                "pos": p["position"],
                "proj": 200, #placeholdder until projections added
                "tier": 3,   #placeholder until tiers calculated
                "adp": p.get("adp", 100)  #Use fallback if adp is missing
            })


    return players


def load_players_from_api():
   return load_players_from_sleeper()

players = load_players_from_api()

replacement_points = {"QB": 180, "RB": 160, "WR": 165, "TE": 140}
roster_limits = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}

# Your roster starts empty
roster = defaultdict(int)

# === Scoring Functions ===
def calculate_vor(player):
    return player["proj"] - replacement_points[player["pos"]]

def calculate_need_modifier(position, roster):
    if roster[position] == 0:
        return 1.2
    elif roster[position] < roster_limits[position]:
        return 1.0
    else:
        return 0.8

def calculate_scarcity_modifier(position, tier, players):
    remaining = sum(1 for p in players if p["pos"] == position and p["tier"] == tier)
    if remaining <= 1:
        return 1.2
    elif remaining <= 3:
        return 1.0
    else:
        return 0.9

def calculate_composite_score(player, roster, players):
    vor = calculate_vor(player)
    need = calculate_need_modifier(player["pos"], roster)
    scarcity = calculate_scarcity_modifier(player["pos"], player["tier"], players)
    return vor * need * scarcity

def recommend_best_picks(players, roster, top_n=5):
    scored = []
    for p in players:
        score = calculate_composite_score(p, roster, players)
        scored.append((p, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]

# === Draft Loop ===
while True:
    print("\n--- Draft Assistant ---")
    if not players:
        print("All players drafted.")
        break

    print("\nTop Recommendations:")
    recommendations = recommend_best_picks(players, roster)
    for i, (p, score) in enumerate(recommendations):
        print(f"{i + 1}. {p['name']} ({p['pos']}) - Score: {score:.2f}")

    try:
        choice = int(input("Select player to draft (1-5), or 0 to quit: "))
        if choice == 0:
            break
        selected = recommendations[choice - 1][0]
    except (ValueError, IndexError):
        print("Invalid choice. Try again.")
        continue

    # Update roster
    roster[selected["pos"]] += 1
    players = [p for p in players if p["name"] != selected["name"]]

    print(f"\nYou drafted: {selected['name']} ({selected['pos']})")
    print("Current Roster:")
    for pos in roster_limits:
        print(f"{pos}: {roster[pos]} / {roster_limits[pos]}")

