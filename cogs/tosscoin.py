import discord
from discord.ext import commands
import asyncio
import random

intents = discord.Intents.all()
class Tosscoin(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def flip_coin(self, channel: discord.TextChannel, user_id: int, flip: int):
        user_obj = self.bot.get_user(user_id)
        await channel.send(f"{user_obj.mention}擲硬幣{flip}次！") 
        try:
            print(f"用戶 {user_obj.name} 在頻道 {channel.name} 擲硬幣 {flip} 次")
            message = await channel.send(f"{user_obj.mention}擲硬幣中...")
            new_content = message.content + "\n"
            counter = 0

            for i in range(flip):
                await asyncio.sleep(0.8)
                    
                if random.randint(1, 100)%2 == 1:
                    counter += 1
                    new_content += "🔴"
                    await message.edit(content = new_content)
    
                else:
                    new_content += "⚫" 
                    await message.edit(content = new_content)

                if (i+1)%3 == 0:
                    new_content += "\n"
    
            await channel.send(f"{user_obj.mention}共有{counter}次正面，{flip-counter}次反面")
            await asyncio.sleep(2)
            await message.delete()
            print(f"用戶 {user_obj.name} 擲硬幣完成")
            return 
            
        except Exception as e:
            print(f"發生未知錯誤: {e}")
            return


async def setup(bot):
    await bot.add_cog(Tosscoin(bot))