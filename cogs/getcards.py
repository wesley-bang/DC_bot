import discord
import os
import random
from discord.ext import commands

ALLOWED_EXTENSIONS = ".webp"

class Getcards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.card_path = "cogs/cards"
        self.active_drawn = {}
        self.option = { 
            "🧬": "最強的基因",
            "🍄": "幻遊島",
            "🌌": "時空激鬥", 
            "💫": "超克之光", 
            "🪩": "嗨放異彩",
            "🌓": "雙天之守護者",
            "🛸": "異次元危機"
        }

    async def send_cards(self, channel: discord.TextChannel, user_id: int, pack_name: str, emoji: str):        
        user = self.bot.get_user(user_id)
        pack_path = os.path.join(self.card_path, pack_name)

        if not os.path.join(pack_path):
            await channel.send(f"錯誤：圖片資料夾 '{pack_path}' 不存在。請聯繫 Bot 管理員。")
            
            challenge_cog = self.bot.get_cog('Challenge')
            if challenge_cog:
                challenge_cog.remove_active_task(user_id)
            return

        image_files = [f for f in os.listdir(pack_path) if f.lower().endswith(ALLOWED_EXTENSIONS)]

        if not image_files:
            await channel.send(f"{user.mention}該卡包無可用卡片")
            
            challenge_cog = self.bot.get_cog('Challenge')
            if challenge_cog:
                challenge_cog.remove_active_task(user_id)
            return

        total_cards = min(5, len(image_files))
        selected_card = random.sample(image_files, total_cards)
        selected_card_path = [os.path.join(pack_path, f) for f in selected_card]
        self.active_drawn[user_id] = {'selected_card_path': selected_card_path}

        discord_files = []
        for path in selected_card_path:
            try:
                discord_files.append(discord.File(path))

            except Exception as e:
                print(f"無法載入檔案 {path}: {e}")
                continue

        if not discord_files:
            await channel.send("未能準備任何圖片檔案進行發送。")
            
            challenge_cog = self.bot.get_cog('Challenge')
            if challenge_cog:
                challenge_cog.remove_active_task(user_id)
            return

        try:
            sent_message = await channel.send(f"{user.mention}\n你選擇了**{self.option[emoji]}**\n1到5選一個!", files = discord_files)
            print(f"已向 {channel.name} 發送 {len(discord_files)} 張圖片。")
            self.active_drawn[user_id]['old_cards']= sent_message.id
            self.active_drawn[user_id]['channel_id']= channel.id

        except discord.errors.HTTPException as e:
            if e.code == 40005: await channel.send(f"發送圖片失敗：檔案數量過多或總大小超出 Discord 限制。錯誤訊息: {e}")
            
            else: await channel.send(f"發送圖片時發生 HTTP 錯誤：{e}")           

        except Exception as e:
            await channel.send(f"發送圖片時發生未知錯誤：{e}")


        def check(m):
            return (m.author.id == user_id and m.channel.id == channel.id and m.content.isdigit())

        invalid_trial = 0
        choice_num = -1
        print(f"用戶{user.name}開始抽卡")
        try:
            while True:
                if invalid_trial >= 3:
                    await channel.send(f"{user.mention}滾，不讓你選了")
                    break

                choice_msg = await self.bot.wait_for('message', check = check, timeout = 20.0)
                print(choice_msg.content)

                if choice_msg.content.isdigit():

                    if int(choice_msg.content) < 1 or int(choice_msg.content) > 5:
                        await channel.send(f"{user.mention}煞筆重選")
                        invalid_trial += 1

                    elif 1 <= int(choice_msg.content) <= 5:
                        choice_num = int(choice_msg.content)
                        print(f"{user.name} 選擇:{choice_num}")
                        break

                else: invalid_trial += 1     

            if choice_num != -1:
                derived_idx = (choice_num + random.randint(100, 800))%5
                drawn_image = self.active_drawn[user_id]['selected_card_path'][derived_idx]
                print(f"抽出卡牌索引為:{derived_idx+1}")
                await channel.send(f"{user.mention}抽得不錯，下次抽你", file = discord.File(drawn_image))
                print(f"已向用戶{user.name}發送第{derived_idx+1}張卡牌")


        except Exception as e:
            await channel.send(f"{user.mention}抽卡時發生錯誤")
            print(f"用戶{user.name}抽卡時發生錯誤: {e}")

        finally:
            if user_id in self.active_drawn:
                del self.active_drawn[user_id]
            
            challenge_cog = self.bot.get_cog('Challenge')
            if challenge_cog:
                challenge_cog.remove_active_task(user_id)
            return

    async def delete_old_cards(self, user_id: int):
        user_obj = self.bot.get_user(user_id)
        if user_id in self.active_drawn and 'old_cards' in self.active_drawn[user_id]:
            message_id = self.active_drawn[user_id]['old_cards']
            channel_id = self.active_drawn[user_id]['channel_id']

            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    message_delete = await channel.fetch_message(message_id)
                    await message_delete.delete()
                    print(f"已刪除使用者{user_obj.name}的舊卡片訊息: {message_id}")

                else:
                    print(f"頻道 {channel_id} 未找到，無法刪除訊息 {message_id}")

            except discord.NotFound:
                print(f"訊息 {message_id} 未找到，可能已被刪除")

            except Exception as e:
                print(f"刪除訊息 {message_id} 時發生錯誤: {e}")

            finally:
                if user_id in self.active_drawn:
                    del self.active_drawn[user_id]

async def setup(bot):
    await bot.add_cog(Getcards(bot))