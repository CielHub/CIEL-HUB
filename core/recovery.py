import subprocess

def force_stop(package):

    result = subprocess.run(
        [
            "am",
            "force-stop",
            package,
        ],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def recover(
    package,
    config,
    monitor,
    launcher,
    joiner,
):

    # ==========================================
    # Launch Roblox
    # ==========================================

    monitor.set_loading()

    launched = launcher(package)

    if not launched:

        monitor.cancel_recovery()

        return False

    # ==========================================
    # Join Private Server
    # ==========================================

    joined = joiner(
        package,
        config,
    )

    if not joined:

        monitor.cancel_recovery()

        return False

    # ==========================================
    # Recovery Success
    # ==========================================

    monitor.finish_recovery()

    return True
  