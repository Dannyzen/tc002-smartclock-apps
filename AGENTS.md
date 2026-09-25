# Kitchen Clock agent guide

## Truth and boundaries

- Repository source and tests are the source of truth for behavior. `README.md` and `docs/` explain it.
- Source tests and documents do not by themselves prove AWTRIX NG HTTP or Berry behavior. Record device validation separately from repository source.
- All project work runs on Bigs under `/srv/bigs-runtime`. Do not use a local project copy as an active workspace.
- `BIRTHDAYS_JSON_B64`, credentials, API responses, caches, and runtime state are private process or secret-manager data. No Birthday payload, `.env`, or example belongs in Git.

## Write boundaries

- Every tool defaults to a safe local computation except a command with `--apply`.
- `apps/configure_time_first.py` performs a device **GET** even in dry-run mode. `--apply` writes settings and app ordering after printing/validating the inventory-derived plan.
- `apps/install_birthday_scripts.py` has no network I/O until `--apply`; apply uploads one Berry script and then its per-person configuration for every plan entry. It is sequential and not transactional.
- Never send a Clock write, enable an app, upload a script, alter device settings, or change app order without explicit user approval and a verified device target.

## Script map

| Path | Role | External side effect |
| --- | --- | --- |
| `apps/shabbat.py` | Host-pushed Hebcal candle time | HTTP push to Clock |
| `apps/birthdays.py` | Legacy host-pushed birthday fallback | HTTP pushes two volatile cards per birthday |
| `apps/install_birthday_scripts.py` | Persistent Berry birthday installer | Only with `--apply` |
| `scripts/birthday_countdown.be` | On-Clock persistent countdown | Executes only after upload to Clock |
| `apps/sports.py` | Host-pushed ESPN sports cards | ESPN read and Clock HTTP push |
| `apps/configure_time_first.py` | Time-first rotation profile | Clock GET; writes only with `--apply` |
| `apps/icons.py` | Local GIF generator | Overwrites tracked `icons/*.gif`; does not install icons on Clock |

## Birthday modes

Persistent Berry birthdays are the preferred design. A birthday display name is limited to 18 characters by the Berry config field; its derived AWTRIX script name is limited to 32 characters. They use the Clock calendar and `loop()` to recompute after midnight. Legacy `apps/birthdays.py` is invoked only when a user runs it; it is not an automatic fallback.

Feb. 29 defaults to Feb. 28 in non-leap years. A per-person `leap_day: "mar1"` opts into March 1.

## Verification

Run the gate from the repository root:

```bash
uv run --with coverage coverage run -m unittest discover -s tests -v
uv run --with coverage coverage report -m
uvx --offline ruff check apps tests
uvx --offline ruff format --check apps tests
```

The Python coverage gate measures the safety-critical birthday and Time-first modules with branches. It does not prove Berry runtime execution. A real-device acceptance must separately capture inventory, settings, uploaded script/config readback, rotation order, reboot persistence, and a cross-midnight result.
