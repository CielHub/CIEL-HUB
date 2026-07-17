import time
import sys
import select
import urllib.request
import json
import os

from core.monitor import create_monitors
from core.memory import get_ram
from core.dashboard import draw_dashboard
from core.watchdog import Watchdog
from core.recovery import force_stop

# File buat nyimpen memori ID Panel sebelumnya
PANEL_FILE = os.path.expanduser("~/.cielhub_panel_id")

class Manager:

    def __init__(
        self,
        packages,
        config,
        launcher,
        joiner,
        cache_cleaner, 
    ):
        self.packages = packages
        self.config = config

        self.monitors = create_monitors(packages, config) 

        self.watchdog = Watchdog(
            self.monitors,
            config,
            launcher,
            joiner,
        )

        self.cache_cleaner = cache_cleaner
        self.last_cache_clear = time.time()
        
        # Variabel buat Panel Discord
        self.panel_message_id = None
        self.last_panel_update = 0
        self.webhook_url = self.config.get("discord_webhook", "").strip().rstrip("/")
        
        # Eksekusi Pembersihan Panel Lama saat script baru nyala
        if self.webhook_url:
            self.delete_old_panel()
        
        self.running = False

    # ==========================================
    # Auto-Delete Panel Lama
    # ==========================================
    def delete_old_panel(self):
        try:
            if os.path.exists(PANEL_FILE):
                with open(PANEL_FILE, "r") as f:
                    old_id = f.read().strip()
                
                # Kalau ada jejak ID lama, kirim request DELETE ke Discord
                if old_id:
                    req = urllib.request.Request(
                        f"{self.webhook_url}/messages/{old_id}",
                        headers={'User-Agent': 'Mozilla/5.0'},
                        method='DELETE'
                    )
                    urllib.request.urlopen(req, timeout=5)
                
                # Hapus file memorinya biar ga menuhin sistem
                os.remove(PANEL_FILE)
        except Exception:
            pass # Cuekin kalo error (misal pesannya udah lu hapus duluan secara manual di Discord)

    # ==========================================
    # Monitor Engine
    # ==========================================
    def update_monitors(self):
        for monitor in self.monitors:
            monitor.tick()
            monitor.update()

    # ==========================================
    # Watchdog Engine
    # ==========================================
    def update_watchdog(self):
        self.watchdog.check()

    # ==========================================
    # Auto Cache Cleaner Engine
    # ==========================================
    def update_cache_cleaner(self):
        interval_minutes = self.config.get("auto_clear_cache_minutes", 0)
        
        if interval_minutes > 0:
            if time.time() - self.last_cache_clear >= (interval_minutes * 60):
                for pkg in self.packages:
                    try:
                        self.cache_cleaner(pkg, silent=True) 
                    except Exception:
                        pass
                self.last_cache_clear = time.time()

    # ==========================================
    # Dashboard Engine
    # ==========================================
    def update_dashboard(self):
        ram_used, ram_total = get_ram()
        draw_dashboard(
            self.monitors,
            ram_used,
            ram_total,
        )

    # ==========================================
    # Discord Panel Engine
    # ==========================================
    def update_discord_panel(self):
        if not self.webhook_url:
            return

        # Jeda 5 detik tiap update biar ngga kena Limit Discord (Rate Limit)
        now = time.time()
        if now - self.last_panel_update < 5:
            return
        self.last_panel_update = now

        device_name = self.config.get("device_name", "Device-1")
        
        # Susun isi panel
        desc_lines = []
        for m in self.monitors:
            # Emoji status
            if m.status.startswith("[OK]"): icon = "🟢"
            elif m.status.startswith("[RC]"): icon = "🟡"
            elif m.status.startswith("[LO]"): icon = "🔵"
            else: icon = "🔴"

            # Ambil waktu
            if m.recovering(): timer = f"{m.recovery_remaining:02}s"
            else: timer = m.uptime()
            
            # Status text bersih
            plain_status = m.status.split("] ")[-1]
            
            desc_lines.append(f"{icon} **{m.akun_label}** - {plain_status} (`{timer}`)")

        data = {
            "embeds": [{
                "title": f"🚀 CIEL-HUB PANEL | {device_name}",
                "description": "\n\n".join(desc_lines),
                "color": 3447003, # Biru
                "footer": {"text": "Live Auto Update • Ciel-Hub"}
            }]
        }

        try:
            # Kalo pesan panel belum dibuat, kirim Pesan Baru (POST)
            if not self.panel_message_id:
                req = urllib.request.Request(
                    f"{self.webhook_url}?wait=true",
                    data=json.dumps(data).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    self.panel_message_id = resp_data.get('id')
                    
                    # SIMPAN ID PESAN BARU KE DALAM FILE MEMORI
                    try:
                        with open(PANEL_FILE, "w") as f:
                            f.write(str(self.panel_message_id))
                    except Exception:
                        pass
            
            # Kalo udah ada, Edit (PATCH) pesan yang sama biar jadi Live Panel
            else:
                req = urllib.request.Request(
                    f"{self.webhook_url}/messages/{self.panel_message_id}",
                    data=json.dumps(data).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                    method='PATCH'
                )
                urllib.request.urlopen(req, timeout=5)
        except Exception:
            # Kalau gagal (misal pesannya ga sengaja kehapus), reset ID biar bikin baru lagi
            self.panel_message_id = None

    # ==========================================
    # Main Loop
    # ==========================================
    def start(self):
        self.running = True

        try:
            while self.running:
                # 1. Update semua clone
                self.update_monitors()

                # 2. Recovery Engine
                self.update_watchdog()

                # 3. Clean Cache Engine
                self.update_cache_cleaner()

                # 4. Dashboard Termux
                self.update_dashboard()
                
                # 5. Dashboard Discord (Live Panel)
                self.update_discord_panel()

                # 6. Dengerin shortcut keyboard 'r'
                i, o, e = select.select([sys.stdin], [], [], 1)
                if i:
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == 'r':
                        # Force Reset
                        for monitor in self.monitors:
                            monitor.cancel_recovery() 
                            monitor.set_offline()     

        except KeyboardInterrupt:
            self.stop()

    # ==========================================
    # Stop
    # ==========================================
    def stop(self):
        self.running = False

        # Kill semua Roblox
        for package in self.packages:
            try:
                force_stop(package)
            except Exception:
                pass

    # ==========================================
    # Getter
    # ==========================================
    def get_monitors(self):
        return self.monitors
    
