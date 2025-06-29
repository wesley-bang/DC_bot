import discord
from discord.ext import tasks, commands
from discord import app_commands
import os
import google.generativeai as genai
from bs4 import BeautifulSoup
from google.generativeai.types import BlockedPromptException
import datetime
import pytz
import json

import chat_backup_manager

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash')

GENERATION_CONFIG = json.loads(os.getenv("GENERATION_CONFIG_JSON", '{}'))
SAFETY = json.loads(os.getenv("SAFETY_JSON", '[]'))
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", "100"))

intents = discord.Intents.all()
class Talking(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_history = {}
        #self.special_bot_id = 1382939229969190943
        #self.special_bot_name = "嘎嘎嘎"
        self.role_prompt = os.getenv("ROLE_PROMPT_BASE")

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nTalking Cog 已成功載入。\n")


    @tasks.loop(minutes = [0, 15, 30, 45])
    async def timed_backup_task(self):
        taiwan_tz = pytz.timezone('Asia/Taipei')
        print(f"正在備份聊天記錄...，時間(UTF+8): {datetime.datetime.now(taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        
        chat_backup_manager.save_chat_history(self.message_history)
        print(f"定時聊天記錄已成功備份。時間(UTF+8): {datetime.datetime.now(taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')}\n")

    @timed_backup_task.error
    async def timed_backup_task_error(self, error):
        print(f"定時備份任務發生錯誤: {error}")

    def cog_unload(self):
        self.timed_backup_task.cancel()
        print("\nTalking Cog 已卸載，定時備份任務已取消。")
        print("正在執行最後一次備份...")
        chat_backup_manager.save_chat_history(self.message_history)
        print("最後一次備份已完成。\n")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.mention_everyone: return

        if self.bot.user in message.mentions:
            content = message.content.replace(f"<@{self.bot.user.id}>", "")
            content = content.strip()

            if content == "":
                await message.add_reaction("❓")
                return

            if "奶龍" in content:
                await message.channel.send(file = discord.File("C:/Users/user/Desktop/DC_bot/cogs/nailong.png"))
                return
            
            if "得卡" in content: return

            else:
                async with message.channel.typing():
                    user_id = message.author.id
                    self.update_message_history(user_id, content, sender = "user")
                    response_content = await self.generate_response(self.get_message_history(user_id))
                    response_text = f"```\n{response_content}\n```"
    
                    if response_text:
                        await message.reply(response_text)
                        self.update_message_history(user_id, response_content, sender = "bot")


    async def generate_response(self, content: str):
        try:
            full_prompt = f"{self.role_prompt}\n\n使用者問題: {content}"
            response = model.generate_content(full_prompt, generation_config = GENERATION_CONFIG, safety_settings = SAFETY)
            gemini_text = response.text

            if '<div' in gemini_text or '<p' in gemini_text or '<br>' in gemini_text:
                soup = BeautifulSoup(gemini_text, 'html.parser')
                gemini_text_cleaned = soup.get_text(separator = ' ', strip = True)
                gemini_text = gemini_text_cleaned.replace('\n', ' ').replace('  ', ' ')

            return gemini_text

        except BlockedPromptException as e:
            print(f"Blocked prompt: {e}")
            return "抱歉，我無法回答這個問題。請嘗試其他問題。"

        except Exception as e:
            print(f"發生未知錯誤: {e}")
            return "抱歉，發生了一些錯誤。請稍後再試。"


    def update_message_history(self, user_id, message_content, sender):
        user_obj = self.bot.get_user(user_id)
        
        if user_id not in self.message_history:
            self.message_history[user_id] = []
            print(f"用戶 {user_obj.name} 的訊息歷史已初始化。")

        taiwan_tz = pytz.timezone('Asia/Taipei')
        self.message_history[user_id].append({
            "sender": sender,
            "content": message_content,
            "timestamp": datetime.datetime.now(taiwan_tz).isoformat("#", "seconds")
        })

        if len(self.message_history[user_id]) >= MAX_HISTORY_LENGTH:
            self.message_history[user_id].pop(0)


    def get_message_history(self, user_id):
        if user_id in self.message_history:
            return '\n\n'.join([msg["content"] for msg in self.message_history[user_id]])

        else:
            return f"你與使用者初次見面，{self.role_prompt}"

    @app_commands.command(name = "清除機器人記憶", description = "清除與機器人的對話歷史")
    async def clear_history(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if user_id in self.message_history:
            del self.message_history[user_id]
            print(f"用戶 {interaction.user.name} 的對話歷史已清除。")

        else: print(f"用戶 {interaction.user.name} 沒有對話歷史可清除。")
              
        try:
            reset_prompt = f"你剛被清除了與此使用者的對話記憶。\n\n{self.role_prompt}"
            response = model.generate_content(reset_prompt, generation_config = GENERATION_CONFIG, safety_settings = SAFETY)
            await interaction.response.send_message(response.text)

        except BlockedPromptException as e:
            print(f"清除記憶被GEMINI阻擋: {e}")

        except Exception as e:
            user_obj = self.bot.get_user(user_id)
            await interaction.response.send_message("發生錯誤，稍後在試。")
            print(f"用戶{user_obj.name}在清除機器人記憶時發生錯誤: {e}")

        finally: return
        
        
    @app_commands.command(name = "查看機器人記憶", description = "查看機器人記憶了多少則訊息")
    async def view_history(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
    
            if user_id in self.message_history:
                await interaction.response.send_message(f"你與機器人的對話歷史有{len(self.message_history[user_id])}/{MAX_HISTORY_LENGTH}則。")
    
            else:
                await interaction.response.send_message(f"你沒有與機器人的對話歷史。")
    
        except Exception as e:
            user_obj = self.bot.get_user(user_id)
            await interaction.response.send_message("發生錯誤，稍後在試。")
            print(f"用戶{user_obj.name}在查看機器人記憶時發生錯誤: {e}")

        finally: return

        
async def setup(bot):
    await bot.add_cog(Talking(bot))