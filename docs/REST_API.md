# AWTRIX NG TC002 REST API Reference

The clock exposes an HTTP REST API on port `8080` (or configured port) with optional HTTP Basic Authentication.

---

## 1. Authentication
* **Scheme**: HTTP Basic Auth
* **Credentials**: Configured in AWTRIX web interface (`admin` / `password` or custom)
* **Header**: `Authorization: Basic <BASE64_USER_PASS>`

---

## 2. Pushed Custom Apps API

### Push / Update App
`PUT /api/v1/apps/pushed/{name}`

**Headers:**
`Content-Type: application/json`

**Payload:**
```json
{
  "text": "<display-label>",
  "textColor": "#00E5FF",
  "icon": "cake",
  "font": "small",
  "durationMs": 3000
}
```

**Parameters:**
* `text` *(string)*: Text string to display next to icon.
* `textColor` *(string)*: Hex RGB color (e.g. `"#FFFFFF"`, `"#00E5FF"`).
* `icon` *(string, optional)*: Name of icon in `/data/awtrix-ng/ICONS/<name>.gif` (without `.gif` extension).
* `font` *(string, optional)*: `"small"` (default) or `"large"`.
* `durationMs` *(int, optional)*: How long this app remains on screen before switching to next app (e.g. `3000` = 3s).

### Delete App
`DELETE /api/v1/apps/{name}`

**Response:**
```json
{"ok": true}
```

---

## 3. Persistent Script Apps API

### Upload Berry Script App (Stored on Flash)
`PUT /api/v1/apps/script/{name}`

**Headers:**
`Content-Type: text/plain`

**Body:**
```ruby
class ShabbatApp
  def draw()
    clear()
    icon("candle", 0, 0)
    text("6:36", 18, 5, "#FFFFFF")
  end
end
return ShabbatApp()
```

---

## 4. Device Status & Telemetry API

### Get Device Telemetry
`GET /api/v1/device`

**Example Response:**
```json
{
  "version": "1.1.1-tc002.5",
  "uid": "ccc4b2779b98",
  "ipAddress": "<device-address>",
  "hostname": "awtrix_clock",
  "wifiRssi": -50,
  "uptimeSeconds": 516,
  "freeHeapBytes": 16592896,
  "fps": 42,
  "brightness": 130,
  "batteryPercent": 100,
  "batteryVoltage": 4.15,
  "batteryPinMillivolts": 4150,
  "currentApp": "Time"
}
```

---

## 5. Active App Carousel API

### List All Apps in Carousel
`GET /api/v1/apps`

**Response:**
```json
[
  {"name": "Time", "enabled": true, "inLoop": true, "origin": "builtin"},
  {"name": "Date", "enabled": true, "inLoop": true, "origin": "builtin"},
  {"name": "Battery", "enabled": true, "inLoop": true, "origin": "builtin"},
  {"name": "shabbat", "enabled": true, "inLoop": true, "origin": "pushed", "icon": "candle"},
  {"name": "bday_1", "enabled": true, "inLoop": true, "origin": "pushed", "icon": "cake"}
]
```

---

## 6. Time-first Kitchen Clock profile

AWTRIX NG persists the display profile through two calls:

```text
PATCH /api/v1/settings
{"autoTransition": true, "appDurationMs": 600000}

PUT /api/v1/apps/order
{"order": ["Time", "...Kitchen Clock apps"], "disabled": ["...other built-ins"]}
```

`appDurationMs` is the default dwell for native apps. A pushed app with its own `durationMs` overrides that default, so Kitchen Clock cards remain short while native Time stays visible for ten minutes. Use `apps/configure_time_first.py` to read the live inventory, produce the exact order, and apply it only with `--apply`.

---

## 7. Persistent birthday scripts

`PUT /api/v1/apps/script/{name}` stores a Berry birthday script on AWTRIX. Follow it with:

```text
PATCH /api/v1/apps/{name}/config
```

The installer creates names such as `birthday-zach` and persists the person, month, day, color, Feb. 29 policy, and dwell time through the script configuration endpoint. The script uses AWTRIX's own `year()`, `month()`, `day()`, and hidden `loop()` lifecycle hook, so it recalculates after midnight without a host-side daemon.
