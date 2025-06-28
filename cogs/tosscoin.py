import discord
from discord.ext import commands

intents = discord.Intents.all()
class Challenge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_challenges = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.bot.user.mentioned_in(message) and "得卡" in message.content:
            if message.author.bot: return

            print(f"在頻道 '{message.channel.name}' 收到來自 '{message.author}' 的 '得卡挑戰' 請求。")
            user_id = message.author.id
            
            if user_id in self.active_challenges:
                old_challenge = self.active_challenges[user_id]
                old_user_msg_id = old_challenge['user_msg_id']
                old_bot_msg_obj = old_challenge['old_bot_msg_obj']
                old_task = old_challenge['task']
                old_task.cancel()

                get_cards_cog = self.bot.get_cog('Getcards')
                if get_cards_cog:
                    await get_cards_cog.delete_old_cards(user_id)

                try:
                    old_user_msg = await message.channel.fetch_message(old_user_msg_id)
                    await old_user_msg.delete()
                    print(f"刪除用戶{message.author.name}的訊息: {old_user_msg.id}")

                    await message.channel.send(f"{message.author.mention}給你新的啦貪心鬼")
                    print(f"用戶{message.author.name}的舊挑戰取消，開啟新挑戰\n\n")

                except discord.NotFound:
                    print(f"用戶{message.author.name}的訊息{old_user_msg_id}未找到")

                except Exception as e:
                    print(f"刪除訊息時發生錯誤: {e}")


                try:
                    await old_bot_msg_obj.delete()
                    print(f"刪除用戶{message.author.name}的訊息: {old_bot_msg_obj.id}")

                except discord.NotFound:
                    print(f"用戶{message.author.name}的選擇訊息{old_bot_msg_obj.id}未找到")

                except Exception as e:
                    print(f"刪除選擇訊息時發生錯誤: {e}")


            description = f"{message.author.mention} 選卡包! (等選項跑完在按!) \n"\
                            "🧬---最強的基因      🍄---幻遊島\n"\
                            "🌌---時空激鬥          💫---超克之光\n"\
                            "🪩---嗨放異彩          🌓---雙天之守護者\n"\
                            "🛸---異次元危機"

            pack_choice = await message.channel.send(description)
            pack_choice_cog = self.bot.get_cog('PackChoice')
            if pack_choice_cog:
                task = self.bot.loop.create_task(pack_choice_cog.start_pack_selection(pack_choice, user_id))
                self.active_challenges[user_id] = {'user_msg_id': message.id, 'old_bot_msg_obj': pack_choice,'task': task}

            else:
                await message.channel.send(f"{message.author.mention}發生錯誤，稍後再試")
                print(f"PackChoice cog 未載入")
                return
        
    def remove_active_task(self, user_id):
        user_obj = self.bot.get_user(user_id)
        if user_id in self.active_challenges:
            del self.active_challenges[user_id]
            print(f"用戶{user_obj.name}的挑戰已移除")

async def setup(bot):
    await bot.add_cog(Challenge(bot))      