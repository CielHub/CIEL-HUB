import subprocess
import time
import json
import urllib.request

STATUS_LOADING = "[LO] Loading"
STATUS_FARMING = "[OK] Farming"
STATUS_RECOVER = "[RC] Recover"
STATUS_OFFLINE = "[ER] Offline"

class CloneMonitor:

    def __init__(self, package, config):

        self.package = package
        self.config = config # Simpen config buat Webhook
        self.webhook_url = config.get("discord_webhook", "").strip()

        self.status = STATUS_LOADING

        self.start_time = time.time()
        self.last_update = time.time()
        self.last_recover = time.time()

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
    # Discord Webhook Logic
    # ==========================================
    def send_discord_alert(self, title, description, color):
        if not self.webhook_url:
            return
            
        data = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "footer": {"text": "Ciel-Hub Auto Recovery"}
            }]
        }
        
        req = urllib.request.Request(
            self.webhook_url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        try:
            # Ngirim data tapi dikasih bates waktu biar Termux lu ga ngelag
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass # Cuekin aja kalo gagal kirim biar script tetep jalan

    # ==========================================
    # Uptime
    # ==========================================

    def uptime(self):
        sec = int(time.time() - self.start_time)
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
        self.status = STATUS_LOADING
        self.is_online = True
        self.is_launching = True
        self.is_joining = False
        self.launch_count += 1
        self.last_seen = time.time()
        self.last_update = time.time()
        
        # Kirim Alert Kuning (16776960)
        self.send_discord_alert(
            f"🔄 {self.package} - Memulai Loading",
            "Menyiapkan clone untuk masuk ke in-game.",
            16776960
        )

    def set_farming(self):
        self.status = STATUS_FARMING
        self.is_online = True
        self.is_launching = False
        self.is_joining = False
        self.last_seen = time.time()
        self.last_update = time.time()
        
        # Kirim Alert Hijau (65280)
        self.send_discord_alert(
            f"🟢 {self.package} - Farming Berjalan",
            "Clone berhasil online dan sedang farming.",
            65280
        )

    def set_recover(self):
        self.status = STATUS_RECOVER
        self.is_online = False
        self.last_update = time.time()

    def set_offline(self):
        self.status = STATUS_OFFLINE
        self.is_online = False
        self.is_launching = False
        self.is_joining = False
        self.offline_count += 1
        self.last_update = time.time()
        
        # Kirim Alert Merah (16711680)
        self.send_discord_alert(
            f"🔴 {self.package} - Clone Terputus / Force Close",
            "Game tidak terdeteksi oleh sistem. Menunggu proses recovery...",
            16711680
        )

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
    # Update
    # ==========================================

    def update(self):
        if self.is_recovering:
            return

        alive = self.process_alive()

        if alive:
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
    
