"""Shabbat Candle Lighting Times for AWTRIX NG TC002.

Pulls candle lighting times for Friday evening from the Hebcal API
and displays them cleanly as a static zero-scroll screen: `[🕯️] 6:36`.

Usage:
  python3 apps/shabbat.py --zip 11803
  python3 apps/shabbat.py --city "New York"
"""

import argparse
import base64
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request


def get_shabbat_info(zip_code=None, city=None, b_minutes=18):
    """Fetch Shabbat candle lighting time from Hebcal API."""
    params = {
        "cfg": "json",
        "m": 50,  # havdalah minutes
        "b": b_minutes,  # candle lighting minutes before sundown
    }
    if zip_code:
        params["zip"] = zip_code
    elif city:
        params["city"] = city
    else:
        params["geo"] = "geoname"
        params["geonameid"] = "5128581"  # New York

    url = f"https://www.hebcal.com/shabbat?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AwtrixTC002Shabbat/1.0"})

    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)

    candle_lighting_str = None
    candle_lighting_dt = None
    parasha = None
    havdalah_str = None

    for item in data.get("items", []):
        cat = item.get("category")
        if cat == "candles":
            candle_lighting_str = item.get("title", "").replace("Candle lighting: ", "")
            candle_lighting_dt = item.get("date")
        elif cat == "parashat":
            parasha = item.get("title")
        elif cat == "havdalah":
            havdalah_str = item.get("title", "").replace("Havdalah: ", "")

    return {
        "location": data.get("location", {}).get("title", "Unknown"),
        "candle_time": candle_lighting_str,
        "candle_date": candle_lighting_dt,
        "parasha": parasha,
        "havdalah_time": havdalah_str,
    }


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
        "--zip",
        dest="zip_code",
        default=os.environ.get("HEBCAL_ZIP", ""),
        help="US Zip Code",
    )
    p.add_argument(
        "--city",
        default=os.environ.get("HEBCAL_CITY", ""),
        help="City name (e.g. 'New York')",
    )
    p.add_argument("--name", default="shabbat", help="App name on Awtrix carousel")
    p.add_argument(
        "--daemon", action="store_true", help="Keep running and update every 2 hours"
    )
    args = p.parse_args()

    while True:
        try:
            info = get_shabbat_info(
                zip_code=args.zip_code or None, city=args.city or None
            )
            if info["candle_time"]:
                time_str = info["candle_time"].split()[0]  # e.g. "6:36"
            else:
                time_str = "--:--"

            print(
                f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] Location: {info['location']}"
            )
            print(f"Candle Lighting Time: {time_str}")

            res = push_to_awtrix(
                host=args.host,
                port=args.port,
                user=args.user,
                password=args.password,
                app_name=args.name,
                text=time_str,
                color="#FFFFFF",
                font="small",
                icon="candle",
                duration_ms=7000,
            )
            print(f"Pushed to AWTRIX: {res}")
        except (OSError, ValueError, KeyError) as e:
            print(f"Error updating Shabbat times: {e}", file=sys.stderr)

        if not args.daemon:
            break
        time.sleep(7200)


if __name__ == "__main__":
    main()
