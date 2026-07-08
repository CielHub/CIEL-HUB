import os

WIDTH = 47

# ==========================================
# ANSI COLOR
# ==========================================

RESET = "\033[0m"

BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
WHITE = "\033[97m"

# ==========================================
# TERMINAL
# ==========================================

def clear():
    os.system("clear")


def blue(text):
    return f"{BLUE}{text}{RESET}"


def green(text):
    return f"{GREEN}{text}{RESET}"


def yellow(text):
    return f"{YELLOW}{text}{RESET}"


def cyan(text):
    return f"{CYAN}{text}{RESET}"


def red(text):
    return f"{RED}{text}{RESET}"


def color_status(status):

    if "[OK]" in status:
        return green(status)

    if "[RC]" in status:
        return yellow(status)

    if "[LO]" in status:
        return cyan(status)

    if "[ER]" in status:
        return red(status)

    return status


def line(left="", right=""):

    print(
        blue("║")
        + f" {left:<{WIDTH-3}}"
        + blue("║")
    )


# ==========================================
# DASHBOARD
# ==========================================

def draw_dashboard(monitors, ram_used, ram_total):

    clear()

    percent = (
        (ram_used / ram_total) * 100
        if ram_total
        else 0
    )

    print(blue("╔══════════════════════════════════════════════╗"))

    line(blue("🚀 CIEL-HUB v4.0"))

    print(blue("╠══════════════════════════════════════════════╣"))

    line(
        f"RAM   : {ram_used:.2f} / {ram_total:.2f} GB ({percent:.0f}%)"
    )

    line(
        f"Clone : {len(monitors)} / {len(monitors)}"
    )

    print(blue("╠══════════════════════════════════════════════╣"))

    for monitor in monitors:

        name = monitor.package.replace(
            "com.roblox.",
            "",
        )

        # ==========================
        # TIMER
        # ==========================

        if "[RC]" in monitor.status:

            timer = (
                f"00:00:{monitor.recovery_remaining:02}"
            )

        else:

            timer = monitor.uptime()

        status = color_status(monitor.status)

        # nama
        print(
            blue("║")
            + f" {name:<8}"
            + f"{status:<22}"
            + f"{timer:>10} "
            + blue("║")
        )

    print(blue("╚══════════════════════════════════════════════╝"))