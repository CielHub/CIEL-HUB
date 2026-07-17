import os
import shutil

# Lebar maksimal pas layar full
DEFAULT_WIDTH = 58

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
    # Balik pake clear bawaan sistem biar stabil pas split-screen
    os.system("clear")

def color(text, ansi):
    return f"{ansi}{text}{RESET}"

def line(text, current_width):
    print(
        color("║", BLUE)
        + f" {text:<{current_width-2}}"
        + color("║", BLUE)
    )

# ==========================================
# Dashboard
# ==========================================

def draw_dashboard(monitors, ram_used, ram_total):
    clear()
    
    # Bikin lebar dinamis ngikutin ukuran layar Termux (Auto-Responsive)
    try:
        term_width = shutil.get_terminal_size().columns
        WIDTH = min(DEFAULT_WIDTH, term_width)
        # Batas minimal biar tabel ga terlalu dempet pas di-split screen banget
        if WIDTH < 42: 
            WIDTH = 42
    except Exception:
        WIDTH = DEFAULT_WIDTH
        
    percent = 0
    if ram_total:
        percent = (ram_used / ram_total) * 100

    online = sum(m.online() for m in monitors)
    offline = sum(m.offline() for m in monitors)
    recovering = sum(m.recovering() for m in monitors)

    # ==========================================
    # ASCII Banner CIEL
    # ==========================================
    ascii_ciel = [
        " ██████╗██╗███████╗██╗     ",
        "██╔════╝██║██╔════╝██║     ",
        "██║     ██║█████╗  ██║     ",
        "██║     ██║██╔══╝  ██║     ",
        "╚██████╗██║███████╗███████╗",
        " ╚═════╝╚═╝╚══════╝╚══════╝"
    ]
    
    print()
    for line_art in ascii_ciel:
        print(color(line_art.center(WIDTH), CYAN))
    print()

    # ==========================================
    # Header Tabel
    # ==========================================
    print(color("╔" + "═" * WIDTH + "╗", BLUE))
    line(color("🚀 CIEL-HUB v4.1 (Tempest)", WHITE), WIDTH)
    print(color("╠" + "═" * WIDTH + "╣", BLUE))
    
    line(f"RAM      : {ram_used:.2f}/{ram_total:.2f} GB ({percent:.0f}%)", WIDTH)
    line(f"Online   : {online} | Offline : {offline} | Recover : {recovering}", WIDTH)
    
    print(color("╠" + "═" * WIDTH + "╣", BLUE))

    # ==========================================
    # List Akun
    # ==========================================
    for monitor in monitors:
        
        # Ambil nama akun dan pastikan panjangnya persis 10 karakter biar rata
        raw_name = monitor.akun_label if monitor.akun_label else monitor.package.replace("com.roblox.", "")
        name = (raw_name[:10]).ljust(10)

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

        left_str = f" {name}"
        right_str = f"{timer:>9} " 
        
        # Rumus spasi tengah otomatis
        inside_space = WIDTH - 2
        pad_length = inside_space - len(left_str) - len(right_str) - len(vis_status)
        padding = " " * max(1, pad_length) # Minimal kasih 1 spasi

        print(
            color("║", BLUE)
            + left_str
            + status_colored
            + padding
            + right_str
            + color("║", BLUE)
        )

    print(color("╚" + "═" * WIDTH + "╝", BLUE))
    
