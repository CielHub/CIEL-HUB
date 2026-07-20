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
        with open("chielhub_error.log", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {err_msg}\n")
    except:
        pass

# ==========================================
# DISCORD UI (Dropdown, Tombol, & Screenshot)
# ==========================================
if DISCORD_AVAILABLE:
    class PanelView(discord.ui.View):
        def __init__(self, manager):
            super().__init__(timeout=None)
            self.manager = manager
            self.selected_account = None
            self.device_name = self.manager.config.get("device_name", "Device-1")

            options = []
            for i, m in enumerate(self.manager.monitors):
                label = m.akun_label if m.akun_label else m.package.split('.')[-1]
                options.append(discord.SelectOption(label=label[:90], value=str(i), emoji="🕹️"))

            self.select = discord.ui.Select(
                placeholder=f"Pilih Akun di {self.device_name}...",
                min_values=1, 
                max_values=1, 
                options=options,
                custom_id=f"select_{self.device_name}",
                row=0
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)

            btn_restart = discord.ui.Button(label="Restart", style=discord.ButtonStyle.primary, emoji="🔄", custom_id=f"btn_res_{self.device_name}", row=1)
            btn_restart.callback = self.restart_callback
            self.add_item(btn_restart)

            btn_kill = discord.ui.Button(label="Kill", style=discord.ButtonStyle.danger, emoji="💀", custom_id=f"btn_kill_{self.device_name}", row=1)
            btn_kill.callback = self.kill_callback
            self.add_item(btn_kill)

            btn_snap = discord.ui.Button(label="Cek Layar", style=discord.ButtonStyle.secondary, emoji="📸", custom_id=f"btn_snap_{self.device_name}", row=1)
            btn_snap.callback = self.snap_callback
            self.add_item(btn_snap)

            btn_restart_all = discord.ui.Button(label="Restart Semua", style=discord.ButtonStyle.success, emoji="🌍", custom_id=f"btn_res_all_{self.device_name}", row=2)
            btn_restart_all.callback = self.restart_all_callback
            self.add_item(btn_restart_all)

            btn_kill_all = discord.ui.Button(label="Nuke Semua", style=discord.ButtonStyle.secondary, emoji="💣", custom_id=f"btn_kill_all_{self.device_name}", row=2)
            btn_kill_all.callback = self.kill_all_callback
            self.add_item(btn_kill_all)

        async def select_callback(self, interaction: discord.Interaction):
            self.selected_account = int(self.select.values[0])
            m = self.manager.monitors[self.selected_account]
            await interaction.response.send_message(f"🎯 [{self.device_name}] Terkunci ke target: **{m.akun_label}**.", ephemeral=True)

        async def snap_callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                # Bikin nama file unik per device biar ga tabrakan
                safe_device_name = self.device_name.replace(" ", "_")
                path = f"/sdcard/chiel_snap_{safe_device_name}.png"
                
                with self.manager.ui_lock:
                    # KASIH JEDA 0.5 DETIK
                    # Biar engine grafis Android selesai render UI secara utuh sebelum difoto
                    time.sleep(0.5) 
                    
                    subprocess.run(["su", "-c", f"screencap -p {path}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(path):
                    file = discord.File(path, filename=f"snap_{safe_device_name}.png")
                    caption = f"📸 **LIVE SCREENSHOT | {self.device_name}**"
                    
                    if self.manager.snap_msg:
                        try:
                            await self.manager.snap_msg.edit(content=caption, attachments=[file])
                            await interaction.followup.send("✅ Foto layar berhasil di-update!", ephemeral=True)
                        except discord.NotFound:
                            self.manager.snap_msg = await interaction.channel.send(content=caption, file=file)
                            await interaction.followup.send("✅ Panel screenshot baru dibuat!", ephemeral=True)
                    else:
                        self.manager.snap_msg = await interaction.channel.send(content=caption, file=file)
                        await interaction.followup.send("✅ Panel screenshot pertama dibuat!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Gagal ambil screenshot (Root bermasalah?).", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Error sistem: {str(e)}", ephemeral=True)

        async def restart_callback(self, interaction: discord.Interaction):
            if self.selected_account is None:
                await interaction.response.send_message("❌ Lu belum milih akun di dropdown!", ephemeral=True)
                return
            m = self.manager.monitors[self.selected_account]
            m.manual_kill = False 
            m.start_recovery(3)
            await interaction.response.send_message(f"🔄 **{m.akun_label}** di {self.device_name} sedang di-restart.", ephemeral=True)

        async def kill_callback(self, interaction: discord.Interaction):
            if self.selected_account is None:
                await interaction.response.send_message("❌ Lu belum milih akun di dropdown!", ephemeral=True)
                return
            m = self.manager.monitors[self.selected_account]
            m.manual_kill = True 
            m.cancel_recovery()
            try: subprocess.run(["su", "-c", f"am force-stop {m.package}"], stdin=subprocess.DEVNULL)
            except: pass
            await interaction.response.send_message(f"💀 **{m.akun_label}** di {self.device_name} dimatikan total.", ephemeral=True)

        async def restart_all_callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True) 
            for m in self.manager.monitors:
                m.manual_kill = False
                m.start_recovery(3)
            await interaction.followup.send(f"🌍 Semua Akun di **{self.device_name}** di-restart!", ephemeral=True)

        async def kill_all_callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            for m in self.manager.monitors:
                m.manual_kill = True
                m.cancel_recovery()
                try: subprocess.run(["su", "-c", f"am force-stop {m.package}"], stdin=subprocess.DEVNULL)
                except: pass
            await interaction.followup.send(f"💣 NUKE! Semua akun di **{self.device_name}** mati.", ephemeral=True)

# ==========================================
# DISCORD BOT CLIENT
# ==========================================
if DISCORD_AVAILABLE:
    class ChielBot(discord.Client):
        def __init__(self, manager):
            intents = discord.Intents.default()
            intents.message_content = True
            super().__init__(intents=intents)
            self.manager = manager
            self.channel_id = int(manager.config.get("discord_channel_id", 0))
            self.device_name = self.manager.config.get("device_name", "Device-1")
            self.panel_msg = None
            self.last_content = ""

        async def setup_hook(self):
            channel = self.get_channel(self.channel_id)
            if channel:
                target_title = f"🚀 CHIEL-HUB PANEL | {self.device_name}"
                # Cari dan selamatkan panel punya device INI SAJA, biarkan device lain hidup
                async for msg in channel.history(limit=50):
                    if msg.author == self.user and msg.embeds:
                        if msg.embeds[0].title == target_title:
                            if not self.panel_msg:
                                self.panel_msg = msg
                            else:
                                try: await msg.delete() # Hapus duplikat dari device yang sama
                                except: pass
            
            self.update_task.start()

        @tasks.loop(seconds=5)
        async def update_task(self):
            if not self.is_ready():
                return
            
            try:
                desc_lines = []
                for m in self.manager.monitors:
                    if getattr(m, 'manual_kill', False):
                        icon, plain_status, timer = "💀", "Disabled (Manual Kill)", "00:00:00"
                    else:
                        if m.status.startswith("[OK]"): icon = "🟢"
                        elif m.status.startswith("[RC]"): icon = "🟡"
                        elif m.status.startswith("[LO]"): icon = "🔵"
                        else: icon = "🔴"
                        
                        timer = f"{m.recovery_remaining:02}s" if m.recovering() else m.uptime()
                        plain_status = m.status.split("] ")[-1]
                    
                    desc_lines.append(f"{icon} **{m.akun_label}** - {plain_status} (`{timer}`)")

                content = "\n\n".join(desc_lines)
                
                if content == self.last_content:
                    return
                
                self.last_content = content
                
                embed = discord.Embed(
                    title=f"🚀 CHIEL-HUB PANEL | {self.device_name}", 
                    description=content, 
                    color=0x2b2d31
                )
                embed.set_footer(text=f"Live Auto Update • {self.device_name}")
                
                channel = self.get_channel(self.channel_id)
                if not channel: return

                view = PanelView(self.manager)

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
        
        self.ui_lock = threading.Lock()
        
        self.bot_token = self.config.get("discord_bot_token", "").strip()
        self.channel_id = self.config.get("discord_channel_id", "").strip()
        
        self.bot_thread = None
        self.snap_msg = None 

        if self.bot_token and self.channel_id:
            if DISCORD_AVAILABLE:
                self.start_discord_bot()
            else:
                log_error("Library discord.py belum terinstall. Bot dibatalkan.")

    def start_discord_bot(self):
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot = ChielBot(self)
            
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
                
                with self.ui_lock:
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
            try: force_stop(package)
            except: pass

    def get_monitors(self):
        return self.monitors
                                                                          
