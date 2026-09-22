# Troubleshooting & Operational Guide

This document covers common diagnostic scenarios, battery behaviors, network IP shifts, and recovery procedures for the Ulanzi TC002 with AWTRIX NG.

---

## 1. Battery Telemetry & 0% Pre-Charge Recovery

### Symptoms:
* The clock ran completely out of battery and turned off.
* After plugging in USB power, the display and API report `batteryPercent: 0%` for 15–30 minutes.

### Root Cause:
* The TC002 uses a 3.7V nominal Li-ion cell.
* When drained completely, cell voltage drops below 3.0V (e.g. `2.25V`).
* The firmware calculates percentage using the discharge curve:
  $$\text{Percent} = \max\left(0, \min\left(100, \frac{V - 3.20\text{V}}{4.20\text{V} - 3.20\text{V}} \times 100\right)\right)$$
* As long as $V < 3.20\text{V}$, the percentage mathematically clamps to **`0%`**.
* The hardware charger IC safely applies **trickle charge** until voltage exceeds 3.0V–3.2V.

### Verification Command:
Check real-time voltage rise:
```bash
curl -s -u <USER>:<PASS> http://<CLOCK_IP>:8080/api/v1/device | jq '{batteryPercent, batteryVoltage, batteryPinMillivolts}'
```
If `batteryPinMillivolts` is continuously rising (e.g. `2250` ➔ `2500` ➔ `2720`), the battery is actively charging and will begin reporting percentage once it reaches ~3.25V.

---

## 2. Clock IP Changes (DHCP Subnet Sweep)

If the clock reboots and receives a new IP address, use the fast concurrent discovery scanner (adjust subnet as appropriate):

```bash
python3 -c '
import socket, concurrent.futures

SUBNET_PREFIX = "<local-subnet>."  # Adjust for your LAN

def check(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    if s.connect_ex((ip, 8080)) == 0:
        return ip
    s.close()
    return None

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    for ip in ex.map(check, [f"{SUBNET_PREFIX}{i}" for i in range(1, 255)]):
        if ip: print(f"Found AWTRIX clock at http://{ip}:8080")
'
```

---

## 3. ADB Wireless Management

Connect to ADB over Wi-Fi:
```bash
./adb connect <CLOCK_IP>:5555
```

List installed flash icons:
```bash
./adb -s <CLOCK_IP>:5555 shell ls -la /data/awtrix-ng/ICONS
```

Push new icon to flash:
```bash
./adb -s <CLOCK_IP>:5555 push icons/cake.gif /data/awtrix-ng/ICONS/cake.gif
```

---

## 4. Watchdog & Stock Firmware Rollback

If the knob is held during power-on, or if AWTRIX NG crashes 3 times during startup:
* The system falls back to launching the stock Ulanzi UI (`zkswe`).
* **Fix**: Ensure port 80 is not used (`"webPort": 8080` in `/data/awtrix-ng/device.json`).
