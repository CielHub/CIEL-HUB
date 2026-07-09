import os

WIDTH = 58

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
# Terminal
# ==========================================

def clear():
    os.system("clear")


def color(text, ansi):
    return f"{ansi}{text}{RESET}"


def status_text(monitor):

    if monitor.status.startswith("[OK]"):
        return color("🟢 Farming", GREEN)

    if monitor.status.startswith("[RC]"):
        return color("🟡 Recover", YELLOW)

    if monitor.status.startswith("[LO]"):
        return color("🔵 Loading", CYAN)

    if monitor.status.startswith("[ER]"):
        return color("🔴 Offline", RED)

    return monitor.status


def line(text=""):

    print(
        color("║", BLUE)
        + f" {text:<{WIDTH-2}}"
        + color("║", BLUE)
    )


# ==========================================
# Dashboard
# ==========================================

def draw_dashboard(monitors, ram_used, ram_total):

    clear()

    percent = 0

    if ram_total:
        percent = (ram_used / ram_total) * 100

    online = sum(m.online() for m in monitors)
    offline = sum(m.offline() for m in monitors)
    recovering = sum(m.recovering() for m in monitors)

    print(color("╔" + "═" * WIDTH + "╗", BLUE))

    line(color("🚀 CIEL-HUB v4.1", WHITE))

    print(color("╠" + "═" * WIDTH + "╣", BLUE))

    line(
        f"RAM      : {ram_used:.2f}/{ram_total:.2f} GB ({percent:.0f}%)"
    )

    line(
        f"Online   : {online} | Offline : {offline} | Recover : {recovering}"
    )

    print(color("╠" + "═" * WIDTH + "╣", BLUE))

    for monitor in monitors:

        name = monitor.package.replace(
            "com.roblox.",
            "",
        )

        if monitor.recovering():

            timer = f"{monitor.recovery_remaining:02}s"

        else:

            timer = monitor.uptime()

        status = status_text(monitor)

        plain_status = (
            "🟢 Farming"
            if monitor.status.startswith("[OK]")
            else "🟡 Recover"
            if monitor.status.startswith("[RC]")
            else "🔵 Loading"
            if monitor.status.startswith("[LO]")
            else "🔴 Offline"
        )

        padding = " " * max(1, 13 - len(plain_status))

        print(
            color("║", BLUE)
            + f" {name:<10}"
            + status
            + padding
            + f"{timer:>10} "
            + color("║", BLUE)
        )

    print(color("╚" + "═" * WIDTH + "╝", BLUE))