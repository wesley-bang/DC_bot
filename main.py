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
        print(f"機器人初始狀態設定為：正在玩{initial_activity}，時間: {time_now.strftime('%H:%M:%S')}\n\n")
        
        if not doing_cog.doing_task.is_running():
            doing_cog.doing_task.start()
        else:
            print("doing_task 任務已經在運行中。")
    else:
        print("未找到 Doing Cog，無法設定初始狀態或啟動任務。")

    
    talking_cog = bot.get_cog("Talking")
    if talking_cog:
        print("正在為 Talking Cog 載入聊天記錄並啟動定時備份任務...")
        talking_cog.message_history = chat_backup_manager.load_chat_history()
        print("已載入所有使用者的對話歷史。\n")

        # 啟動定時備份任務
        if not talking_cog.timed_backup_task.is_running():
            talking_cog.timed_backup_task.start()
        else:
            print("聊天記錄定時備份任務已在運行中。")
    else:
        print("未找到 Talking Cog，無法載入歷史記錄或啟動備份任務。")

    


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
# 為了安全，TOKEN 建議放在環境變數或 config.py 中，不要直接寫在這裡
bot.run(BOT_TOKEN)