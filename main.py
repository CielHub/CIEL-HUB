import os
import subprocess
import time
import json
import random
import re
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
    "staggered_delay_min": 25,
    "staggered_delay_max": 40,
    "auto_clear_cache_minutes": 60, 
    "discord_webhook": "", 
    "device_name": "Device-1",
    "akun_labels": {},         
    "join_method": "private_server",
    "private_server_link": "",
    "ps_tiap_akun": {},
    "place_id": "",
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                old = json.load(f)
            
            if "staggered_delay" in old:
                old["staggered_delay_min"] = old["staggered_delay"]
                old["staggered_delay_max"] = old["staggered_delay"] + 10
                del old["staggered_delay"]
                
            if "auto_clear_cache" in old:
                old["auto_clear_cache_minutes"] = 60 if old["auto_clear_cache"] else 0
                del old["auto_clear_cache"]

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
    print(f"Device Name             : {config.get('device_name', 'Device-1')}")
    print(f"Reconnect saat ini      : {config.get('reconnect_minutes', 5)} menit")
    print(f"Force Close Delay       : {config.get('force_close_delay', 30)} detik")
    print(f"Staggered Delay (Acak)  : {config.get('staggered_delay_min', 25)} - {config.get('staggered_delay_max', 40)} detik")
    print(f"Auto Clear Cache        : {config.get('auto_clear_cache_minutes', 60)} menit")

    webhook_status = "Tersimpan" if config.get("discord_webhook") else "Kosong"
    print(f"Discord Webhook URL     : {webhook_status}")
    print()

    answer = input("Ubah pengaturan? (y/n): ").strip().lower()
    if answer != "y":
        info("Menggunakan konfigurasi tersimpan.")
        return config

    print()
    title("NAMA DEVICE & WEBHOOK")
    ans_device = input(f"Masukkan Nama Device ini (Kosongi utk pakai '{config.get('device_name', 'Device-1')}'):\n> ").strip()
    if ans_device:
        config["device_name"] = ans_device
    elif not config.get("device_name"):
        config["device_name"] = "Device-1"
        
    ans_webhook = input("Masukkan URL Webhook Discord (Kosongkan jika tidak pakai):\n> ").strip()

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
    title("STAGGERED LAUNCH DELAY (ANTI-BOT)")
    info("Sistem akan memilih waktu tunggu secara acak di antara dua nilai ini.")
    while True:
        try:
            stagger_min = int(input("Jeda MINIMAL antar clone (detik): "))
            stagger_max = int(input("Jeda MAKSIMAL antar clone (detik): "))
            if stagger_min >= 0 and stagger_max >= stagger_min:
                break
            else:
                warning("Input tidak valid. Pastikan Maksimal lebih besar atau sama dengan Minimal.")
        except ValueError:
            pass
        warning("Masukkan angka yang valid.")
        
    print()
    title("AUTO CLEAR CACHE (ROOT REQUIRED)")
    info("Bersihkan cache otomatis tiap durasi tertentu (saat game jalan) biar ngga lag.")
    while True:
        try:
            cache_min = int(input("Interval bersihkan cache (menit, 0=OFF): "))
            if cache_min >= 0:
                break
        except ValueError:
            pass
        warning("Masukkan angka valid (Misal: 60).")
    

    config["reconnect_minutes"] = reconnect
    config["force_close_delay"] = delay
    config["staggered_delay_min"] = stagger_min
    config["staggered_delay_max"] = stagger_max
    config["auto_clear_cache_minutes"] = cache_min
    if ans_webhook:
        config["discord_webhook"] = ans_webhook

    save_config(config)
    print()
    success("Konfigurasi berhasil disimpan.")
    return config


# ==========================================
# JOIN METHOD
# ==========================================

def verify_ps_tiap_akun(config, selected_packages):
    if "ps_tiap_akun" not in config:
        config["ps_tiap_akun"] = {}
    ada_perubahan = False
    print("\n[*] Mengecek data Link PS untuk setiap akun...")
    
    for i, pkg in enumerate(selected_packages, start=1):
        # Kalau belum kedetect username, bakal nampilin nama package nya dulu buat identifikasi
        label = config.get("akun_labels", {}).get(pkg, pkg.replace("com.roblox.", ""))
        if pkg not in config["ps_tiap_akun"] or config["ps_tiap_akun"][pkg] == "":
            link = input(f"[>] Masukkan Link PS khusus untuk akun [{label}]:\n> ").strip()
            config["ps_tiap_akun"][pkg] = link
            ada_perubahan = True
        else:
            success(f"Akun [{label}] : Link PS sudah tersimpan.")

    if ada_perubahan:
        save_config(config)
        success("Data Private Server tiap akun berhasil diperbarui!")
    return config

def join_method_menu(config, selected_packages):
    print()
    title("METODE JOIN")
    current_method = config.get("join_method")
    
    if current_method == "private_server":
        current = "1. Private Server (Global)"
    elif current_method == "private_server_tiap_akun":
        current = "2. Private Server (Tiap Akun)"
    else:
        current = "3. Place ID"

    print(f"Metode saat ini : {current}\n")
    answer = input("Ubah metode join? (y/n): ").strip().lower()

    if answer != "y":
        info("Menggunakan metode yang tersimpan.")
        if current_method == "private_server_tiap_akun":
            config = verify_ps_tiap_akun(config, selected_packages)
        return config

    print("\n[1] Private Server (Global)")
    print("[2] Private Server (Tiap Akun)")
    print("[3] Place ID\n")

    while True:
        choice = input("Pilih metode (1/2/3): ").strip()
        if choice == "1":
            title("PRIVATE SERVER (GLOBAL)")
            link = input("Masukkan Private Server Link:\n> ").strip()
            config["join_method"] = "private_server"
            config["private_server_link"] = link
            config["place_id"] = ""
            break
        elif choice == "2":
            title("PRIVATE SERVER (TIAP AKUN)")
            config["join_method"] = "private_server_tiap_akun"
            config = verify_ps_tiap_akun(config, selected_packages)
            break
        elif choice == "3":
            title("PLACE ID")
            place = input("Masukkan Place ID:\n> ").strip()
            config["join_method"] = "place_id"
            config["place_id"] = place
            config["private_server_link"] = ""
            break
        else:
            warning("Pilihan tidak valid.")

    save_config(config)
    print("\n\033[92m[+] Metode join berhasil disimpan.\033[0m")
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
            warning("Nomor tidak valid: " + ", ".join(invalid))
        if selected:
            return selected
        warning("Tidak ada package yang dipilih.")

# ==========================================
# LAUNCHER & AUTO-DETECT LOGIC
# ==========================================

def clear_cache(package, silent=False):
    if not silent:
        info(f"Membersihkan cache {package}...")
    
    result = subprocess.run(
        ["su", "-c", f"rm -rf /data/data/{package}/cache/*"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    
    if not silent:
        if result.returncode == 0:
            success(f"Cache {package} berhasil dibersihkan.")
        else:
            warning(f"Gagal bersihin cache (Pastikan punya akses Root).")


def launch_package(package):
    info(f"Menjalankan {package}...")
    result = subprocess.run(
        ["cmd", "package", "resolve-activity", "--brief", package],
        capture_output=True,
        text=True,
    )
    activity = None
    for line in result.stdout.splitlines():
        if "/" in line:
            activity = line.strip()
            break

    if not activity:
        candidates = [
            f"{package}/com.roblox.client.startup.ActivitySplash",
            f"{package}/com.roblox.client.ActivitySplash",
            f"{package}/com.roblox.client.MainActivity",
        ]
        for act in candidates:
            test = subprocess.run(["am", "start", "-n", act], capture_output=True, text=True)
            if test.returncode == 0:
                success(f"{package} berhasil dijalankan.")
                return True
        error(f"Gagal menemukan Activity untuk {package}")
        return False

    launch = subprocess.run(["am", "start", "-n", activity], capture_output=True, text=True)
    if launch.returncode == 0:
        success(f"{package} berhasil dijalankan.")
        return True
    error(launch.stderr)
    return False


def is_running(package):
    result = subprocess.run(["pidof", package], capture_output=True, text=True)
    return bool(result.stdout.strip())

def smart_launch(package):
    if not launch_package(package):
        return False
    wait_until_foreground(package)
    return True

def is_foreground(package):
    result = subprocess.run(["/system/bin/dumpsys", "window"], capture_output=True, text=True)
    return package in result.stdout and "mCurrentFocus" in result.stdout

def wait_until_foreground(package, timeout=20):
    info("Menunggu Roblox siap...")
    for _ in range(timeout):
        if is_foreground(package):
            success("Roblox siap.")
            return True
        time.sleep(1)
    warning("Timeout, lanjut eksekusi berikutnya...")
    return True

def detect_single_username(pkg, config, index):
    """Jalanin ini persis setelah game masuk ke foreground biar datanya fresh"""
    if "akun_labels" not in config:
        config["akun_labels"] = {}
        
    short_pkg = pkg.replace("com.roblox.", "")
    
    # Kalo labelnya masih kosong atau masih pake nama package default
    if pkg not in config["akun_labels"] or config["akun_labels"][pkg] == "" or config["akun_labels"][pkg] == short_pkg:
        info(f"Mencoba deteksi otomatis Username dari {short_pkg}...")
        username = None
        
        try:
            # Kasih jeda dikit biar game sempet nulis data xml ke storage
            time.sleep(2)
            cmd = ["su", "-c", f"cat /data/data/{pkg}/shared_prefs/*.xml"]
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.DEVNULL)
            output = result.stdout
            
            # Scan 1: Format XML standar
            match = re.search(r'(?i)<string name="[^"]*username[^"]*">([^<]+)</string>', output)
            if match:
                username = match.group(1).strip()
            else:
                # Scan 2: Kalau formatnya JSON atau raw text
                match_alt = re.search(r'(?i)"username"\s*:\s*"([^"]+)"', output)
                if match_alt:
                    username = match_alt.group(1).strip()
        except Exception:
            pass
            
        if username:
            success(f"Akun {index} : Berhasil mendeteksi otomatis [{username}]")
            config["akun_labels"][pkg] = username
        else:
            warning(f"Gagal mendeteksi otomatis Username.")
            print("\033[93m[!] Silakan kembali ke Termux sebentar untuk input nama manual!\033[0m")
            label = input(f"[>] Masukkan Nama Akun manual untuk clone {short_pkg}:\n> ").strip()
            config["akun_labels"][pkg] = label if label else short_pkg
            
        save_config(config)
    return config

def join_private_server(package, config):
    method = config.get("join_method")
    
    if method == "private_server":
        link = config.get("private_server_link", "").strip()
    elif method == "private_server_tiap_akun":
        link = config.get("ps_tiap_akun", {}).get(package, "").strip()
    else:
        return

    if not link:
        warning(f"Private Server Link untuk {package} kosong/tidak ditemukan.")
        return

    info("Menunggu sebentar sebelum Join...")
    time.sleep(5)
    info(f"Join Private Server untuk {package}...")

    result = subprocess.run(
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", link, package],
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

    config = load_config()
    config = settings_menu(config)
    print()

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

    config = join_method_menu(config, selected)
    print()

    try:
        total_clones = len(selected)
        for i, package in enumerate(selected):
            # 1. Buka gamenya dulu
            if smart_launch(package):
                
                # 2. SEKARANG baru kita deteksi pas udah masuk game (Flow baru)
                config = detect_single_username(package, config, i + 1)
                
                # 3. Lanjut Join
                join_private_server(package, config)
                
                # 4. Tunggu Delay Acak sebelum akun berikutnya
                if i < total_clones - 1:
                    min_delay = config.get("staggered_delay_min", 25)
                    max_delay = config.get("staggered_delay_max", 40)
                    delay = random.randint(min_delay, max_delay)
                    
                    print()
                    info(f"Menunggu {delay} detik (Acak) agar {package} masuk ke in-game...")
                    for remain in range(delay, 0, -1):
                        print(f"\r\033[94m[*] Lanjut ke clone berikutnya dalam {remain} detik...\033[0m  ", end="", flush=True)
                        time.sleep(1)
                    print("\r" + " " * 60 + "\r", end="", flush=True)
                    print()

        success("Semua clone berhasil dijalankan.")

        # Kirim config terbaru yang udah ada labelnya ke Manager biar Webhooknya bener
        manager = Manager(
            selected,
            config,
            smart_launch,
            join_private_server,
            clear_cache,
        )
        manager.start()
        
        os.system("stty sane")

    except KeyboardInterrupt:
        print()
        warning("Program dihentikan paksa oleh user (Ctrl+C).")
        info("Menghentikan seluruh clone Roblox...")
        for package in selected:
            try:
                subprocess.run(["am", "force-stop", package], capture_output=True, text=True)
            except Exception:
                pass
        success("Semua clone berhasil di-force stop. Keluar bersih.")
        os.system("stty sane")

if __name__ == "__main__":
    main()
            
