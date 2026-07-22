import os
import subprocess
import time
import json
import random
import re
import sys
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
SILENT_MODE = False

def clear():
    os.system("clear")

def banner():
    clear()
    print("\033[96m" + r"""
   ________  ______________ 
  / ____/ / / /  _/ ____/ / 
 / /   / /_/ // // __/ / /  
/ /___/ __  // // /___/ /___
\____/_/ /_/___/_____/_____/
""" + "\033[0m")
    print(f"                 {VERSION} (Tempest Edition)\n")

def info(msg):
    if not SILENT_MODE: print(f"[*] {msg}")

def success(msg):
    if not SILENT_MODE: print(f"\033[92m[+] {msg}\033[0m")

def warning(msg):
    if not SILENT_MODE: print(f"\033[93m[!] {msg}\033[0m")

def error(msg):
    if not SILENT_MODE: print(f"\033[91m[-] {msg}\033[0m")

def title(text):
    if not SILENT_MODE: print(f"\n\033[96m=== {text} ===\033[0m\n")

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

CONFIG_FILE = Path.home() / ".chielhub_config.json"
OLD_CONFIG_FILE = Path.home() / ".cielhub_config.json" 

DEFAULT_CONFIG = {
    "packages": [],
    "reconnect_minutes": 5, 
    "force_close_delay": 30,
    "auto_clear_cache_minutes": 60, 
    "discord_bot_token": "",     
    "discord_channel_id": "",    
    "device_name": "Device-1",
    "akun_labels": {},         
    "join_method": "private_server",
    "private_server_link": "",
    "ps_tiap_akun": {},
    "place_id": "",
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    
    if OLD_CONFIG_FILE.exists() and not CONFIG_FILE.exists():
        try:
            OLD_CONFIG_FILE.rename(CONFIG_FILE)
        except Exception:
            pass

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                old = json.load(f)
            
            # Bersihin config lama biar ga nyampah
            if "staggered_delay" in old:
                del old["staggered_delay"]
            if "staggered_delay_min" in old:
                del old["staggered_delay_min"]
            if "staggered_delay_max" in old:
                del old["staggered_delay_max"]
                
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
    print(f"Auto Clear Cache        : {config.get('auto_clear_cache_minutes', 60)} menit")
    
    token_status = "Tersimpan" if config.get("discord_bot_token") else "Kosong"
    print(f"Discord Bot Token       : {token_status}")
    print(f"Discord Channel ID      : {config.get('discord_channel_id', 'Kosong')}")
    print()

    answer = input("Ubah pengaturan? (y/n): ").strip().lower()
    if answer != "y":
        info("Menggunakan konfigurasi tersimpan.")
        return config

    print()
    title("NAMA DEVICE & DISCORD BOT")
    ans_device = input(f"Masukkan Nama Device ini (Kosongi utk pakai '{config.get('device_name', 'Device-1')}'):\n> ").strip()
    if ans_device:
        config["device_name"] = ans_device
    elif not config.get("device_name"):
        config["device_name"] = "Device-1"
        
    ans_token = input("Masukkan Bot Token Discord (Kosongi jika tidak ingin mengubah):\n> ").strip()
    ans_channel = input("Masukkan Channel ID tempat bot akan nangkring (Kosongi jika tidak ingin mengubah):\n> ").strip()

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
    config["auto_clear_cache_minutes"] = cache_min
    
    if ans_token:
        config["discord_bot_token"] = ans_token
    if ans_channel:
        config["discord_channel_id"] = ans_channel

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
# LAUNCHER LOGIC
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
    if not SILENT_MODE: info(f"Menjalankan {package}...")
    
    result = subprocess.run(
        ["su", "-c", f"cmd package resolve-activity --brief {package}"],
        capture_output=True,
        text=True,
    )
    activity = None
    for line in result.stdout.splitlines():
        if "/" in line:
            activity = line.strip()
            break

    if not activity:
        activity = f"{package}/com.roblox.client.ActivitySplash"

    cmd = f"su -c \"am start -f 0x18000000 -n {activity}\""
    launch = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if launch.returncode == 0:
        if not SILENT_MODE: success(f"{package} berhasil dijalankan.")
        return True
        
    if not SILENT_MODE: error(launch.stderr)
    return False

def is_running(package):
    result = subprocess.run(["su", "-c", f"pidof {package}"], capture_output=True, text=True)
    return bool(result.stdout.strip())

def smart_launch(package):
    if not launch_package(package):
        return False
    wait_until_foreground(package)
    return True

def is_foreground(package):
    result = subprocess.run(["su", "-c", "dumpsys window"], capture_output=True, text=True)
    return package in result.stdout and "mCurrentFocus" in result.stdout

def wait_until_foreground(package, timeout=20):
    if not SILENT_MODE: info("Menunggu Roblox siap...")
    for _ in range(timeout):
        if is_foreground(package):
            if not SILENT_MODE: success("Roblox siap.")
            return True
        time.sleep(1)
    if not SILENT_MODE: warning("Timeout, lanjut eksekusi berikutnya...")
    return True

def get_link_for_pkg(pkg, config):
    method = config.get("join_method")
    if method == "private_server":
        return config.get("private_server_link", "").strip()
    elif method == "private_server_tiap_akun":
        return config.get("ps_tiap_akun", {}).get(pkg, "").strip()
    return ""

# ============================================================
# FUNGSI RECOVERY (WAKE & SHOOT) KHUSUS 1 AKUN (WATCHDOG)
# ============================================================
def join_private_server(package, config):
    link = get_link_for_pkg(package, config)
    if not link: return

    if not SILENT_MODE: info(f"Menunggu {package} siap masuk Main Menu (30s)...")
    time.sleep(30) 

    if not SILENT_MODE: info(f"Membangunkan {package} dari tidur/bubble...")
    subprocess.run(f"su -c \"monkey -p {package} -c android.intent.category.LAUNCHER 1\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    if not SILENT_MODE: info(f"Menembak Link Server ke {package}...")
    cmd = f"su -c \"am start -a android.intent.action.VIEW -d '{link}' {package}\""
    
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    # Double tap khusus Recovery tetep ada (karena cuma ngurusin 1 akun, aman)
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return True

# ==========================================
# MAIN
# ==========================================

def main():
    global SILENT_MODE 
    
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
        
        # ============================================================
        # FASE 1: BUKA SEMUA GAME DULU (RAPID FIRE)
        # ============================================================
        title("FASE 1: MEMBUKA SEMUA AKUN (RAPID FIRE)")
        for i, package in enumerate(selected):
            # Langsung force open tanpa nunggu fungsi foreground biar ngebut
            launch_package(package)
            
            if i < total_clones - 1:
                # Jeda tipis 2 detik sesuai request!
                if not SILENT_MODE: info(f"Jeda kilat 2 detik...")
                time.sleep(2)
                    
        # ============================================================
        # FASE 2: PEMATANGAN BATCH
        # ============================================================
        if not SILENT_MODE:
            print()
            info("Semua game terbuka. Menunggu 35 detik agar Main Menu matang barengan...")
        # Walau bukanya cepet, tetep butuh nunggu mereka loading dari layar hitam
        time.sleep(35)

        # ============================================================
        # FASE 3: INJEKSI MASSAL SERENTAK (FAST WAKE & SHOOT)
        # ============================================================
        title("FASE 2: INJEKSI LINK (FAST WAKE & SHOOT)")
        
        for package in selected:
            link = get_link_for_pkg(package, config)
            if link:
                if not SILENT_MODE: info(f"Wake & Shoot: {package}")
                
                # Buka balon
                subprocess.run(f"su -c \"monkey -p {package} -c android.intent.category.LAUNCHER 1\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2) # Tunggu mekar 2 detik doang
                
                # Tembak Jantung
                cmd = f"su -c \"am start -a android.intent.action.VIEW -d '{link}' {package}\""
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(3) # Kasih napas 3 detik buat nangkep link sebelum pindah ke clone sebelah

        success("Seluruh fase Injeksi Massal berhasil dieksekusi!")
        time.sleep(2)

        # ==========================================
        # TRANSISI KE DASHBOARD
        # ==========================================
        
        SILENT_MODE = True 

        sys.stdout.write('\033c\033[2J\033[3J\033[H')
        sys.stdout.flush()

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
