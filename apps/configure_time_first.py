"""Configure an AWTRIX NG clock for Time first, then Kitchen Clock apps.

By default this command is read-only: it inventories the Clock and prints the
planned change. Pass --apply to persist the documented AWTRIX NG settings.
"""

import argparse
import base64
import json
import os
import urllib.error
import urllib.request

TIME_APP_DURATION_MS = 600_000
BUILTIN_APP_NAMES = {"Time", "Date", "Temperature", "Humidity", "Battery"}
DISPLAYABLE_ORIGINS = {"pushed", "script"}


def request_json(host, port, user, password, path, method="GET", payload=None):
    """Call one documented AWTRIX NG JSON endpoint."""
    url = f"http://{host}:{port}{path}"
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    if user and password:
        token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def slot_key(app):
    """Keep the Clock's existing ordered apps in their established order."""
    slot = app.get("slot")
    return (slot is None, slot if slot is not None else 0)


def build_time_first_plan(apps):
    """Return a validated Time-first loop plan from AWTRIX's live inventory."""
    managed_apps = [app for app in apps if "enabled" in app and app.get("name")]
    names = {app["name"] for app in managed_apps}
    if "Time" not in names:
        raise ValueError("AWTRIX inventory has no built-in Time app")

    # A present but disabled app is retained in inventory only. Reordering it would
    # silently reactivate it, so the new loop owns enabled entries only.
    kitchen_apps = [
        app
        for app in managed_apps
        if app.get("origin") in DISPLAYABLE_ORIGINS
        and app.get("enabled", False)
        and app.get("present", False)
    ]
    visible_kitchen_apps = [
        app for app in kitchen_apps if not app.get("headless", False)
    ]
    if not visible_kitchen_apps:
        raise ValueError(
            "AWTRIX inventory has no present pushed or script apps to cycle after Time"
        )

    ordered_kitchen_names = [app["name"] for app in sorted(kitchen_apps, key=slot_key)]
    order = ["Time", *ordered_kitchen_names]
    # The order API preserves names it is not told about. Explicitly disable every
    # managed omission so the profile means Time followed by the selected app set.
    disabled = sorted(name for name in names if name not in set(order))

    return {
        "settings": {
            "autoTransition": True,
            "appDurationMs": TIME_APP_DURATION_MS,
        },
        "appOrder": {
            "order": order,
            "disabled": disabled,
        },
        "visibleKitchenApps": [
            app["name"] for app in sorted(visible_kitchen_apps, key=slot_key)
        ],
    }


def configure_time_first(host, port, user, password, apply=False):
    """Inventory the Clock and optionally apply its Time-first display profile."""
    apps = request_json(host, port, user, password, "/api/v1/apps")
    plan = build_time_first_plan(apps)
    if apply:
        # Settings and order are separate device writes. Keep the only two settings
        # this profile owns so a rejected order does not strand a 10-minute fallback.
        previous_settings = request_json(host, port, user, password, "/api/v1/settings")
        rollback_settings = {key: previous_settings[key] for key in plan["settings"]}
        request_json(
            host,
            port,
            user,
            password,
            "/api/v1/settings",
            method="PATCH",
            payload=plan["settings"],
        )
        try:
            request_json(
                host,
                port,
                user,
                password,
                "/api/v1/apps/order",
                method="PUT",
                payload=plan["appOrder"],
            )
        except (OSError, ValueError):
            # The order did not report success; restore settings only. The API does
            # not expose a safe transactional restoration of the prior full order.
            try:
                request_json(
                    host,
                    port,
                    user,
                    password,
                    "/api/v1/settings",
                    method="PATCH",
                    payload=rollback_settings,
                )
            except (OSError, ValueError) as rollback_error:
                raise RuntimeError(
                    "app-order write failed and Time-first settings rollback failed"
                ) from rollback_error
            raise
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("AWTRIX_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("AWTRIX_PORT", "8080"))
    )
    parser.add_argument("--user", default=os.environ.get("AWTRIX_USER", ""))
    parser.add_argument("--password", default=os.environ.get("AWTRIX_PASS", ""))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the Time-first profile after inventory succeeds",
    )
    args = parser.parse_args()
    plan = configure_time_first(
        args.host, args.port, args.user, args.password, apply=args.apply
    )
    print(json.dumps({"applied": args.apply, **plan}, indent=2))


if __name__ == "__main__":
    main()
