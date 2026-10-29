# witool
> CLI-based wireless penetration testing tool for Linux.

`witool` is a lightweight, automated command-line utility designed to streamline Wi-Fi security auditing, including monitor mode management, WPS status scanning, EAPOL handshake capture with automatic deauth, and WPS Pixie Dust attacks.

---

## Features
- **Smart CLI Interface:** Clean flag-based commands (`--monitor`, `--scan`, `--capture`, `--wps`, `--normal`).
- **Auto-Interface Persistence:** Remembers your active monitor interface automatically across commands.
- **Automated Deauth & Handshake Capture:** Automatically triggers deauth packets and validates captured handshakes (`aircrack-ng` integration).
- **Graceful Cleanup:** Automatically restores `NetworkManager` and managed mode on exit (`Ctrl+C` safe).

---

## Prerequisites
Ensure the following tools are installed on your Linux system:
- `aircrack-ng` (includes `airmon-ng`, `airodump-ng`, `aireplay-ng`)
- `reaver` (includes `wash`)

---

## Installation

Clone the repository and install it globally:

```bash
git clone [https://github.com/hex277/witool.git](https://github.com/hex277/witool.git)
cd witool
chmod +x witool.py
sudo cp witool.py /usr/bin/witool

Disclaimer

This tool is created for educational and authorized security auditing purposes only. Unauthorized testing against networks you do not own or have explicit permission to test is illegal.
