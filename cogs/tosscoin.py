import discord
from discord.ext import commands
import asyncio
import random

intents = discord.Intents.all()
class TossCoin(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def flip_coin(self, channel: discord.TextChannel, flip: int):
        message = await channel.send(f"擲硬幣{flip}次！\n") 
        try:
            counter = 0

            for i in flip:
                content = message.content
                await asyncio.sleep(0.5)
                    
                if random.radiant(1, 100)%2 == 1:
                    counter += 1
                    await message.edit(content + "🔴")
    
                else: await message.edit(content + "⚫️")

                if (i+1)%3 == 0:
                    await message.edit(content + "\n") 
    
            await channel.send(f"共有{counter}次正面，{flip-counter}次反面")
            return
            
        except Exception as e:
            print(f"發生未知錯誤: {e}")
            return


async def setup(bot):
    await bot.add_cog(Tosscoin(bot))