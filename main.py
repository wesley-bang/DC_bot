import discord
from discord.ext import commands
import os # 用於讀取資料夾中的檔案
from dotenv import load_dotenv
from discord import Activity, ActivityType
import chat_backup_manager


# intents是要求機器人的權限
intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "$", intents = intents)
load_dotenv()
BOT_TOKEN = os.getenv("DC_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 當機器人完成啟動
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    print("----- 載入 Cogs -----")
    # 載入 cogs 資料夾中的所有 .py 檔案
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                # 載入 Cog，例如 'cogs.general'
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"成功載入 {filename}")
            except Exception as e:
                print(f"無法載入 {filename}: {e}")
    slash = await bot.tree.sync()
    print(f"已同步 {len(slash)} 個指令到 Discord")
    print("----- Cogs 載入完成 -----")

    doing_cog = bot.get_cog("Doing")
    if doing_cog: 
        import random
        import datetime
        import pytz

        taiwan_tz = pytz.timezone('Asia/Taipei')
        time_now = datetime.datetime.now(taiwan_tz)
        
        initial_activity = random.choice(doing_cog.activities)
        await bot.change_presence(activity = discord.Activity(type = ActivityType.playing, name = f"{initial_activity}"), status = discord.Status.online)
        print(f"喬伊初始狀態設定為：正在玩{initial_activity}，時間: {time_now.strftime('%H:%M:%S')}\n")
        
        if not doing_cog.doing_task.is_running():
            doing_cog.doing_task.start()
        else:
            print("doing_task 任務已經在運行中。")
    else:
        print("未找到 Doing Cog，無法設定初始狀態或啟動任務。")

    talking_cog = bot.get_cog("Talking")
    if talking_cog:
        print("Talking Cog 已載入，統一備份系統和記憶管理系統已自動啟動。")
        
        # 顯示當前備份統計信息
        try:
            stats = talking_cog.backup_manager.get_backup_stats()
            print(f"當前備份統計：")
            print(f"  - 聊天備份: {stats['chat_backup_count']} 個")
            print(f"  - 記憶備份: {stats['memory_backup_count']} 個")
            print(f"  - 總用戶數: {stats['total_users']} 人")
            print()
        except Exception as e:
            print(f"獲取備份統計失敗: {e}")
    else:
        print("未找到 Talking Cog，記憶管理和備份系統未啟動。")    


# 載入 Cog 的指令 (可選，但建議有，方便開發時測試)
@bot.command()
async def load(ctx, extension):
    try:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'已載入 {extension}。')
    except Exception as e:
        await ctx.send(f'無法載入 {extension}: {e}')

# 卸載 Cog 的指令
@bot.command()
async def unload(ctx, extension):
    try:
        await bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'已卸載 {extension}。')
    except Exception as e:
        await ctx.send(f'無法卸載 {extension}: {e}')

# 重新載入 Cog 的指令
@bot.command()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f'cogs.{extension}')
        await ctx.send(f'已重新載入 {extension}。')
    except Exception as e:
        await ctx.send(f'無法重新載入 {extension}: {e}')


# 運行機器人
bot.run(BOT_TOKEN)