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
    
    line(f"RAM      : {ram_used:.2f}/{ram_total:.2f} GB ({percent:.0f}%)")
    line(f"Online   : {online} | Offline : {offline} | Recover : {recovering}")
    
    print(color("╠" + "═" * WIDTH + "╣", BLUE))

    for monitor in monitors:
        name = monitor.package.replace("com.roblox.", "")

        if monitor.recovering():
            timer = f"{monitor.recovery_remaining:02}s"
        else:
            timer = monitor.uptime()

        # Tentukan status visual dan warnanya
        if monitor.status.startswith("[OK]"):
            vis_status = "♦ Farming"
            ansi_color = GREEN
        elif monitor.status.startswith("[RC]"):
            vis_status = "♦ Recover"
            ansi_color = YELLOW
        elif monitor.status.startswith("[LO]"):
            vis_status = "♦ Loading"
            ansi_color = CYAN
        else:
            vis_status = "♦ Offline"
            ansi_color = RED

        status_colored = color(vis_status, ansi_color)

        # Hitung layout dinamis
        left_str = f" {name:<10}"
        right_str = f"{timer:>10} "
        
        space_left = (WIDTH - 2) - len(left_str) - len(right_str)
        pad_length = space_left - len(vis_status)
        padding = " " * max(0, pad_length)

        print(
            color("║", BLUE)
            + left_str
            + status_colored
            + padding
            + right_str
            + color("║", BLUE)
        )

    print(color("╚" + "═" * WIDTH + "╝", BLUE))
    
