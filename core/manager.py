import time
import sys
import select

from core.monitor import create_monitors
from core.memory import get_ram
from core.dashboard import draw_dashboard
from core.watchdog import Watchdog
from core.recovery import force_stop

class Manager:

    def __init__(
        self,
        packages,
        config,
        launcher,
        joiner,
        cache_cleaner, # Terima fungsi hapus cache dari main.py
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
        self.last_cache_clear = time.time() # Start timer cache
        self.running = False

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
            # Kalau selisih waktu sekarang udah ngelewatin batas menit
            if time.time() - self.last_cache_clear >= (interval_minutes * 60):
                for pkg in self.packages:
                    try:
                        self.cache_cleaner(pkg, silent=True) # Mode senyap biar ga ngerusak dashboard
                    except Exception:
                        pass
                # Reset timer abis dibersihin
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

                # 3. Clean Cache Engine (Background Task)
                self.update_cache_cleaner()

                # 4. Dashboard
                self.update_dashboard()

                # 5. Jeda 1 detik sekalian dengerin input keyboard (Shortcut 'r' buat Reset)
                i, o, e = select.select([sys.stdin], [], [], 1)
                if i:
                    user_input = sys.stdin.readline().strip().lower()
                    
                    if user_input == 'r':
                        # Force Reset: Set semua monitor jadi Offline
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
        
