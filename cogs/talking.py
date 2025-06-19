import discord
from discord.ext import commands

intents = discord.Intents.all()
class Talking(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user: return

        if self.bot.user in message.mentions:
            content = message.content.replace(f"<@{self.bot.user.id}>", "")
            content = content.strip()

            if content == "":
                await message.add_reaction("❓")
                return

            if "Hello" in content:
                await message.channel.send("HI GAY")
                return

            if "奶龍" in content:
                await message.channel.send(file = discord.File("C:/Users/user/Desktop/DC_bot/cogs/nailong.png"))
                return
            
            if "得卡" in content: return

            if "丟硬幣" in content: 
                tosscoin_cog = self.bot.get_cog('Tosscoin')
                if tosscoin_cog:
                    await tosscoin_cog.flip_coin(message.channel, message.author.id, 5)
                    return
                else: return

            else: await message.channel.send("蛤")
            
async def setup(bot):
    await bot.add_cog(Talking(bot))