
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
    ):

        self.packages = packages
        self.config = config

        # Nambahin config kesini biar bisa dipake buat Discord Webhook
        self.monitors = create_monitors(packages, config) 

        self.watchdog = Watchdog(
            self.monitors,
            config,
            launcher,
            joiner,
        )

        self.running = False

    # ==========================================
    # Monitor Engine
    # ==========================================

    def update_monitors(self):

        for monitor in self.monitors:

            # Countdown Recovery
            monitor.tick()

            # Process Detection
            monitor.update()

    # ==========================================
    # Watchdog Engine
    # ==========================================

    def update_watchdog(self):

        self.watchdog.check()

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

                # Update semua clone
                self.update_monitors()

                # Recovery Engine
                self.update_watchdog()

                # Dashboard
                self.update_dashboard()

                # Jeda 1 detik sekalian dengerin input keyboard
                # Kalau user ngetik 'r' lalu Enter, paksa reset status
                i, o, e = select.select([sys.stdin], [], [], 1)
                
                if i:
                    user_input = sys.stdin.readline().strip().lower()
                    
                    if user_input == 'r':
                        # Force Reset: Set semua monitor jadi Offline
                        for monitor in self.monitors:
                            monitor.cancel_recovery() # Batalin kalau ada yg nyangkut recover
                            monitor.set_offline()     # Paksa offline biar Watchdog kerja lagi

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
        
