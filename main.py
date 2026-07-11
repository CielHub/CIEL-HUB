import os
import subprocess
import time
import json
from pathlib import Path

from core.manager import Manager

VERSION = "ULTIMA"

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

    print(f"                 {VERSION} (Tempest Edition)\n")


def info(msg):
    print(f"[*] {msg}")


def success(msg):
    print(f"\033[92m[+] {msg}\033[0m")


def warning(msg):
    print(f"\033[93m[!] {msg}\033[0m")


def error(msg):
    print(f"\033[91m[-] {msg}\033[0m")


def title(text):
    print(f"\n\033[96m=== {text} ===\033[0m\n")


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

CONFIG_FILE = Path.home() / ".cielhub_config.json"


DEFAULT_CONFIG = {
    "packages": [],
    "reconnect_minutes": 5,
    "force_close_delay": 30,
    "staggered_delay": 30,
    "auto_clear_cache": False,
    "discord_webhook": "", # Konfigurasi baru

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
        f"{config.get('reconnect_minutes', 5)} menit"
    )

    print(
        f"Force Close Delay       : "
        f"{config.get('force_close_delay', 30)} detik"
    )
    
    print(
        f"Staggered Delay         : "
        f"{config.get('staggered_delay', 30)} detik"
    )
    
    status_cache = "ON" if config.get("auto_clear_cache") else "OFF"
    print(
        f"Auto Clear Cache (Root) : "
        f"{status_cache}"
    )

    webhook_status = "Tersimpan" if config.get("discord_webhook") else "Kosong"
    print(
        f"Discord Webhook URL     : "
        f"{webhook_status}"
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
            reconnect = int(input("Reconnect (menit, 0=OFF): "))
            if reconnect >= 0:
                break
        except ValueError:
            pass
        warning("Masukkan angka yang valid.")

    print()

    title("FORCE CLOSE DELAY")

    while True:
        try:
            delay = int(input("Delay sebelum kill (detik): "))
            if delay >= 0:
                break
        except ValueError:
            pass
        warning("Masukkan angka yang valid.")
        
    print()

    title("STAGGERED LAUNCH DELAY")

    while True:
        try:
            stagger = int(input("Jeda antar clone in-game (detik): "))
            if stagger >= 0:
                break
        except ValueError:
            pass
        warning("Masukkan angka yang valid.")
        
    print()
    
    title("AUTO CLEAR CACHE (ROOT REQUIRED)")
    ans_cache = input("Aktifkan fitur bersihin cache tiap launch? (y/n): ").strip().lower()
    auto_cache = True if ans_cache == "y" else False
    
    print()
    
    title("DISCORD WEBHOOK NOTIFICATION")
    ans_webhook = input("Masukkan URL Webhook Discord (Kosongkan jika tidak pakai):\n> ").strip()

    config["reconnect_minutes"] = reconnect
    config["force_close_delay"] = delay
    config["staggered_delay"] = stagger
    config["auto_clear_cache"] = auto_cache
    if ans_webhook:
        config["discord_webhook"] = ans_webhook

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

    if config.get("join_method") == "private_server":
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

def clear_cache(package):
    info(f"Membersihkan cache {package}...")
    
    result = subprocess.run(
        ["su", "-c", f"rm -rf /data/data/{package}/cache/*"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    
    if result.returncode == 0:
        success(f"Cache {package} berhasil dibersihkan.")
    else:
        warning(f"Gagal bersihin cache (Pastikan punya akses Root).")


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
    cfg = load_config()
    
    if cfg.get("auto_clear_cache"):
        clear_cache(package)

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

    if config.get("join_method") != "private_server":
        return

    link = config.get("private_server_link", "").strip()

    if not link:
        warning("Private Server Link kosong.")
        return

    info("Menunggu Roblox siap...")
    time.sleep(8)

    info(f"Join Private Server untuk {package}...")

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
        success("Berhasil mengirim perintah Join Private Server.")
        return True

    error(result.stderr)
    return False
  
# ==========================================
# MAIN
# ==========================================

def main():
    os.system("stty sane")
    
    banner()

    # ==========================
    # Load Config & Menus
    # ==========================
    config = load_config()
    config = settings_menu(config)
    config = join_method_menu(config)
    print()

    # ==========================
    # Scan & Select
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

    selected = select_packages(packages)
    config["packages"] = selected
    save_config(config)

    title("PACKAGE TERPILIH")
    for package in selected:
        success(package)
    print()

    # ==========================
    # Launch & Join (Staggered)
    # ==========================
    try:
        total_clones = len(selected)

        for i, package in enumerate(selected):
            
            if smart_launch(package):
                join_private_server(package, config)
                
                if i < total_clones - 1:
                    delay = config.get("staggered_delay", 30)
                    print()
                    info(f"Menunggu {delay} detik agar {package} masuk ke in-game...")
                    
                    for remain in range(delay, 0, -1):
                        print(f"\r\033[94m[*] Lanjut ke clone berikutnya dalam {remain} detik...\033[0m  ", end="", flush=True)
                        time.sleep(1)
                    
                    print("\r" + " " * 60 + "\r", end="", flush=True)
                    print()

        success("Semua clone berhasil dijalankan.")

        # Start Manager
        manager = Manager(
            selected,
            config,
            smart_launch,
            join_private_server,
        )
        manager.start()
        
        os.system("stty sane")

    except KeyboardInterrupt:
        print()
        print("\033[93m[!] Program dihentikan paksa oleh user (Ctrl+C).\033[0m")
        print("\033[94m[*] Menghentikan seluruh clone Roblox...\033[0m")
        
        for package in selected:
            try:
                subprocess.run(["am", "force-stop", package], capture_output=True, text=True)
            except Exception:
                pass
                
        print("\033[92m[+] Semua clone berhasil di-force stop. Keluar bersih.\033[0m")
        os.system("stty sane")


if __name__ == "__main__":
    main()
    
