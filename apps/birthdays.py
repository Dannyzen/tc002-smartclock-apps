"""Birthday Countdown script for AWTRIX NG TC002.

Calculates days remaining until birthdays and pushes clean, crisp flip cards
with an animated birthday cake icon to the clock.

Usage:
  python3 apps/birthdays.py                # Push all birthdays as clean flip cards
  python3 apps/birthdays.py --daemon       # Auto-refresh daily
"""

import argparse
import base64
import binascii
import datetime
import json
import os
import sys
import time
import urllib.request

RUNTIME_BIRTHDAYS_ENV = "BIRTHDAYS_JSON_B64"


def load_birthdays():
    """Load runtime-only Birthday records from a base64-encoded JSON secret.

    Birthday data is intentionally absent from source control. The process
    environment must supply one valid runtime payload; this command never loads
    repository files or substitutes demos when that payload is absent.
    """
    encoded = os.environ.get(RUNTIME_BIRTHDAYS_ENV)
    if not encoded:
        raise ValueError(f"{RUNTIME_BIRTHDAYS_ENV} is required")
    try:
        birthdays = json.loads(base64.b64decode(encoded, validate=True))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{RUNTIME_BIRTHDAYS_ENV} must contain base64 JSON") from error
    if not isinstance(birthdays, list):
        raise TypeError(f"{RUNTIME_BIRTHDAYS_ENV} must encode a JSON array")
    return birthdays


def birthday_date_for_year(target_month, target_day, year, leap_day="feb28"):
    """Return a birthday date, using Feb. 28 for Feb. 29 in non-leap years."""
    if target_month == 2 and target_day == 29:
        try:
            return datetime.date(year, 2, 29)
        except ValueError:
            if leap_day == "mar1":
                return datetime.date(year, 3, 1)
            return datetime.date(year, 2, 28)
    return datetime.date(year, target_month, target_day)


def calculate_days_until(target_month, target_day, now=None, leap_day="feb28"):
    """Calculate days remaining until next occurrence of month/day."""
    if now is None:
        now = datetime.date.today()  # noqa: DTZ011 - legacy fallback follows host-local calendar

    this_year_bday = birthday_date_for_year(
        target_month, target_day, now.year, leap_day
    )
    if this_year_bday == now:
        return 0, this_year_bday
    if this_year_bday > now:
        return (this_year_bday - now).days, this_year_bday
    next_year_bday = birthday_date_for_year(
        target_month, target_day, now.year + 1, leap_day
    )
    return (next_year_bday - now).days, next_year_bday


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
    """Push custom app payload to AWTRIX NG."""
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
        "--daemon", action="store_true", help="Continuously refresh countdown daily"
    )
    args = p.parse_args()

    birthdays_list = load_birthdays()

    while True:
        today = datetime.date.today()  # noqa: DTZ011 - persistent mode uses the Clock calendar
        # Calculate days for all birthdays and sort by days remaining
        active_bdays = []
        for b in birthdays_list:
            days, next_date = calculate_days_until(
                b["month"], b["day"], today, b.get("leap_day", "feb28")
            )
            active_bdays.append(
                {
                    "name": b["name"],
                    "days": days,
                    "date": next_date,
                    "color": b.get("color", "#FFFFFF"),
                    "app_slug": b["name"].lower().replace(" ", "_"),
                }
            )

        active_bdays.sort(key=lambda x: x["days"])

        for b in active_bdays:
            name = b["name"]
            days = b["days"]
            slug = f"{b['app_slug']}"
            color = b["color"]

            if days == 0:
                text_1 = name
                text_2 = "TODAY!"
            elif days == 1:
                text_1 = name
                text_2 = "1 Day"
            else:
                text_1 = name
                text_2 = f"{days} Days"

            # Push synchronized 3.0s flip cards with cake icon
            try:
                # Card 1: supplied display label
                push_to_awtrix(
                    host=args.host,
                    port=args.port,
                    user=args.user,
                    password=args.password,
                    app_name=f"{slug}_1",
                    text=text_1,
                    color=color,
                    font="small",
                    icon="cake",
                    duration_ms=3000,
                )
                # Card 2: Days (e.g. "22 Days")
                push_to_awtrix(
                    host=args.host,
                    port=args.port,
                    user=args.user,
                    password=args.password,
                    app_name=f"{slug}_2",
                    text=text_2,
                    color=color,
                    font="small",
                    icon="cake",
                    duration_ms=3000,
                )
                print(f"[OK] Pushed birthday cards for {name}: {days} days remaining")
            except (OSError, ValueError) as e:
                print(f"[ERR] Failed pushing birthday for {name}: {e}", file=sys.stderr)

        if not args.daemon:
            break
        # This is elapsed-time legacy behavior, not a timezone-aware midnight scheduler.
        print("Sleeping until tomorrow...")
        time.sleep(86400)


if __name__ == "__main__":
    main()
