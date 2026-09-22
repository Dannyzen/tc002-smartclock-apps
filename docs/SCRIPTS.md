# Kitchen Clock script operations

| Tool | Inputs | Side effects | Persistence and operational limits |
| --- | --- | --- | --- |
| `apps/shabbat.py` | `HEBCAL_ZIP`, city, Clock settings | Hebcal GET; pushed Clock card | Volatile; 2-hour daemon interval; host required |
| `apps/birthdays.py` | `BIRTHDAYS_JSON_B64` in the process environment | Two pushed cards/person | Runtime-only payload; missing or malformed payload stops the command; volatile 24-hour daemon mode |
| `apps/install_birthday_scripts.py` | private birthday JSON, Clock settings | None by default; upload/config writes only with `--apply` | Persistent Clock scripts; sequential install no rollback |
| `scripts/birthday_countdown.be` | per-script Clock configuration | On-device calendar/display logic | Intended persistent behavior; needs hardware proof |
| `apps/sports.py` | ESPN, `--team`, `--sport` | ESPN GET; pushed cards | Five-game cap; no-team `nba`/`nfl` names can reuse slots; stale `_2` cards require device policy |
| `apps/configure_time_first.py` | Clock inventory/settings | GET always; writes only with `--apply` | Inventory-derived destructive ordering change; settings-only compensation on order failure |
| `apps/icons.py` | none | Writes tracked `icons/*.gif` | Does not upload icons to the Clock |

Callers provide runtime environment variables through their process supervisor or approved secret manager. Repository files are never loaded for Birthday payloads or Clock credentials.
