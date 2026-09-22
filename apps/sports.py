"""Fetch live NBA and NFL stats/scores from ESPN and push to AWTRIX NG TC002.

Usage:
  python3 apps/sports.py                      # Show all active/upcoming NFL & NBA games
  python3 apps/sports.py --team NYK           # Track Knicks
  python3 apps/sports.py --team NYG           # Track Giants
  python3 apps/sports.py --sport nfl          # Track only NFL
  python3 apps/sports.py --sport nba          # Track only NBA
  python3 apps/sports.py --daemon             # Auto-refresh live scores every 60s
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request

ESPN_ENDPOINTS = {
    "nfl": "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
}

FINAL_SCORE_DURATION_MS = 7000


def get_team_schedule_game(sport="nba", team="nyk"):
    """Fetch upcoming or recent game for a specific team from ESPN schedule API."""
    url = f"http://site.api.espn.com/apis/site/v2/sports/{'basketball/nba' if sport == 'nba' else 'football/nfl'}/teams/{team.lower()}/schedule"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
            events = data.get("events", [])
            for ev in events:
                comp = ev["competitions"][0]
                state = comp["status"]["type"]["state"]
                if state in ["in", "pre"]:
                    competitors = comp["competitors"]
                    home = next(c for c in competitors if c["homeAway"] == "home")
                    away = next(c for c in competitors if c["homeAway"] == "away")
                    return {
                        "sport": sport.upper(),
                        "state": state,
                        "away": away["team"]["abbreviation"],
                        "home": home["team"]["abbreviation"],
                        "away_score": away.get("score", {}).get("value", "0")
                        if isinstance(away.get("score"), dict)
                        else away.get("score", "0"),
                        "home_score": home.get("score", {}).get("value", "0")
                        if isinstance(home.get("score"), dict)
                        else home.get("score", "0"),
                        "detail": comp["status"]["type"].get("shortDetail", ""),
                        "clock": comp["status"].get("displayClock", ""),
                        "period": comp["status"].get("period", 0),
                    }
    except (OSError, ValueError, KeyError, IndexError, StopIteration) as error:
        print(f"Error fetching team schedule: {error}", file=sys.stderr)
    return None


def get_games(sport="nfl", team_filter=None):
    """Fetch games from ESPN scoreboard API."""
    url = ESPN_ENDPOINTS.get(sport.lower())
    if not url:
        return []

    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
    except (OSError, ValueError) as error:
        print(f"Error fetching {sport.upper()} data: {error}", file=sys.stderr)
        return []

    results = []
    for event in data.get("events", []):
        try:
            comp = event["competitions"][0]
            competitors = comp["competitors"]
            home = next(c for c in competitors if c["homeAway"] == "home")
            away = next(c for c in competitors if c["homeAway"] == "away")

            home_team = home["team"]["abbreviation"]
            away_team = away["team"]["abbreviation"]

            if team_filter:
                tf = team_filter.upper()
                if home_team != tf and away_team != tf:
                    continue

            home_score = home.get("score", "0")
            away_score = away.get("score", "0")

            status = comp["status"]
            state = status["type"]["state"]  # "pre", "in", "post"
            detail = status["type"].get("shortDetail", "")
            clock = status.get("displayClock", "")
            period = status.get("period", 0)

            results.append(
                {
                    "sport": sport.upper(),
                    "state": state,
                    "away": away_team,
                    "home": home_team,
                    "away_score": away_score,
                    "home_score": home_score,
                    "detail": detail,
                    "clock": clock,
                    "period": period,
                }
            )
        except (KeyError, IndexError, StopIteration, TypeError) as error:
            print(f"Skipping malformed {sport.upper()} event: {error}", file=sys.stderr)
            continue

    if not results and team_filter:
        sched_game = get_team_schedule_game(sport, team_filter)
        if sched_game:
            results.append(sched_game)

    return results


def format_compact_time(detail_str):
    """Convert verbose time strings like '10/5 - 7:00 PM EDT' to compact '10/5 7P'."""
    s = (
        detail_str.replace(" - ", " ")
        .replace(" EDT", "")
        .replace(" EST", "")
        .replace(" CDT", "")
        .replace(" CST", "")
        .replace(" PDT", "")
        .replace(" PST", "")
        .strip()
    )
    parts = s.split()
    if len(parts) >= 3 and ":" in parts[1]:
        hour = parts[1].split(":")[0]
        am_pm = "P" if "PM" in parts[2].upper() else "A"
        return f"{parts[0]} {hour}{am_pm}"
    elif len(parts) >= 2 and ":" in parts[0]:
        hour = parts[0].split(":")[0]
        am_pm = "P" if "PM" in parts[1].upper() else "A"
        return f"{hour}{am_pm}"
    return s[:8]


def push_to_awtrix(
    host,
    port,
    user,
    password,
    app_name,
    text,
    color="#FFFFFF",
    font="small",
    icon=None,
    duration_ms=None,
):
    """Push custom sports app payload to AWTRIX NG."""
    url = f"http://{host}:{port}/api/v1/apps/pushed/{app_name}"
    payload = {
        "text": text,
        "textColor": color,
        "font": font,
    }
    if icon:
        payload["icon"] = icon
    if duration_ms:
        payload["durationMs"] = duration_ms

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="PUT", headers={"Content-Type": "application/json"}
    )
    if user and password:
        creds = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
        req.add_header("Authorization", f"Basic {creds}")

    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--host",
        default=os.environ.get("AWTRIX_HOST", "127.0.0.1"),
        help="AWTRIX clock IP/hostname",
    )
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AWTRIX_PORT", "8080")),
        help="AWTRIX port",
    )
    p.add_argument(
        "--user", default=os.environ.get("AWTRIX_USER", ""), help="Auth user"
    )
    p.add_argument(
        "--password", default=os.environ.get("AWTRIX_PASS", ""), help="Auth password"
    )
    p.add_argument(
        "--team", help="Team abbreviation to track (e.g. NYG, NYJ, NYK, BKN, KC, BOS)"
    )
    p.add_argument(
        "--sport",
        choices=["all", "nfl", "nba"],
        default="all",
        help="Sport league to fetch",
    )
    p.add_argument("--daemon", action="store_true", help="Continuously refresh scores")
    args = p.parse_args()

    sports_to_check = ["nfl", "nba"] if args.sport == "all" else [args.sport]

    while True:
        all_games = []
        for sport in sports_to_check:
            games = get_games(sport=sport, team_filter=args.team)
            all_games.extend(games)

        if not all_games:
            print("No matching games found right now.")
        else:
            for game in all_games[:5]:  # Push primary team or top games
                base_name = (
                    f"{args.team.lower()}" if args.team else f"{game['sport'].lower()}"
                )
                icon = "basketball" if game["sport"] == "NBA" else "football"

                if game["state"] == "in":
                    # LIVE GAME: Green flip cards
                    push_to_awtrix(
                        args.host,
                        args.port,
                        args.user,
                        args.password,
                        base_name,
                        f"{game['away']} {game['away_score']}",
                        color="#00E676",
                        font="small",
                        icon=icon,
                        duration_ms=3000,
                    )
                    push_to_awtrix(
                        args.host,
                        args.port,
                        args.user,
                        args.password,
                        f"{base_name}_2",
                        f"{game['home']} {game['home_score']}",
                        color="#00E676",
                        font="small",
                        icon=icon,
                        duration_ms=3000,
                    )
                elif game["state"] == "post":
                    # FINAL GAME: Single scrolling score
                    text = f"{game['away']} {game['away_score']} - {game['home']} {game['home_score']} (Final)"
                    push_to_awtrix(
                        args.host,
                        args.port,
                        args.user,
                        args.password,
                        base_name,
                        text,
                        color="#B0BEC5",
                        font="small",
                        icon=icon,
                        duration_ms=FINAL_SCORE_DURATION_MS,
                    )
                else:
                    # UPCOMING: Card 1 = "NY@PHI", Card 2 = "10/5 7P"
                    time_str = format_compact_time(game["detail"])
                    push_to_awtrix(
                        args.host,
                        args.port,
                        args.user,
                        args.password,
                        base_name,
                        f"{game['away']}@{game['home']}",
                        color="#64B5F6",
                        font="small",
                        icon=icon,
                        duration_ms=3500,
                    )
                    push_to_awtrix(
                        args.host,
                        args.port,
                        args.user,
                        args.password,
                        f"{base_name}_2",
                        time_str,
                        color="#FFB74D",
                        font="small",
                        icon=icon,
                        duration_ms=3500,
                    )
                    print(
                        f"[{game['sport']}] Pushed upcoming flip cards: {game['away']}@{game['home']} & {time_str}"
                    )

        if not args.daemon:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
