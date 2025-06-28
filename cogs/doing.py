<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 56e6e8c3efde4722659eb16880b31f2a963aca69
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
            "寶可夢劍/盾", "寶可夢日/月", "弄訓練員感情", "寶可夢綠寶石",
            "寶可夢紅寶石", "PTCG", "自己的奶頭", "自己的陰蒂", "寶可夢 朱/紫",
            "寶可夢 鑽石/珍珠", "Pokemon GO", "寶可夢藍寶石"
        ]
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        
    every_hour = [datetime.time(hour = i, minute = 0, second = 0, tzinfo = pytz.timezone('Asia/Taipei')) 
                    for i in range(24)]

    @tasks.loop(time = every_hour)
    async def doing_task(self): 
        random_activity = random.choice(self.activities)
        time_now = datetime.datetime.now(self.taiwan_tz)
        await self.bot.change_presence(activity = discord.Activity(type = ActivityType.playing, name = f"{random_activity}"), status = discord.Status.online)
        print(f"機器人正在玩{random_activity}，時間: {time_now.strftime('%H:%M:%S')}")

    @doing_task.before_loop
    async def before_doing_task(self):
        await self.bot.wait_until_ready()
        time_now = datetime.datetime.now(self.taiwan_tz)
        random_activity = random.choice(self.activities)
        await self.bot.change_presence(activity = discord.Activity(type = ActivityType.playing, name = f"{random_activity}"), status = discord.Status.online)
        print(f"機器人正在玩{random_activity}，時間: {time_now.strftime('%H:%M:%S')}")

    @commands.Cog.listener() 
    async def on_ready(self):
        print("Doing Cog 的 on_ready 事件被觸發。")
        #if not self.doing_task.is_running():
        #    self.doing_task.start()


async def setup(bot):
    await bot.add_cog(Doing(bot))
<<<<<<< HEAD
=======
import discord
from discord.ext import tasks, commands
import datetime
import random

class Doing(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.activities = [
            "照顧寶可夢", "餵食寶可夢", "打掃寶可夢中心", "摸摸寶可夢",
            "與寶可夢玩耍", "治療受傷的寶可夢", "與其他訓練員交流",
            "廁所裡自慰", "偷偷看你的照片", "偷看你在做什麼", "偷聽你在說什麼",
            "偷拍你的照片", "打瞌睡", "被騷擾", "被調戲", "被調教"
        ]
        self.chosen_activity = random.choice(self.activities)
        
    every_hour = [datetime.time(hour = i, minute = 0, second = 0, tzinfo = datetime.timezone(datetime.timedelta(hours = 8))) 
                    for i in range(24)]

    @tasks.loop(time = every_hour)
    async def doing_task(self): 
        random_activity = random.choice(self.activities)
        await self.bot.change_presence(activity = discord.Game(name = f"正在{random_activity}"), status = discord.Status.online)
        print(f"機器人正在{random_activity}，時間: {datetime.datetime.now().strftime('%H:%M:%S')}")


    @doing_task.before_loop
    async def before_doing_task(self):
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity = discord.Game(name = f"正在{self.chosen_activity}"), status = discord.Status.online)
        print(f"機器人正在{self.chosen_activity}，時間: {datetime.datetime.now().strftime('%H:%M:%S')}")


    @commands.Cog.listener() 
    async def on_ready(self):
        print("Doing Cog 的 on_ready 事件被觸發。")
        if not self.doing_task.is_running():
            self.doing_task.start()
            print("doing_task 任務已啟動。")
        else:
            print("doing_task 任務已經在運行中 (不重複啟動)。")

async def setup(bot):
    await bot.add_cog(Doing(bot))
>>>>>>> 517f825841dcac1814d7207a92a1a1032615fc75
=======
>>>>>>> 56e6e8c3efde4722659eb16880b31f2a963aca69
    print("Doing Cog 已成功添加到機器人。")