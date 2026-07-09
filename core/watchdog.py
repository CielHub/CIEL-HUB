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