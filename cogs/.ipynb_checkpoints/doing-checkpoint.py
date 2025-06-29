import discord
from discord.ext import tasks, commands
import datetime
import random
from discord import Activity, ActivityType
import pytz

class Doing(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.activities = [
            "寶可夢劍/盾", "寶可夢日/月", "訓練員的感情", "寶可夢綠寶石",
            "寶可夢紅寶石", "PTCG", "自己的奶頭", "自己的陰蒂", "寶可夢 朱/紫",
            "寶可夢 鑽石/珍珠", "Pokemon GO", "寶可夢藍寶石"
        ]
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        
    every_hour = [datetime.time(hour = i, minute = 0, second = 0, tzinfo = datetime.timezone(datetime.timedelta(hours = 8))) for i in range(24)]

    @tasks.loop(time = every_hour)
    async def doing_task(self): 
        random_activity = random.choice(self.activities)
        time_now = datetime.datetime.now(self.taiwan_tz)
        await self.bot.change_presence(activity = discord.Activity(type = ActivityType.playing, name = f"{random_activity}"), status = discord.Status.online)
        print(f"機器人正在玩{random_activity}，時間: {time_now.strftime('%H:%M:%S')}\n")

    @doing_task.before_loop
    async def before_doing_task(self):
        await self.bot.wait_until_ready()
        time_now = datetime.datetime.now(self.taiwan_tz)
        random_activity = random.choice(self.activities)
        await self.bot.change_presence(activity = discord.Activity(type = ActivityType.playing, name = f"{random_activity}"), status = discord.Status.online)
        print(f"機器人正在玩{random_activity}，時間: {time_now.strftime('%H:%M:%S')}\n")

    @commands.Cog.listener() 
    async def on_ready(self):
        print("\nDoing Cog 的 on_ready 事件被觸發。\n")
        #if not self.doing_task.is_running():
        #    self.doing_task.start()


async def setup(bot):
    await bot.add_cog(Doing(bot))
    print("Doing Cog 已成功添加到機器人。")