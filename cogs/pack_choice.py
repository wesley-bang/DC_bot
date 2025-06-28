import re
import discord
from discord.ext import commands
import asyncio


class PackChoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.option = { 
            "🧬": "GeneticApex",
            "🍄": "MythicalIsland",
            "🌌": "SpacetimeSmack", 
            "💫": "TriumphantLight", 
            "🪩": "ShinyRevelry",
            "🌓": "CelestialGuardians",
            "🛸": "ExtradimensionalCrisis"
        }
        self.waiting_selection = {}
    
    async def start_pack_selection(self, message: discord.Message, user_id: int):
        
        self.waiting_selection[message.id] = user_id

        tasks = []
        for emoji in self.option.keys():
            tasks.append(message.add_reaction(emoji))
        
        try:
            await asyncio.gather(*tasks, return_exceptions = True)
            
        except Exception as e:
            print(f"添加表情時發生錯誤: {e}")


        def check(reaction, user):
            return (user.id == user_id and reaction.message.id == message.id and str(reaction.emoji) in self.option)
        
        user_obj = self.bot.get_user(user_id)
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check = check, timeout = 20.0)
            chosen_pack = self.option[str(reaction.emoji)]
            
            get_cards_cog = self.bot.get_cog('Getcards')
            if get_cards_cog:
                await get_cards_cog.send_cards(message.channel, user_id, chosen_pack, reaction.emoji)

            else: 
                await message.channel.send(f"{user_obj.mention} 發生錯誤，稍後再試")
                print(f"GetCards cog 未載入")
                return
            
        except asyncio.TimeoutError:
            try:
                await message.delete()
                await message.channel.send(f"{user_obj.mention}愛玩不玩，滾")
                print(f"用戶{user_obj.name}的請求超時")
            
            except discord.NotFound:
                print(f"找不到超時訊息{message.id}")

            except Exception as e:
                print(f"處理超時發生未知錯誤: {e}")           

        except asyncio.CancelledError:
            print(f"用戶{user_obj.name}的挑戰取消")
            try:
                await message.delete() 
            
            except discord.NotFound:
                print(f"找不到取消訊息{message.id}")

            except Exception as e:
                print(f"處理取消時發生未知錯誤: {e}")

        except Exception as e:
            print(f"等待用戶{user_obj.name}時發生未知錯誤: {e}")
            await message.channel.send(f"{user_id}的得卡挑戰發生錯誤")


        challenge_cog = self.bot.get_cog('Challenge')
        if challenge_cog:
            challenge_cog.remove_active_task(user_id)
            
async def setup(bot):
    await bot.add_cog(PackChoice(bot)) 