import time

from core.monitor import create_monitors
from core.memory import get_ram
from core.dashboard import draw_dashboard
from core.watchdog import Watchdog


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

        self.monitors = create_monitors(packages)

        self.watchdog = Watchdog(
            self.monitors,
            config,
            launcher,
            joiner,
        )

        self.running = False

    # ==========================================
    # Dashboard
    # ==========================================

    def update_dashboard(self):

        ram_used, ram_total = get_ram()

        draw_dashboard(
            self.monitors,
            ram_used,
            ram_total,
        )

    # ==========================================
    # Monitor Update
    # ==========================================

    def update_monitors(self):

        for monitor in self.monitors:

            # Countdown recovery
            monitor.tick()

            # Update process status
            monitor.update()

    # ==========================================
    # Main Loop
    # ==========================================

    def start(self):

        self.running = True

        try:

            while self.running:

                # 1. Update semua monitor
                self.update_monitors()

                # 2. Jalankan watchdog
                self.watchdog.check()

                # 3. Refresh dashboard
                self.update_dashboard()

                # 4. Refresh tiap 1 detik
                time.sleep(1)

        except KeyboardInterrupt:

            self.stop()

    # ==========================================
    # Stop
    # ==========================================

    def stop(self):

        self.running = False

    # ==========================================
    # Getter
    # ==========================================

    def get_monitors(self):

        return self.monitors