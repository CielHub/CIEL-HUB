import threading
from core.recovery import recover

class Watchdog:

    def __init__(
        self,
        monitors,
        config,
        launcher,
        joiner,
    ):
        self.monitors = monitors
        self.config = config
        self.launcher = launcher
        self.joiner = joiner

    # ==========================================
    # Check Clone
    # ==========================================

    def check(self):
        reconnect_minutes = self.config.get(
            "reconnect_minutes",
            0,
        )

        delay = self.config.get(
            "force_close_delay",
            45,
        )

        for monitor in self.monitors:

            # =====================================
            # Skip jika sedang recovery
            # =====================================
            if monitor.recovering():
                pass

            # =====================================
            # Auto Recovery berdasarkan Timer
            # =====================================
            elif (
                reconnect_minutes > 0
                and monitor.recover_elapsed()
                >= reconnect_minutes * 60
            ):
                monitor.start_recovery(delay)

            # =====================================
            # Auto Recovery jika Offline
            # =====================================
            elif monitor.offline():
                monitor.start_recovery(delay)

            # =====================================
            # Clone masih Farming
            # =====================================
            else:
                continue

            # =====================================
            # Countdown selesai
            # =====================================
            if monitor.recovery_finished():
                
                # Tandai kalau proses recovery udah dimulai biar ga ditimpa
                monitor.mark_recovery_started()

                # --- IMPLEMENTASI MULTITHREADING ---
                # Bikin fungsi pembungkus buat dijalanin di latar belakang
                def background_recovery(pkg_monitor):
                    success = recover(
                        pkg_monitor.package,
                        self.config,
                        pkg_monitor,
                        self.launcher,
                        self.joiner,
                    )
                    
                    if not success:
                        pkg_monitor.cancel_recovery()

                # Panggil Pekerja Bayangan (Thread) biar sistem utama ga ikutan Freeze
                recovery_thread = threading.Thread(
                    target=background_recovery, 
                    args=(monitor,), 
                    daemon=True
                )
                recovery_thread.start()
                
