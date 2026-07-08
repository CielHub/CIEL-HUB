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

    if not launcher(package):

        monitor.cancel_recovery()

        return False

    # ==========================================
    # Join Private Server
    # ==========================================

    if not joiner(package, config):

        monitor.cancel_recovery()

        return False

    # ==========================================
    # Success
    # ==========================================

    monitor.finish_recovery()

    return True