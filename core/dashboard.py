import os
import shutil
import sys

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
    # Pake direct ANSI escape sequence, ga pake os.system("clear") lagi
    # Dijamin anti-tumpuk, anti-glitch, dan ga bakal ke-skip sama proses Root
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def color(text, ansi):
    return f"{ansi}{text}{RESET}"

def print_header_row(left_text, ansi_left="", width=58):
    # Hitung sisa spasi secara akurat tanpa terganggu kode ANSI
    spaces = width - len(left_text)
    if spaces < 0: spaces = 0
    text_colored = f"{ansi_left}{left_text}{RESET}" if ansi_left else left_text
    print(color("║ ", BLUE) + text_colored + (" " * spaces) + color(" ║", BLUE))

# ==========================================
# Dashboard
# ==========================================

def draw_dashboard(monitors, ram_used, ram_total):
    clear()
    
    # Deteksi lebar layar otomatis
    try:
        term_width = shutil.get_terminal_size().columns
        # Kurangi 4 karakter buat alokasi ruang border Kiri-Kanan 
        WIDTH = min(DEFAULT_WIDTH, term_width - 4)
        if WIDTH < 36: 
            WIDTH = 36 # Batas terkecil biar tulisan ga kepotong
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
        # Centering otomatis sesuai total lebar box (WIDTH + 4)
        art_text = line_art.center(WIDTH + 4)
        print(color(art_text, CYAN))
    print()

    # ==========================================
    # Header Tabel
    # ==========================================
    print(color("╔" + "═" * (WIDTH + 2) + "╗", BLUE))
    print_header_row("🚀 CIEL-HUB v4.1 (Tempest)", WHITE, WIDTH)
    print(color("╠" + "═" * (WIDTH + 2) + "╣", BLUE))
    
    print_header_row(f"RAM      : {ram_used:.2f}/{ram_total:.2f} GB ({percent:.0f}%)", "", WIDTH)
    print_header_row(f"Online   : {online} | Offline : {offline} | Recover : {recovering}", "", WIDTH)
    
    print(color("╠" + "═" * (WIDTH + 2) + "╣", BLUE))

    # ==========================================
    # List Akun
    # ==========================================
    for monitor in monitors:
        
        # Ambil nama akun, paskan jadi 10 karakter
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

        # Hitung sisa spasi buat misahin teks kiri dan kanan secara presisi
        # Panjang isi = Nama(10) + Spasi(1) + Status(9) + Timer(variatif)
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
        
