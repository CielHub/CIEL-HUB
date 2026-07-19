import time
import sys
import select
import json
import os
import threading
import asyncio
import subprocess

try:
    import discord
    from discord.ext import tasks
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

from core.monitor import create_monitors
from core.memory import get_ram
from core.dashboard import draw_dashboard
from core.watchdog import Watchdog
from core.recovery import force_stop

# ==========================================
# Error Logger
# ==========================================
def log_error(err_msg):
    try:
        with open("cielhub_error.log", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {err_msg}\n")
    except:
        pass

# ==========================================
# DISCORD UI (Dropdown & Tombol)
# ==========================================
if DISCORD_AVAILABLE:
    class PanelView(discord.ui.View):
        def __init__(self, manager):
            # timeout=None biar tombolnya ga basi/expired
            super().__init__(timeout=None)
            self.manager = manager
            self.selected_account = None

            # 1. Bikin Dropdown (Select Menu)
            options = []
            for i, m in enumerate(self.manager.monitors):
                label = m.akun_label if m.akun_label else m.package.split('.')[-1]
                options.append(discord.SelectOption(label=label[:90], value=str(i), emoji="🕹️"))

            self.select = discord.ui.Select(
                placeholder="Pilih Akun yang mau dieksekusi...",
                min_values=1, 
                max_values=1, 
                options=options,
                custom_id="select_account"
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)

            # 2. Bikin Tombol Restart
            btn_restart = discord.ui.Button(label="Restart Akun", style=discord.ButtonStyle.primary, emoji="🔄", custom_id="btn_restart")
            btn_restart.callback = self.restart_callback
            self.add_item(btn_restart)

            # 3. Bikin Tombol Kill
            btn_kill = discord.ui.Button(label="Kill (Matikan Total)", style=discord.ButtonStyle.danger, emoji="💀", custom_id="btn_kill")
            btn_kill.callback = self.kill_callback
            self.add_item(btn_kill)

        async def select_callback(self, interaction: discord.Interaction):
            self.selected_account = int(self.select.values[0])
            m = self.manager.monitors[self.selected_account]
            # ephemeral=True biar pesannya cuma bisa diliat sama lu doang
            await interaction.response.send_message(f"🎯 Terkunci ke target: **{m.akun_label}**. Silakan klik tombol Restart atau Kill di bawah.", ephemeral=True)

        async def restart_callback(self, interaction: discord.Interaction):
            if self.selected_account is None:
                await interaction.response.send_message("❌ Lu belum milih akun di dropdown atas!", ephemeral=True)
                return
            
            m = self.manager.monitors[self.selected_account]
            m.manual_kill = False # Cabut status manual kill (jika ada)
            m.start_recovery(3)
            await interaction.response.send_message(f"🔄 **{m.akun_label}** sedang di-restart paksa. Watchdog akan mengambil alih.", ephemeral=True)

        async def kill_callback(self, interaction: discord.Interaction):
            if self.selected_account is None:
                await interaction.response.send_message("❌ Lu belum milih akun di dropdown atas!", ephemeral=True)
                return
            
            m = self.manager.monitors[self.selected_account]
            m.manual_kill = True # Tandai akun ini biar diabaikan sama Watchdog
            m.cancel_recovery()
            
            # Eksekusi Root Force Close di Termux
            try:
                subprocess.run(["su", "-c", f"am force-stop {m.package}"], stdin=subprocess.DEVNULL)
            except: pass
            
            await interaction.response.send_message(f"💀 **{m.akun_label}** telah dimatikan total. Sistem Auto-Recovery tidak akan menyentuh akun ini sampai lu klik Restart lagi.", ephemeral=True)

# ==========================================
# DISCORD BOT CLIENT
# ==========================================
if DISCORD_AVAILABLE:
    class CielBot(discord.Client):
        def __init__(self, manager):
            intents = discord.Intents.default()
            intents.message_content = True
            super().__init__(intents=intents)
            self.manager = manager
            self.channel_id = int(manager.config.get("discord_channel_id", 0))
            self.panel_msg = None
            self.last_content = ""

        async def setup_hook(self):
            # Bersihkan pesan lama bot saat baru nyala
            channel = self.get_channel(self.channel_id)
            if channel:
                async for msg in channel.history(limit=15):
                    if msg.author == self.user:
                        try: await msg.delete()
                        except: pass
            
            self.update_task.start()

        @tasks.loop(seconds=5)
        async def update_task(self):
            if not self.is_ready():
                return
            
            try:
                desc_lines = []
                for m in self.manager.monitors:
                    # Logika tampilan kalau akun di-kill manual
                    if getattr(m, 'manual_kill', False):
                        icon = "💀"
                        plain_status = "Disabled (Manual Kill)"
                        timer = "00:00:00"
                    else:
                        if m.status.startswith("[OK]"): icon = "🟢"
                        elif m.status.startswith("[RC]"): icon = "🟡"
                        elif m.status.startswith("[LO]"): icon = "🔵"
                        else: icon = "🔴"
                        
                        if m.recovering(): timer = f"{m.recovery_remaining:02}s"
                        else: timer = m.uptime()
                        plain_status = m.status.split("] ")[-1]
                    
                    desc_lines.append(f"{icon} **{m.akun_label}** - {plain_status} (`{timer}`)")

                content = "\n\n".join(desc_lines)
                
                # Smart Update: Cuma kirim/edit pesan ke Discord kalau ada status yang berubah
                if content == self.last_content:
                    return
                
                self.last_content = content
                device_name = self.manager.config.get("device_name", "Device-1")
                
                embed = discord.Embed(
                    title=f"🚀 CIEL-HUB PANEL | {device_name}", 
                    description=content, 
                    color=0x2b2d31
                )
                embed.set_footer(text="Live Auto Update • Remote Control Aktif")
                
                channel = self.get_channel(self.channel_id)
                if not channel:
                    return

                view = PanelView(self.manager)

                # Kirim atau Edit panel UI
                if not self.panel_msg:
                    self.panel_msg = await channel.send(embed=embed, view=view)
                else:
                    try:
                        await self.panel_msg.edit(embed=embed, view=view)
                    except discord.NotFound:
                        self.panel_msg = await channel.send(embed=embed, view=view)
            except Exception as e:
                log_error(f"Discord Bot Error: {e}")

# ==========================================
# MANAGER ENGINE
# ==========================================
class Manager:
    def __init__(
        self,
        packages,
        config,
        launcher,
        joiner,
        cache_cleaner, 
    ):
        self.packages = packages
        self.config = config

        self.monitors = create_monitors(packages, config) 
        self.watchdog = Watchdog(self.monitors, config, launcher, joiner)
        self.cache_cleaner = cache_cleaner
        self.last_cache_clear = time.time()
        self.running = False
        
        self.bot_token = self.config.get("discord_bot_token", "").strip()
        self.channel_id = self.config.get("discord_channel_id", "").strip()
        self.bot_thread = None

        # Jalankan pekerja bayangan Discord Bot jika Token tersedia
        if self.bot_token and self.channel_id:
            if DISCORD_AVAILABLE:
                self.start_discord_bot()
            else:
                log_error("Library discord.py belum terinstall. Bot dibatalkan.")

    def start_discord_bot(self):
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot = CielBot(self)
            
            import logging
            logging.getLogger('discord').setLevel(logging.CRITICAL)
            
            bot.run(self.bot_token, log_handler=None)

        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()

    def update_monitors(self):
        for monitor in self.monitors:
            monitor.tick()
            monitor.update()

    def update_watchdog(self):
        # HACK CERDAS: 
        # Sembunyikan sementara akun yang sedang di-kill manual dari penglihatan Watchdog
        # Biar Watchdog ga nyoba-nyoba nge-recover akun tersebut.
        active_monitors = [m for m in self.monitors if not getattr(m, 'manual_kill', False)]
        original_monitors = self.watchdog.monitors
        
        self.watchdog.monitors = active_monitors
        self.watchdog.check()
        self.watchdog.monitors = original_monitors

    def update_cache_cleaner(self):
        interval_minutes = self.config.get("auto_clear_cache_minutes", 0)
        
        if interval_minutes > 0:
            if time.time() - self.last_cache_clear >= (interval_minutes * 60):
                for pkg in self.packages:
                    try:
                        self.cache_cleaner(pkg, silent=True) 
                    except Exception as e:
                        log_error(f"Gagal membersihkan cache {pkg}: {e}")
                self.last_cache_clear = time.time()

    def update_dashboard(self):
        ram_used, ram_total = get_ram()
        draw_dashboard(self.monitors, ram_used, ram_total)

    def start(self):
        self.running = True
        try:
            while self.running:
                self.update_monitors()
                self.update_watchdog()
                self.update_cache_cleaner()
                self.update_dashboard()
                
                i, o, e = select.select([sys.stdin], [], [], 1)
                if i:
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == 'r':
                        for monitor in self.monitors:
                            monitor.cancel_recovery() 
                            monitor.set_offline()     

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        for package in self.packages:
            try:
                force_stop(package)
            except Exception as e:
                log_error(f"Gagal force-stop aplikasi {package}: {e}")

    def get_monitors(self):
        return self.monitors
        
