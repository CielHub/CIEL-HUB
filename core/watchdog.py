from core.monitor import STATUS_OFFLINE
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
            # Auto Recovery berdasarkan Timer
            # =====================================

            if (
                reconnect_minutes > 0
                and not monitor.is_recovering
            ):

                if (
                    monitor.recover_elapsed()
                    >= reconnect_minutes * 60
                ):

                    monitor.start_recovery(delay)

                    continue

            # =====================================
            # Offline Detection
            # =====================================

            if (
                monitor.status == STATUS_OFFLINE
                and not monitor.is_recovering
            ):

                monitor.start_recovery(delay)

                continue

            # =====================================
            # Countdown selesai
            # =====================================

            if monitor.recovery_finished():

                monitor.mark_recovery_started()

                success = recover(
                    monitor.package,
                    self.config,
                    monitor,
                    self.launcher,
                    self.joiner,
                )

                if not success:

                    monitor.cancel_recovery()