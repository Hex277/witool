# witool 
> CLI-based wireless penetration testing tool for Linux.

`witool` is a lightweight, automated command-line utility designed to streamline Wi-Fi security auditing, including monitor mode management, WPS status scanning, EAPOL handshake capture with automatic deauth, and WPS Pixie Dust attacks.

---

## Features
- **Smart CLI Interface:** Clean flag-based commands (`--monitor`, `--scan`, `--capture`, `--wps`, `--normal`).
- **Auto-Interface Persistence:** Remembers your active monitor interface automatically across commands.
- **Automated Deauth & Handshake Capture:** Automatically triggers deauth packets, validates captured handshakes (`aircrack-ng` integration), and cleans up junk files.
- **Graceful Cleanup:** Automatically restores `NetworkManager` and managed mode on exit (`Ctrl+C` safe).

---

## Prerequisites
Ensure the following tools are installed on your Linux system:
- `aircrack-ng` (includes `airmon-ng`, `airodump-ng`, `aireplay-ng`)
- `reaver` (includes `wash`)

---

## Installation

You can install `witool` globally via pip:

```bash
pip install witool

