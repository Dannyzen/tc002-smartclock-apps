---
name: awtrix-ng-tc002
description: Use for Kitchen Clock AWTRIX NG source, scripts, and device boundaries.
---

# Kitchen Clock AWTRIX NG guidance

Read `AGENTS.md` first. It names source truth, process-only runtime data, and every write boundary.

## Source map

- `apps/configure_time_first.py`: inventory-derived Time-first profile. Dry run reads the Clock; `--apply` writes settings and order.
- `scripts/birthday_countdown.be`: persistent on-Clock birthday logic. Its lifecycle is source-declared until a physical Clock proves it.
- `apps/install_birthday_scripts.py`: validates private birthday data; only `--apply` uploads scripts/configuration.
- `apps/birthdays.py`: legacy host-pushed fallback, not automatic.
- `docs/PERSISTENT_BIRTHDAYS.md`, `docs/TIME_FIRST_PROFILE.md`, and `docs/SCRIPTS.md`: operational contracts.

## Rules

1. Supply all runtime values through the caller process, service supervisor, or approved secret manager. Do not load or create repository `.env` files. Keep Birthday data only in the runtime-only `BIRTHDAYS_JSON_B64` secret.
2. Do not call a Clock, upload a script, alter settings, or reorder apps without explicit user approval and verified device inventory.
3. Persistent Berry scripts and hidden `loop()` behavior require hardware acceptance. Source tests do not prove firmware behavior.
4. Run the coverage, Ruff, and formatting gates in `AGENTS.md`. Python coverage covers `apps/`; Berry execution needs separate simulator/device evidence.
5. `apps/icons.py` changes repository GIFs only. It does not install an icon on a Clock.
