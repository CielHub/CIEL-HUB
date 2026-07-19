import os
import shutil
import sys

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
    sys.stdout.write('\033c\033[2J\033[3J\033[H')
    sys.stdout.flush()

def color(text, ansi):
    return f"{ansi}{text}{RESET}"

def print_header_row(left_text, ansi_left="", width=58):
    spaces = width - len(left_text)
    if spaces < 0: spaces = 0
    text_colored = f"{ansi_left}{left_text}{RESET}" if ansi_left else left_text
    print(color("║ ", BLUE) + text_colored + (" " * spaces) + color(" ║", BLUE))

# ==========================================
# Dashboard
# ==========================================

def draw_dashboard(monitors, ram_used, ram_total):
    clear()
    
    try:
        term_size = shutil.get_terminal_size()
        WIDTH = min(DEFAULT_WIDTH, term_size.columns - 4)
        HEIGHT = term_size.lines # Deteksi tinggi layar HP
        if WIDTH < 36: 
            WIDTH = 36 
    except Exception:
        WIDTH = DEFAULT_WIDTH
        HEIGHT = 24
        
    percent = 0
    if ram_total:
        percent = (ram_used / ram_total) * 100

    online = sum(m.online() for m in monitors)
    offline = sum(m.offline() for m in monitors)
    recovering = sum(m.recovering() for m in monitors)

    # ==========================================
    # LOGIKA SMART BANNER (AUTO-HIDE)
    # ==========================================
    # Tabel utama makan sekitar 6 baris + jumlah akun lu
    butuh_baris = 6 + len(monitors)
    
    # Kalau tinggi terminal sisa banyak (lebih dari butuh_baris + 8 baris buat logo), tampilin Logo
    if HEIGHT >= (butuh_baris + 8):
        # Pakai awalan 'r' biar backslash (\) ga dibaca sebagai karakter khusus
        ascii_chiel = [
            r"   ________  ______________ ",
            r"  / ____/ / / /  _/ ____/ / ",
            r" / /   / /_/ // // __/ / /  ",
            r"/ /___/ __  // // /___/ /___",
            r"\____/_/ /_/___/_____/_____/"
        ]
        
        print()
        for line_art in ascii_chiel:
            art_text = line_art.center(WIDTH + 4)
            print(color(art_text, CYAN))
        print()
    else:
        # Kalau HP miring dan ga muat, logo ilang otomatis biar ga nabrak/nge-glitch
        print()

    # ==========================================
    # Header Tabel (Header Nama Dihilangkan)
    # ==========================================
    print(color("╔" + "═" * (WIDTH + 2) + "╗", BLUE))
    
    print_header_row(f"RAM      : {ram_used:.2f}/{ram_total:.2f} GB ({percent:.0f}%)", "", WIDTH)
    print_header_row(f"Online   : {online} | Offline : {offline} | Recover : {recovering}", "", WIDTH)
    
    print(color("╠" + "═" * (WIDTH + 2) + "╣", BLUE))

    # ==========================================
    # List Akun
    # ==========================================
    for monitor in monitors:
        
        raw_name = monitor.akun_label if monitor.akun_label else monitor.package.replace("com.roblox.", "")
        name = (raw_name[:10]).ljust(10)

        if monitor.recovering():
            timer = f"{monitor.recovery_remaining:02}s"
        else:
            timer = monitor.uptime()

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

        content_len = len(name) + 1 + len(vis_status) + len(timer)
        spaces = WIDTH - content_len
        if spaces < 1: spaces = 1
        
        padding = " " * spaces

        line_str = (
            color("║ ", BLUE) + 
            name + " " + 
            color(vis_status, ansi_color) + 
            padding + 
            timer + 
            color(" ║", BLUE)
        )
        print(line_str)

    print(color("╚" + "═" * (WIDTH + 2) + "╝", BLUE))
