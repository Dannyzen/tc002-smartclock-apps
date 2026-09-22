# Time-first rotation profile

`apps/configure_time_first.py` makes the native `Time` app the first app and gives the default app dwell ten minutes.

## Dry run and apply

```bash
python3 apps/configure_time_first.py --host <clock-ip>
```

Dry run performs `GET /api/v1/apps`, requires `Time` plus one enabled, present, non-headless pushed/script app, then prints its proposed plan.

```bash
python3 apps/configure_time_first.py --host <clock-ip> --apply
```

Apply reads prior settings, patches `autoTransition: true` and `appDurationMs: 600000`, then writes the inventory-derived order. It restores only those two settings if the order write raises an expected network or response error. It does not restore a prior app order and has no successful-apply readback.

## Order rules

The order is `Time` followed by enabled, present pushed/script apps sorted by their current slots. Headless scripts remain in the order so they continue to run, though they do not satisfy the visible-app requirement. Every managed app omitted from the order is placed in `disabled`, including built-ins and disabled app entries.

Short cards must set their own durations: persistent birthday scripts use 6000ms; Shabbat and sports final cards use 7000ms; live sports use 3000ms; upcoming sports cards use 3500ms. Otherwise the global ten-minute fallback applies.

## Device acceptance

Capture live app inventory and current settings before applying. After application, read them back and confirm Time first, intended scripts present, unwanted built-ins disabled, and a full rotation returns to Time after the short app cards. No repository test proves this on hardware.
