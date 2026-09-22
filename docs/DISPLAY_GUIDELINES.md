# 52×16 Display Matrix & Zero-Scroll UX Guidelines

The Ulanzi TC002 smart clock features a physical **52 pixel wide × 16 pixel high** matrix. Designing high-readability apps requires strict adherence to spatial budgeting and anti-scrolling techniques.

---

## 1. Spatial Width Budget

```text
|<--------------------------- 52 Pixels Total --------------------------->|
+------------------+------------------------------------------------------+
|   16x16 Icon     |                 36px Text Canvas                     |
|  (x = 0 to 15)   |                  (x = 18 to 51)                      |
|                  |                                                      |
|   [🎂 / 🕯️ / 🏀]  |              "6:36"   or   "<display-label>"                   |
+------------------+------------------------------------------------------+
```

* **Icon Area**: `0 <= x <= 15` (16 pixels)
* **Text Margin**: `x = 16..17` (2 pixels padding)
* **Text Canvas**: `18 <= x <= 51` (**36 pixels usable**)

---

## 2. Character Capacity & Font Rules

* Standard small font character width: `~4 to 5 pixels` (including inter-character spacing).
* **Maximum static text length**: **7 to 8 characters**.
* Any text string longer than 8 characters will automatically trigger horizontal scrolling across the screen.

---

## 3. Anti-Scrolling Techniques (Zero-Scroll Protocol)

### Technique A: 3-Second Synchronized Flip Cards ⭐ *(Preferred)*
For data that cannot fit within 8 characters (e.g. Name + Days remaining, or Matchup + Game Time), split the data into **two sequential static cards**:

#### Birthday Countdown Pattern:
* **Card 1 (3.0s)**: `[🎂] <display-label>` *(Electric Cyan `#00E5FF`)*
* **Card 2 (3.0s)**: `[🎂] 22 Days` *(White `#FFFFFF`)*

#### Sports Schedule Pattern:
* **Card 1 (3.5s)**: `[🏀] NY@PHI` *(Light Blue `#64B5F6`)*
* **Card 2 (3.5s)**: `[🏀] 10/5 7P` *(Warm Gold `#FFB74D`)*

---

### Technique B: Ultra-Compact Single Strings
* Shabbat Time: `6:36` (4 characters) — fits statically with 16px icon.
* Live Scores: `NY 88-85` (9 chars in compact numbers).

---

### Technique C: Selective Final Scrolling
Only trigger horizontal scrolling for finalized game results where full context is desired:
* `NY 110 - PHI 102 (Final)` in Silver (`#B0BEC5`).
