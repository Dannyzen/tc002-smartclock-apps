# AWTRIX NG TC002 System Architecture

This document describes the internal hardware and firmware architecture of the **Ulanzi TC002 Smart Pixel Clock** running **AWTRIX NG**.

---

## 1. Hardware Specifications

* **Processor (SoC)**: Allwinner SSD202D (Dual-Core ARM Cortex-A7 @ 1.2 GHz)
* **RAM**: 128 MB DDR3 (integrated inside SoC package)
* **Storage**: 32 MB SPI NOR Flash (Winbond/Macronix) — **No external MicroSD slot**
* **Display Matrix**: 52 wide × 16 high RGB LED matrix (832 discrete WS2812B/SK6812-compatible pixels)
* **Power & Battery**: 2500 mAh 3.7V / 4.2V Li-ion cell charged via USB Type-C
* **Connectivity**: 2.4 GHz 802.11 b/g/n Wi-Fi (SSV6x5x / RTL8189 chipset)
* **Audio / Buzzer**: Integrated mono speaker / buzzer driven via `/dev/snd`

---

## 2. Flash Partition Layout & JFFS2 Storage

The 32 MB SPI NOR flash is divided into MTD partitions:

| Partition | Mount Point | Filesystem | Size | Description |
|---|---|---|---|---|
| `mtd0` | `/boot` | Raw / U-Boot | ~1 MB | U-Boot bootloader & environment |
| `mtd1` | `/` | SquashFS (read-only) | ~8 MB | Linux rootfs (kernel 4.9.84) |
| `mtd2` | `/customer` | SquashFS / JFFS2 | ~12 MB | Vendor binaries (`zkswe`, `zkdaemon`, `zkgui`) |
| `mtd3` | `/data` | **JFFS2 (read-write)** | **~8 MB** | **Persistent application & user storage** |

### `/data/awtrix-ng/` Directory Tree
All persistent configuration, icons, and scripts reside in `/data/awtrix-ng`:
```text
/data/awtrix-ng/
├── .wifi-applied           # Wi-Fi configuration cache
├── device.json             # Hardware config (webPort: 8080, matrix power, etc.)
├── settings.json           # Runtime settings (transition speed, brightness, etc.)
├── launcher.log            # Boot watchdog and handover logs
├── ICONS/                  # Persistent 16x16 pixel-art GIF icons
│   ├── candle.gif          # Flickering Shabbat candles
│   ├── cake.gif            # Birthday cake with flickering flame
│   └── basketball.gif      # NBA basketball with black seams
└── SCRIPTS/                # Persistent .ax Berry script apps
    ├── shabbat.ax
    ├── bday_zach.ax
    ├── bday_jared.ax
    └── nyk.ax
```

---

## 3. The Port 80 Conflict & Watchdog Mechanism

> [!CAUTION]
> On the stock partition, the stock vendor UI daemon (`zkdaemon`) binds to port 80.

1. If AWTRIX NG is configured with `"webPort": 80`, it fails to bind (`sim http: cannot bind port 80`).
2. The boot launcher detects the crash and increments `/data/awtrix-ng/launcher.log` (`attempt 1 of 3`).
3. If AWTRIX fails **3 consecutive times**, the watchdog permanently falls back to launching the stock Ulanzi UI (`zkswe`).
4. **Resolution**: Always ensure `"webPort": 8080` in `/data/awtrix-ng/device.json`.

---

## 4. Boot Sequence

```mermaid
flowchart TD
    A[Power On / Reset] --> B[U-Boot 2015.01]
    B --> C[Linux Kernel 4.9.84]
    C --> D[/etc/init.rc]
    D --> E{Knob pressed at boot?}
    E -- Yes --> F[Start Stock Vendor UI 'zkswe']
    E -- No --> G[AWTRIX Launcher]
    G --> H{AWTRIX healthy < 3 crashes?}
    H -- No --> F
    H -- Yes --> I[Launch /customer/awtrix-tc002 on port 8080]
    I --> J[Load ICONS & SCRIPTS from /data/awtrix-ng/]
    J --> K[Start App Carousel Loop]
```
