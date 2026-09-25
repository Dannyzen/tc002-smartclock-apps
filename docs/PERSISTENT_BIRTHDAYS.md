# Persistent Birthday Runtime Configuration

Birthday records are runtime-only data. This repository contains no Birthday names, dates, colors, examples, or configuration files.

## Runtime secret

Store `BIRTHDAYS_JSON_B64` in Infisical. It is a base64-encoded JSON array injected only into the process that runs the installer or legacy fallback. Do not print it, put it in the repository source, commit it, attach it to an issue, or include it in logs.

The installer requires this variable and validates the decoded records before making any Clock request. The host-pushed fallback renders no Birthday cards when the variable is missing or invalid.

## Installation

1. Inject `AWTRIX_HOST`, `AWTRIX_USER`, `AWTRIX_PASS`, and `BIRTHDAYS_JSON_B64` from the approved runtime secret path.
2. Run the installer without `--apply` to validate the runtime payload and inspect the plan locally.
3. Run with `--apply` only after explicit device-write approval.
4. Confirm the Clock inventory reports the expected script count, origin, enabled state, and loop state.

The installer writes sequentially. A failed apply can leave earlier scripts installed. It rejects logical AWTRIX errors and requires a final app-inventory readback before success.

## Proof boundary

Source tests and API inventory prove payload validation and installation protocol. Physical rendering, visible dwell, midnight rollover, and reboot persistence require separate device evidence.
