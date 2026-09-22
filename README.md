# Ulanzi TC002 Smart Clock App Suite

A standalone, lightweight Python integration suite, pixel icon generator, and zero-scroll display engine for the **Ulanzi TC002 (SSD202D)** smart pixel clock running **AWTRIX NG**.

> [!NOTE]
> **No Home Assistant, Node-RED, or MQTT broker required.** All apps directly communicate with the clock's native HTTP REST API.

---

## ⚙️ Configuration

Provide runtime values through the caller process, service supervisor, or approved secret manager. This repository does not load a repository `.env` file and includes no environment-template file.

```bash
export AWTRIX_HOST=<clock-host>
export AWTRIX_PORT=8080
# Supply AWTRIX_USER and AWTRIX_PASS only through your approved runtime secret path.
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `AWTRIX_HOST` | IP address or hostname of your clock | `127.0.0.1` |
| `AWTRIX_PORT` | HTTP Web port (AWTRIX uses 8080) | `8080` |
| `AWTRIX_USER` | Basic Auth username (if enabled) | `""` |
| `AWTRIX_PASS` | Basic Auth password (if enabled) | `""` |
| `HEBCAL_ZIP` | US Zip code for Shabbat candle lighting times | `""` |
| `BIRTHDAYS_JSON_B64`| Runtime-only Infisical Birthday payload | unset |

---

## 🕒 Features & Included Apps

### 1. 🕯️ Shabbat Candle Lighting Clock (`apps/shabbat.py`)
Queries the **Hebcal API** for upcoming Shabbat candle lighting and Havdalah times and displays a static, non-scrolling candle-lighting time alongside an animated flickering candle icon.
```bash
python3 apps/shabbat.py                     # Push Shabbat time (via env / flags)
python3 apps/shabbat.py --zip 90210         # Specific US ZIP code
python3 apps/shabbat.py --daemon            # Run as background updater (every 2h)
```

### 2. 🎂 Persistent Birthday Countdown (`scripts/birthday_countdown.be`)
The primary birthday implementation is a persistent Berry script intended to run on the Clock. Its source uses AWTRIX's local calendar and hidden `loop()` lifecycle to recalculate after midnight, with reboot persistence expected from the documented script API. Simulator or physical Clock verification is still required before treating hidden-loop behavior, rendered countdowns, or reboot survival as proven. Feb. 29 defaults to Feb. 28 in non-leap years, with a per-person March 1 option.

Inject the private `BIRTHDAYS_JSON_B64` runtime secret, then review the on-device plan without writing:
```bash
python3 apps/install_birthday_scripts.py --host <clock-ip>
```

Install only after reviewing the plan:
```bash
python3 apps/install_birthday_scripts.py --host <clock-ip> --apply
```

`apps/birthdays.py` remains a host-pushed fallback and now uses the same Feb. 29 rule.

### 3. 🏀 Live Sports Scores & Schedules (`apps/sports.py`)
Tracks live NBA and NFL games directly from ESPN's scoreboard API:
* **Upcoming Game**: `[🏀] New York vs. PHI` (3.5s) ➔ `[🏀] 10/5 7P` (3.5s)
* **Live Game**: `[🏀] NY 88` (3s) ➔ `[🏀] PHI 85` (3s) in bright green
* **Final Game**: `[🏀] NY 110 - PHI 102 (Final)` in silver
```bash
python3 apps/sports.py --team NYK           # Track team (e.g. NYK, BOS, KC, PHI)
python3 apps/sports.py --sport nfl          # Track all active NFL games
python3 apps/sports.py --daemon             # Auto-refresh live scores every 60s
```


### 4. 🕒 Time-first app cycle (`apps/configure_time_first.py`)
The Clock can hold the native **Time** display for ten minutes, then rotate through its present Kitchen Clock pushed and script apps. Pushed cards retain their individual short durations. The command reads the live app inventory and prints its proposed order by default:

```bash
python3 apps/configure_time_first.py --host <clock-ip>
```

Apply the persisted AWTRIX NG profile only after reviewing that plan:

```bash
python3 apps/configure_time_first.py --host <clock-ip> --apply
```

The applied profile sets `autoTransition: true`, native `appDurationMs: 600000`, places `Time` first, keeps current pushed/script apps after it, and disables other currently enabled built-in apps. It refuses to apply when `Time` or a visible pushed/script app is absent.

### 5. 🎨 Pure-Python Pixel Icon Generator (`apps/icons.py`)
Generates 16×16 animated and static GIF89a pixel art icons with zero external dependencies (no Pillow/PIL required):
```bash
python3 apps/icons.py                       # Generates candle.gif, cake.gif, basketball.gif
```

---

## 📐 Display Matrix Budget & Zero-Scroll UX Protocol

The Ulanzi TC002 features a physical **52 pixel wide × 16 pixel high** RGB LED matrix:

```text
|<--------------------------- 52 Pixels Total --------------------------->|
+------------------+------------------------------------------------------+
|   16x16 Icon     |                 36px Text Canvas                     |
|  (x = 0 to 15)   |                  (x = 18 to 51)                      |
|                  |                                                      |
|   [🎂 / 🕯️ / 🏀]  |              "6:36"   or   "<display-label>"                   |
+------------------+------------------------------------------------------+
```

* **Physical Limits**: A 16×16 icon takes 16 pixels. Remaining usable text canvas is **36 pixels**.
* **Character Capacity**: In standard font, maximum static text length is **7 to 8 characters**.
* **Zero-Scroll Flip Card Protocol**: Multi-field information (e.g. Name + Days remaining) is displayed as two alternating 3-second static cards (`<display-label>` ➔ `22 Days`) rather than long, sluggish horizontal text scrolls.

---

## 🧪 Unit Testing

Run the branch coverage gate from the repository root:
```bash
uv run --with coverage coverage run -m unittest discover -s tests -p "test_*.py"
uv run --with coverage coverage report -m
```

The gate measures the safety-critical birthday and Time-first modules and fails below 100% statement and branch coverage. Berry script runtime is tracked separately because Python coverage cannot execute it. Tests cover birthday scripts, Time-first profile behavior, Shabbat, sports, icons, and host fallback paths.

---

## 📚 In-Depth Documentation

* 📖 **[System Architecture](docs/ARCHITECTURE.md)**: SSD202D SoC, JFFS2 flash partitioning, and `zkdaemon` port 80 conflict prevention.
* 🌐 **[REST API Reference](docs/REST_API.md)**: Complete HTTP endpoint reference for port 8080 with Basic Auth.
* 🎨 **[Display Guidelines](docs/DISPLAY_GUIDELINES.md)**: 52×16 matrix geometry, font metrics, and anti-scroll UX rules.
* 🛠️ **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)**: Battery trickle-charge curve & 0% threshold physics, DHCP discovery scripts.
* 🎂 **[Persistent Birthdays](docs/PERSISTENT_BIRTHDAYS.md)**: On-Clock Berry countdown, configuration, and device acceptance.
* 🕒 **[Time-first Profile](docs/TIME_FIRST_PROFILE.md)**: Inventory-derived ordering, settings, and rollback boundary.
* 📋 **[Script Operations](docs/SCRIPTS.md)**: Inputs, effects, persistence, and limits for every tool.

---

## 🤖 Antigravity AI Agent Skill

This repository includes a pre-configured Antigravity AI agent skill in `.agents/skills/awtrix-ng-tc002/SKILL.md` to ensure any AI assistant working on this project automatically adheres to hardware constraints, port rules, and display protocols.
