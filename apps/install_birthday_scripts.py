"""Install persistent, on-Clock AWTRIX NG birthday countdown scripts.

Default mode validates a birthday config and prints the script/configuration plan.
Pass --apply to upload scripts and persist their per-person settings on a reachable Clock.
"""

import argparse
import base64
import binascii
import datetime
import json
import os
import re
import urllib.request
from pathlib import Path

LEAP_DAY_POLICIES = {"feb28", "mar1"}
SCRIPT_PREFIX = "birthday-"
SCRIPT_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "scripts" / "birthday_countdown.be"
)


def script_name(person):
    """Return a stable AWTRIX-safe script name for one birthday."""
    # Script names persist in AWTRIX's namespace, so normalize identically named
    # people and enforce the device's 32-character identifier limit before writing.
    slug = re.sub(r"[^a-z0-9]+", "-", person.lower()).strip("-")
    if not slug:
        raise ValueError("birthday name must contain letters or numbers")
    name = f"{SCRIPT_PREFIX}{slug}"
    if len(name) > 32:
        raise ValueError(f"birthday script name exceeds AWTRIX limit: {name}")
    return name


def validate_birthday(birthday):
    """Validate and normalize one birthday configuration entry."""
    required = {"name", "month", "day"}
    missing = required - birthday.keys()
    if missing:
        raise ValueError(f"birthday is missing required keys: {sorted(missing)}")
    name = birthday["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("birthday name must be a non-empty string")
    if len(name.strip()) > 18:
        raise ValueError(
            "birthday name exceeds Berry person field limit of 18 characters"
        )
    month = birthday["month"]
    day = birthday["day"]
    if not isinstance(month, int) or not isinstance(day, int):
        raise TypeError("birthday month and day must be integers")
    try:
        datetime.date(2024, month, day)
    except ValueError as error:
        raise ValueError(f"invalid birthday {month}/{day}") from error
    leap_day = birthday.get("leap_day", "feb28")
    if leap_day not in LEAP_DAY_POLICIES:
        raise ValueError(f"unsupported leap_day policy: {leap_day}")
    color = birthday.get("color", "#FFFFFF")
    if not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValueError("birthday color must be a #RRGGBB string")
    return {
        "name": name.strip(),
        "month": month,
        "day": day,
        "color": color.upper(),
        "leap_day": leap_day,
    }


RUNTIME_BIRTHDAYS_ENV = "BIRTHDAYS_JSON_B64"


def load_birthdays():
    """Load validated Birthday records from a runtime-only base64 JSON secret."""
    encoded = os.environ.get(RUNTIME_BIRTHDAYS_ENV)
    if not encoded:
        raise ValueError(f"{RUNTIME_BIRTHDAYS_ENV} is required")
    try:
        birthdays = json.loads(base64.b64decode(encoded, validate=True))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{RUNTIME_BIRTHDAYS_ENV} must contain base64 JSON") from error
    if not isinstance(birthdays, list) or not birthdays:
        raise ValueError(f"{RUNTIME_BIRTHDAYS_ENV} must encode a non-empty JSON array")
    return [validate_birthday(birthday) for birthday in birthdays]


def build_install_plan(birthdays):
    """Build one persistent AWTRIX script/configuration record per birthday."""
    names = set()
    plan = []
    for birthday in birthdays:
        birthday = validate_birthday(birthday)
        name = script_name(birthday["name"])
        if name in names:
            raise ValueError(f"duplicate birthday script name: {name}")
        names.add(name)
        plan.append(
            {
                "script": name,
                "config": {
                    "person": birthday["name"],
                    "birthMonth": birthday["month"],
                    "birthDay": birthday["day"],
                    "color": birthday["color"],
                    "leapDay": birthday["leap_day"],
                    "dwellMs": 6000,
                },
            }
        )
    return plan


def request(
    host, port, user, password, path, method="GET", body=None, content_type=None
):
    """Call an AWTRIX endpoint without exposing credentials in output."""
    headers = {"Content-Type": content_type} if content_type else {}
    http_request = urllib.request.Request(
        f"http://{host}:{port}{path}", data=body, method=method, headers=headers
    )
    if user and password:
        token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
        http_request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(http_request, timeout=5) as response:
        return json.load(response)


def require_success(response, action):
    """Reject AWTRIX 200 responses that report a script compile or restart error."""
    if response.get("ok") is not True or response.get("error") is not None:
        raise RuntimeError(f"AWTRIX rejected {action}: {response.get('error')}")


def install_birthdays(host, port, user, password, birthdays, apply=False):
    """Plan or upload persistent birthday scripts and their per-app configuration."""
    plan = build_install_plan(birthdays)
    if not apply:
        return plan
    source = SCRIPT_TEMPLATE.read_bytes()
    # Upload and configuration are deliberately sequential. AWTRIX has no batch
    # transaction: callers must inspect the device before retrying a failed apply.
    for item in plan:
        upload = request(
            host,
            port,
            user,
            password,
            f"/api/v1/apps/script/{item['script']}",
            method="PUT",
            body=source,
            content_type="text/plain",
        )
        require_success(upload, f"script upload for {item['script']}")
        configured = request(
            host,
            port,
            user,
            password,
            f"/api/v1/apps/{item['script']}/config",
            method="PATCH",
            body=json.dumps(item["config"]).encode(),
            content_type="application/json",
        )
        require_success(configured, f"configuration for {item['script']}")

    inventory = request(host, port, user, password, "/api/v1/apps")
    installed = {app.get("name"): app for app in inventory}
    for item in plan:
        app = installed.get(item["script"])
        if not app or app.get("origin") != "script" or not app.get("present"):
            raise RuntimeError(f"AWTRIX readback is missing {item['script']}")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("AWTRIX_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("AWTRIX_PORT", "8080"))
    )
    parser.add_argument("--user", default=os.environ.get("AWTRIX_USER", ""))
    parser.add_argument("--password", default=os.environ.get("AWTRIX_PASS", ""))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = install_birthdays(
        args.host,
        args.port,
        args.user,
        args.password,
        load_birthdays(),
        apply=args.apply,
    )
    print(json.dumps({"applied": args.apply, "scripts": plan}, indent=2))


if __name__ == "__main__":
    main()
