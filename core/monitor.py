import subprocess
import time

STATUS_LOADING = "[LO] Loading"
STATUS_FARMING = "[OK] Farming"
STATUS_RECOVER = "[RC] Recover"
STATUS_OFFLINE = "[ER] Offline"

class CloneMonitor:

    def __init__(self, package, config):
        self.package = package
        self.config = config 
        
        # Data buat Panel Discord / Dashboard Termux
        self.device_name = config.get("device_name", "Device-1")
        self.akun_label = config.get("akun_labels", {}).get(package, package.replace("com.roblox.", ""))

        self.status = STATUS_LOADING

        self.start_time = time.time()
        self.last_update = time.time()
        self.last_recover = time.time()
        
        # ==========================================
        # Timer Session (Buat Pause/Resume Uptime)
        # ==========================================
        self.session_start = time.time()
        self.total_uptime = 0
        
        # Timer buat nge-limit pembacaan log in-game biar ga CPU heavy
        self.last_log_check = time.time()

        # ==========================================
        # Runtime State
        # ==========================================
        self.is_online = False
        self.is_launching = False
        self.is_joining = False
        self.last_seen = time.time()

        # ==========================================
        # Statistics
        # ==========================================
        self.offline_count = 0
        self.recovery_count = 0
        self.launch_count = 0
        self.join_count = 0

        # ==========================================
        # Recovery State Machine
        # ==========================================
        self.recovery_remaining = 0
        self.is_recovering = False
        self.recovery_started = False
        
    # ==========================================
    # Uptime
    # ==========================================

    def uptime(self):
        sec = self.total_uptime
        if self.is_online:
            sec += (time.time() - self.session_start)
            
        sec = int(sec)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02}:{m:02}:{s:02}"

    # ==========================================
    # Recovery Timer
    # ==========================================

    def recover_elapsed(self):
        return int(time.time() - self.last_recover)

    def reset_recover_timer(self):
        self.last_recover = time.time()

    # ==========================================
    # Recovery State
    # ==========================================

    def start_recovery(self, seconds):
        if self.is_online:
            self.total_uptime += (time.time() - self.session_start) 

        self.status = STATUS_RECOVER
        self.is_recovering = True
        self.recovery_started = False
        self.is_online = False
        self.is_launching = False
        self.is_joining = False
        self.recovery_remaining = seconds
        self.last_update = time.time()

    def tick(self):
        if not self.is_recovering:
            return
        if self.recovery_remaining > 0:
            self.recovery_remaining -= 1

    def recovery_finished(self):
        return (
            self.is_recovering
            and self.recovery_remaining <= 0
            and not self.recovery_started
        )

    def mark_recovery_started(self):
        self.recovery_started = True

    def finish_recovery(self):
        self.is_recovering = False
        self.recovery_started = False
        self.recovery_remaining = 0
        self.recovery_count += 1
        self.reset_recover_timer()
        self.set_farming()

    def cancel_recovery(self):
        self.is_recovering = False
        self.recovery_started = False
        self.recovery_remaining = 0
        self.set_offline()

    # ==========================================
    # Status
    # ==========================================

    def set_loading(self):
        if not self.is_online:
            self.session_start = time.time() 

        self.status = STATUS_LOADING
        self.is_online = True
        self.is_launching = True
        self.is_joining = False
        self.launch_count += 1
        self.last_seen = time.time()
        self.last_update = time.time()

    def set_farming(self):
        if not self.is_online:
            self.session_start = time.time() 

        self.status = STATUS_FARMING
        self.is_online = True
        self.is_launching = False
        self.is_joining = False
        self.last_seen = time.time()
        self.last_update = time.time()

    def set_recover(self):
        if self.is_online:
            self.total_uptime += (time.time() - self.session_start) 

        self.status = STATUS_RECOVER
        self.is_online = False
        self.last_update = time.time()

    def set_offline(self):
        if self.is_online:
            self.total_uptime += (time.time() - self.session_start) 

        self.status = STATUS_OFFLINE
        self.is_online = False
        self.is_launching = False
        self.is_joining = False
        self.offline_count += 1
        self.last_update = time.time()

    # ==========================================
    # Process Detection
    # ==========================================

    def process_alive(self):
        try:
            result = subprocess.run(
                [
                    "su",
                    "-c",
                    f"pidof {self.package}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                stdin=subprocess.DEVNULL,
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    # ==========================================
    # In-Game Error Scanner (Log Reader)
    # ==========================================
    def check_in_game_error(self):
        try:
            # Cari 1 file log Roblox yang paling baru ditulis
            cmd_find = f"su -c 'ls -t /sdcard/Android/data/{self.package}/files/logs/*.log 2>/dev/null | head -n 1'"
            res_find = subprocess.run(cmd_find, shell=True, capture_output=True, text=True)
            log_file = res_find.stdout.strip()
            
            # Kalo ga ketemu di /sdcard, cari di /data/data
            if not log_file:
                cmd_find = f"su -c 'ls -t /data/data/{self.package}/files/logs/*.log 2>/dev/null | head -n 1'"
                res_find = subprocess.run(cmd_find, shell=True, capture_output=True, text=True)
                log_file = res_find.stdout.strip()

            if log_file:
                # Cek 30 baris terakhir dari log itu, scan pakai Regex buat cari pop-up disconnect
                cmd_check = f"su -c 'tail -n 30 {log_file} | grep -iE -m 1 \"error 278|error 277|error 268|connection lost|disconnect\"'"
                res_check = subprocess.run(cmd_check, shell=True, capture_output=True, text=True)
                
                if res_check.stdout.strip():
                    return True # Valid, akun ini kena pop-up putus koneksi!
        except Exception:
            pass
        return False

    # ==========================================
    # Update
    # ==========================================

    def update(self):
        if self.is_recovering:
            return

        alive = self.process_alive()
        now = time.time()

        if alive:
            # Pindai log internal tiap 20 detik untuk menghemat penggunaan CPU Android
            if now - self.last_log_check > 20:
                self.last_log_check = now
                if self.check_in_game_error():
                    # Jika game masih idup tapi kedetect pop-up error, manipulasi status jadi offline
                    if self.status != STATUS_OFFLINE:
                        self.set_offline() 
                    return

            if self.status != STATUS_FARMING:
                self.set_farming()
        else:
            if self.status != STATUS_OFFLINE:
                self.set_offline()

    # ==========================================
    # Helper
    # ==========================================

    def online(self):
        return self.is_online

    def offline(self):
        return not self.is_online

    def recovering(self):
        return self.is_recovering

# ==========================================
# Factory
# ==========================================

def create_monitors(packages, config):
    return [
        CloneMonitor(package, config)
        for package in packages
        ]
    
