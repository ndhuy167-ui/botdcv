import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio

COLOR_PURPLE = 0x9B59B6

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'auto',
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'socket_timeout': 10,
            'source_address': '0.0.0.0'
        }
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_opts)
        
        # Thêm self.last_thumbnails để lưu trữ ảnh bìa của từng server
        self.queues, self.last_titles, self.last_thumbnails = {}, {}, {}
        self.is_fetching = False # Biến khóa chống đứng Bot

    async def play_next(self, guild, voice_client, text_channel):
        if not voice_client.is_connected() or self.is_fetching: 
            return
        
        self.is_fetching = True 
        
        if guild.id in self.queues and len(self.queues[guild.id]) > 0:
            next_query = self.queues[guild.id].pop(0)
        else:
            last = self.last_titles.get(guild.id, "")
            next_query = f"related to {last.split('-')[0]}" if last else "nhạc lofi chill tiktok"

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(next_query, download=False))
            data = data['entries'][0] if 'entries' in data else data
            
            # Lấy tiêu đề và Ảnh bìa (Thumbnail)
            self.last_titles[guild.id] = data.get('title', 'Nhạc tiếp theo')
            self.last_thumbnails[guild.id] = data.get('thumbnail', 'https://i.imgur.com/8Qh1QpP.gif')
            
            if 'url' not in data:
                raise Exception("Không tìm thấy luồng âm thanh trực tiếp!")

            player = discord.FFmpegPCMAudio(data['url'], executable="./ffmpeg.exe", **self.ffmpeg_options)
            
            def after_playing(error):
                asyncio.run_coroutine_threadsafe(self.play_next(guild, voice_client, text_channel), self.bot.loop)
            
            self.is_fetching = False
            voice_client.play(player, after=after_playing)
            
            embed = discord.Embed(title="💿 ĐANG TỰ ĐỘNG CHUYỂN BÀI", description=f"**{self.last_titles[guild.id]}**", color=COLOR_PURPLE)
            # Chèn ảnh bìa nhỏ vào góc phải
            embed.set_thumbnail(url=self.last_thumbnails[guild.id]) 
            await text_channel.send(embed=embed)
            
        except Exception as e:
            self.is_fetching = False
            print(f"Lỗi nối bài: {e}")
            await text_channel.send(embed=discord.Embed(title="⚠️ Lỗi Chuyển Bài", description="YouTube vừa quét hoặc đường truyền không ổn định. Hãy dùng lệnh `/play` để mở bài mới nhé!", color=0xE74C3C))
    
    @app_commands.command(name="join", description="🚶 Gọi Bot vào phòng thoại của bạn")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Sếp phải vào phòng thoại trước thì em mới biết đường vào chứ!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if vc and vc.is_connected():
            if vc.channel.id == channel.id:
                return await interaction.response.send_message("✅ Em đang ở chung phòng với sếp rồi mà!", ephemeral=True)
            else:
                await vc.move_to(channel)
                embed = discord.Embed(title="🚶 ĐÃ CHUYỂN PHÒNG", description=f"Em đã bay sang phòng **{channel.name}** để phục vụ sếp!", color=COLOR_PURPLE)
                return await interaction.response.send_message(embed=embed)
        else:
            await channel.connect()
            embed = discord.Embed(title="🚶 ĐÃ CÓ MẶT", description=f"Em đã vào phòng **{channel.name}**! Sẵn sàng nhận lệnh bật nhạc.", color=COLOR_PURPLE)
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="🎧 Phát bài hát hoặc link YouTube")
    async def play(self, interaction: discord.Interaction, bai_hat: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Vào phòng thoại đi sếp!", ephemeral=True)
        
        await interaction.response.defer()
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if not vc: vc = await interaction.user.voice.channel.connect(reconnect=True)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(bai_hat, download=False))
            data = data['entries'][0] if 'entries' in data else data
            
            # Lấy thông tin Tên bài và Ảnh Thumbnail thật từ YouTube
            title = data.get('title', 'Unknown')
            thumbnail = data.get('thumbnail', 'https://i.imgur.com/8Qh1QpP.gif')
            
            self.last_titles[interaction.guild.id] = title
            self.last_thumbnails[interaction.guild.id] = thumbnail

            if vc.is_playing():
                if interaction.guild.id not in self.queues: self.queues[interaction.guild.id] = []
                self.queues[interaction.guild.id].append(bai_hat)
                
                embed = discord.Embed(title="📝 ĐÃ THÊM VÀO HÀNG ĐỢI", description=f"**{title}**\n*Vị trí: {len(self.queues[interaction.guild.id])}*", color=0x34495E)
                embed.set_thumbnail(url=thumbnail) # Hiện ảnh bài sắp tới
                return await interaction.followup.send(embed=embed)

            if 'url' not in data:
                return await interaction.followup.send("❌ Không thể lấy được âm thanh từ video này!")

            player = discord.FFmpegPCMAudio(data['url'], executable="./ffmpeg.exe", **self.ffmpeg_options)
            
            def after_playing(error):
                asyncio.run_coroutine_threadsafe(self.play_next(interaction.guild, vc, interaction.channel), self.bot.loop)

            vc.play(player, after=after_playing)
            
            # Khung bài hát siêu xịn có Avatar người gọi và Ảnh to đùng
            embed = discord.Embed(title="🎶 ĐANG PHÁT NHẠC", description=f"**{title}**", color=COLOR_PURPLE)
            embed.set_image(url=thumbnail) # ẢNH YOUTUBE TO NẰM CHÍNH GIỮA
            embed.set_author(name=f"Yêu cầu bởi: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Lỗi Play: {e}")
            await interaction.followup.send("❌ Mạng bị YouTube làm khó rồi, hãy cài Node.js (nếu chưa cài) hoặc đổi IP nhé!")

    @app_commands.command(name="skip", description="⏭️ Chuyển nhanh qua bài khác")
    async def skip(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.stop() 
            await interaction.response.send_message(embed=discord.Embed(title="⏭️ ĐÃ BỎ QUA", description="Đang tải bài tiếp theo...", color=COLOR_PURPLE))
        else: await interaction.response.send_message("❌ Đang im ắng mà sếp, có bài nào đâu mà qua!", ephemeral=True)

    @app_commands.command(name="stop", description="⏹️ Tắt nhạc và dọn dẹp phòng")
    async def stop(self, interaction: discord.Interaction):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if vc:
            self.queues[interaction.guild.id] = []
            vc.stop(); await vc.disconnect()
            await interaction.response.send_message(embed=discord.Embed(title="🔌 ĐÃ NGẮT KẾT NỐI", description="Hẹn gặp lại gia đình nha!", color=0xE74C3C))
        else: await interaction.response.send_message("❌ Bot đang ngủ, gọi nhầm người rồi!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))