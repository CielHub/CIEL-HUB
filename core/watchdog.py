import threading
from core.recovery import recover

# KUNCI ANTREAN: Biar recovery ga jalan bebarengan dan bikin HP nge-hang
recovery_queue_lock = threading.Lock()

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

    def check(self):
        reconnect_minutes = self.config.get("reconnect_minutes", 0)
        delay = self.config.get("force_close_delay", 45)

        for monitor in self.monitors:
            if monitor.recovering():
                pass
            elif (
                reconnect_minutes > 0
                and monitor.recover_elapsed() >= reconnect_minutes * 60
            ):
                monitor.start_recovery(delay)
            elif monitor.offline():
                monitor.start_recovery(delay)
            else:
                continue

            if monitor.recovery_finished():
                monitor.mark_recovery_started()

                def background_recovery(pkg_monitor):
                    # GERBANG TOL: Thread ini harus antre nunggu giliran
                    with recovery_queue_lock:
                        success = recover(
                            pkg_monitor.package,
                            self.config,
                            pkg_monitor,
                            self.launcher,
                            self.joiner,
                        )
                        
                        if not success:
                            pkg_monitor.cancel_recovery()

                recovery_thread = threading.Thread(
                    target=background_recovery, 
                    args=(monitor,), 
                    daemon=True
                )
                recovery_thread.start()
