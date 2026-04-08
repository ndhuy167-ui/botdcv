from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()
import discord
from discord.ext import commands, tasks
import os
import random

# ================= CẤU HÌNH CHÍNH =================
TOKEN = os.getenv("MTQ5MDMzNDE2ODcyOTY1MzI0OA.Gkt74h.vxabAn6EjxfrhGWpHNQEIZquNe2HaHEB_232Aw")
STATUS_TEXT = "💚 Chỉ yêu mình Hyyy"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Tự động load các file tính năng trong thư mục cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        await self.tree.sync()
        if not self.change_status_task.is_running():
            self.change_status_task.start()

    # ================= STATUS XOAY VÒNG VIP =================
    @tasks.loop(seconds=20)
    async def change_status_task(self):
        if not self.is_ready(): return
        
        total_members = sum(guild.member_count for guild in self.guilds)
        statuses = [
            discord.Activity(type=discord.ActivityType.playing, name=f"{STATUS_TEXT} 💍"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{total_members} thành viên 💎"),
            discord.Activity(type=discord.ActivityType.listening, name="/help để xem lệnh 📚")
        ]
        try: await self.change_presence(activity=random.choice(statuses))
        except: pass

bot = MyBot()

# ================= LỆNH LÀM MỚI CODE (KHÔNG TẮT BOT) =================
@bot.tree.command(name="reload", description="🔄 Làm mới lại toàn bộ code (Chỉ dành cho Sếp John Dawson)")
async def reload(interaction: discord.Interaction):
    # Dùng defer để Bot có thời gian xử lý tải file
    await interaction.response.defer(ephemeral=True)
    
    try:
        count = 0
        # Quét và tải lại toàn bộ các file trong thư mục cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.reload_extension(f'cogs.{filename[:-3]}')
                count += 1
                
        # Đồng bộ lại các lệnh / (Slash commands) lên Discord
        await bot.tree.sync()
        
        await interaction.followup.send(f"✅ Đã tải lại thành công {count} file (Nhạc, Tình Yêu, Tiền Bạc...)! Code mới đã được áp dụng ngay lập tức. 🚀")
    except Exception as e:
        await interaction.followup.send(f"❌ Có lỗi trong code ông vừa sửa rồi: `{e}`\nÔng check lại file vừa sửa nhé!")

@bot.event
async def on_ready():
    print(f'🚀 [SYSTEM] Bot {bot.user} đã khởi động thành công bản VIP PRO MAX!')
    print(f'💎 [MODULES] Đã tải toàn bộ hệ thống Nhạc, Kinh tế, Tình Yêu và Tiện ích.')

if __name__ == "__main__":
    bot.run(TOKEN)
