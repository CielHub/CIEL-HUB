import os
import subprocess
import time

from core.manager import Manager

VERSION = "v3.1.0"

ROBLOX_KEYWORDS = (
    "roblox",
    "rbx",
)


# ==========================================
# UI
# ==========================================

def clear():
    os.system("clear")


def banner():
    clear()

    print(r"""
 ██████╗██╗███████╗██╗         ██╗  ██╗██╗   ██╗██████╗
██╔════╝██║██╔════╝██║         ██║  ██║██║   ██║██╔══██╗
██║     ██║█████╗  ██║         ███████║██║   ██║██████╔╝
██║     ██║██╔══╝  ██║         ██╔══██║██║   ██║██╔══██╗
╚██████╗██║███████╗███████╗    ██║  ██║╚██████╔╝██████╔╝
 ╚═════╝╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
""")

    print(f"                 {VERSION} (Termux Edition)\n")


def info(msg):
    print(f"[*] {msg}")


def success(msg):
    print(f"[+] {msg}")


def warning(msg):
    print(f"[!] {msg}")


def error(msg):
    print(f"[-] {msg}")


def title(text):
    print(f"\n=== {text} ===\n")


# ==========================================
# SCANNER
# ==========================================

def scan_packages():

    result = subprocess.run(
        ["pm", "list", "packages"],
        capture_output=True,
        text=True,
    )

    packages = []

    for line in result.stdout.splitlines():

        if not line.startswith("package:"):
            continue

        package = (
            line.replace("package:", "")
            .replace("\r", "")
            .replace("\t", "")
            .strip()
        )

        if any(keyword in package.lower() for keyword in ROBLOX_KEYWORDS):
            packages.append(package)

    packages = sorted(set(packages))

    return packages


# ==========================================
# CONFIG
# ==========================================

import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".cielhub_config.json"


DEFAULT_CONFIG = {
    "packages": [],
    "reconnect_minutes": 5,
    "force_close_delay": 30,

    "join_method": "private_server",
    "private_server_link": "",
    "place_id": "",
}


def load_config():

    config = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():

        try:
            with open(CONFIG_FILE, "r") as f:
                old = json.load(f)

            config.update(old)

        except Exception:
            pass

    return config


def save_config(config):

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ==========================================
# SETTINGS
# ==========================================

def settings_menu(config):

    print()

    title("PENGATURAN")

    print(
        f"Reconnect saat ini      : "
        f"{config['reconnect_minutes']} menit"
    )

    print(
        f"Force Close Delay       : "
        f"{config['force_close_delay']} detik"
    )

    print()

    answer = input(
        "Ubah pengaturan? (y/n): "
    ).strip().lower()

    if answer != "y":
        info("Menggunakan konfigurasi tersimpan.")
        return config

    print()

    title("AUTO RECONNECT")

    while True:

        try:

            reconnect = int(
                input(
                    "Reconnect (menit, 0=OFF): "
                )
            )

            if reconnect >= 0:
                break

        except ValueError:
            pass

        warning("Masukkan angka yang valid.")

    print()

    title("FORCE CLOSE DELAY")

    while True:

        try:

            delay = int(
                input(
                    "Delay (detik): "
                )
            )

            if delay >= 0:
                break

        except ValueError:
            pass

        warning("Masukkan angka yang valid.")

    config["reconnect_minutes"] = reconnect
    config["force_close_delay"] = delay

    save_config(config)

    print()

    success("Konfigurasi berhasil disimpan.")

    return config


# ==========================================
# JOIN METHOD
# ==========================================

def join_method_menu(config):

    print()

    title("METODE JOIN")

    if config["join_method"] == "private_server":
        current = "Private Server"

    else:
        current = "Place ID"

    print(f"Metode saat ini : {current}")
    print()

    answer = input("Ubah metode join? (y/n): ").strip().lower()

    if answer != "y":

        info("Menggunakan metode yang tersimpan.")
        return config

    print()

    print("[1] Private Server")
    print("[2] Place ID")
    print()

    while True:

        choice = input("Pilih metode: ").strip()

        if choice == "1":

            title("PRIVATE SERVER")

            link = input(
                "Masukkan Private Server Link:\n> "
            ).strip()

            config["join_method"] = "private_server"
            config["private_server_link"] = link
            config["place_id"] = ""

            break

        elif choice == "2":

            title("PLACE ID")

            place = input(
                "Masukkan Place ID:\n> "
            ).strip()

            config["join_method"] = "place_id"
            config["place_id"] = place
            config["private_server_link"] = ""

            break

        else:

            warning("Pilihan tidak valid.")

    save_config(config)

    print()

    success("Metode join berhasil disimpan.")

    return config
  
# ==========================================
# PACKAGE SELECTOR
# ==========================================

def select_packages(packages):

    while True:

        print()
        info("Pisahkan dengan koma (Contoh: 1,2,3)")

        raw = input("Pilih nomor aplikasi: ").strip()

        if not raw:
            warning("Input tidak boleh kosong.")
            continue

        selected = []
        invalid = []

        for item in raw.split(","):

            item = item.strip()

            if not item.isdigit():
                invalid.append(item)
                continue

            index = int(item)

            if 1 <= index <= len(packages):
                package = packages[index - 1]

                if package not in selected:
                    selected.append(package)
            else:
                invalid.append(item)

        if invalid:
            warning(
                "Nomor tidak valid: " +
                ", ".join(invalid)
            )

        if selected:
            return selected

        warning("Tidak ada package yang dipilih.")


# ==========================================
# LAUNCHER
# ==========================================

def launch_package(package):
    info(f"Menjalankan {package}...")

    # Cari activity launcher
    result = subprocess.run(
        [
            "cmd",
            "package",
            "resolve-activity",
            "--brief",
            package,
        ],
        capture_output=True,
        text=True,
    )

    activity = None

    for line in result.stdout.splitlines():
        if "/" in line:
            activity = line.strip()
            break

    # Fallback jika resolve-activity gagal
    if not activity:
        candidates = [
            f"{package}/com.roblox.client.startup.ActivitySplash",
            f"{package}/com.roblox.client.ActivitySplash",
            f"{package}/com.roblox.client.MainActivity",
        ]

        for act in candidates:
            test = subprocess.run(
                ["am", "start", "-n", act],
                capture_output=True,
                text=True,
            )

            if test.returncode == 0:
                success(f"{package} berhasil dijalankan.")
                return True

        error(f"Gagal menemukan Activity untuk {package}")
        return False

    launch = subprocess.run(
        [
            "am",
            "start",
            "-n",
            activity,
        ],
        capture_output=True,
        text=True,
    )

    if launch.returncode == 0:
        success(f"{package} berhasil dijalankan.")
        return True

    error(launch.stderr)
    return False


def is_running(package):

    result = subprocess.run(
        ["pidof", package],
        capture_output=True,
        text=True,
    )

    return bool(result.stdout.strip())


def smart_launch(package):

    if not launch_package(package):
        return False

    wait_until_foreground(package)

    return True


def is_foreground(package):

    result = subprocess.run(
        ["/system/bin/dumpsys", "window"],
        capture_output=True,
        text=True,
    )

    output = result.stdout

    return package in output and "mCurrentFocus" in output

def wait_until_foreground(package, timeout=20):

    info("Menunggu Roblox siap...")

    for _ in range(timeout):

        if is_foreground(package):
            success("Roblox siap.")
            return True

        time.sleep(1)

    warning("Timeout, lanjut join...")
    return True

def join_private_server(package, config):

    if config["join_method"] != "private_server":
        return

    link = config["private_server_link"].strip()

    if not link:
        warning("Private Server Link kosong.")
        return

    info("Menunggu Roblox siap...")
    time.sleep(8)

    info("Join Private Server...")

    result = subprocess.run(
        [
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            link,
            package,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        success("Berhasil Join Private Server.")
        return True

    error(result.stderr)
    return False
  
# ==========================================
# MAIN
# ==========================================

# ==========================================
# MAIN
# ==========================================

def main():

    banner()

    # ==========================
    # Load Config
    # ==========================

    config = load_config()

    config = settings_menu(config)
    config = join_method_menu(config)

    print()

    # ==========================
    # Scan Roblox
    # ==========================

    info("Memindai package Roblox...")

    packages = scan_packages()

    if not packages:
        error("Tidak ada package Roblox ditemukan.")
        return

    success(f"Ditemukan {len(packages)} package.")

    title("DAFTAR APLIKASI ROBLOX")

    for index, package in enumerate(packages, start=1):
        print(f"[{index}] {package}")

    # ==========================
    # Pilih Package
    # ==========================

    selected = select_packages(packages)

    config["packages"] = selected
    save_config(config)

    title("PACKAGE TERPILIH")

    for package in selected:
        success(package)

    print()

    # ==========================
    # Launch & Join
    # ==========================

    for package in selected:

        if smart_launch(package):

            join_private_server(package, config)

    success("Semua clone berhasil dijalankan.")

    # ==========================
    # Start Manager
    # ==========================

    manager = Manager(
        selected,
        config,
        smart_launch,
        join_private_server,
    )

    manager.start()


if __name__ == "__main__":
    main()