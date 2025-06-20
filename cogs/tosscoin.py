import discord
from discord.ext import commands
from discord import User, app_commands
import asyncio
import random

intents = discord.Intents.all()
class Tosscoin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name = "丟硬幣", description = "丟硬幣遊戲")
    @app_commands.describe(flip = "丟硬幣次數")
    async def flip_coin(self, interaction: discord.Interaction, flip: int):
        _user = interaction.user
        await interaction.response.send_message(f"{_user.mention}擲硬幣{flip}次！")

        try:
            print(f"用戶 {_user.name} 在頻道 {interaction.channel} 擲硬幣 {flip} 次")
            message = await interaction.channel.send(f"{_user.mention}擲硬幣中...")
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

            await interaction.channel.send(f"{_user.mention}共有{counter}次正面，{flip-counter}次反面")
            await asyncio.sleep(2)
            await message.delete()
            print(f"用戶 {_user.name} 擲硬幣完成")
            return

        except Exception as e:
            print(f"發生未知錯誤: {e}")
            return

async def setup(bot):
    await bot.add_cog(Tosscoin(bot))