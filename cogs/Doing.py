import discord
from discord.ext import tasks, commands
import datetime
import random

intents  = discord.Intents.all()
class Doing(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.activities = [
            "照顧寶可夢", "餵食寶可夢", "打掃寶可夢中心", "摸摸寶可夢",
            "與寶可夢玩耍", "治療受傷的寶可夢", "與其他訓練員交流",
            "廁所裡自慰", "偷偷看你的照片", "偷看你在做什麼", "偷聽你在說什麼"
        ]
               
    every_two_hour = [datetime.time(hour = i, minute = 0, second = 0, tzinfo = datetime.timezone(datetime.timedelta(hours = 8))) 
                    for i in range(24) if i % 2 == 0]

    @tasks.loop(time = every_two_hour)
    async def doing_task(self):
        await self.bot.change_presence(name = f"正在{random.choice(self.activities)}", status = discord.Status.online)
