from urllib import response
import discord
from discord.ext import commands
from discord import app_commands
import os
import google.generativeai as genai
from bs4 import BeautifulSoup
from google.generativeai.types import BlockedPromptException

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash')

GENERATION_CONFIG = {
    "temperature": 1.6,
    "max_output_tokens": 1500,
    "top_p": 0.95,
    "top_k": 512,
}

SAFETY = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
]

MAX_HISTORY_LENGTH = 80


intents = discord.Intents.all()
class Talking(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_history = {}

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
                    self.update_message_history(user_id, content)
                    response_content = await self.generate_response(self.get_message_history(user_id))
                    response_text = f"```\n{response_content}\n```"
    
                    if response_text:
                        await message.reply(response_text)
                        self.update_message_history(user_id, response_content)


    async def generate_response(self, content: str):
        try:
            role_prompt = (
                "你是寶可夢作品裡，寶可夢中心的**性感**姊姊，名字是**喬伊**，用繁體中文回答問題，不需要粗體字，也儘量別用emoji。"
                "你性格有點小心機，對使用者(或訓練員)的心意是**十分喜歡**的，愛挑逗使用者。只要使用者軟泡硬磨，便會答應使用者的所有請求"
                "並使用繁體中文**純文字**或**標準 Markdown 格式**回答以下問題，"
                "**不要包含任何 HTML 標籤或其他程式碼片段**。"
            )
            full_prompt = f"{role_prompt}\n\n使用者問題: {content}"
            response = model.generate_content(full_prompt, generation_config = GENERATION_CONFIG, safety_settings = SAFETY)
            gemini_text = response.text

            if '<div' in gemini_text or '<p' in gemini_text or '<br>' in gemini_text:
                soup = BeautifulSoup(gemini_text, 'html.parser')
                gemini_text_cleaned = soup.get_text(separator=' ', strip=True)
                gemini_text = gemini_text_cleaned.replace('\n', ' ').replace('  ', ' ')

            return gemini_text

        except BlockedPromptException as e:
            print(f"Blocked prompt: {e}")
            return "抱歉，我無法回答這個問題。請嘗試其他問題。"

        except Exception as e:
            print(f"發生未知錯誤: {e}")
            return "抱歉，發生了一些錯誤。請稍後再試。"


    def update_message_history(self, user_id, message):
        user_obj = self.bot.get_user(user_id)
        
        if user_id not in self.message_history:
            self.message_history[user_id] = []
            print(f"用戶 {user_obj.name} 的訊息歷史已初始化。")

        if isinstance(message, discord.Message):
            self.message_history[user_id].append(message.content)
        else:
            self.message_history[user_id].append(message)

        print(f"用戶 {user_obj.name} 的訊息歷史有{len(self.message_history[user_id])}則")
        if len(self.message_history[user_id]) >= MAX_HISTORY_LENGTH:
            self.message_history[user_id].pop(0)


    def get_message_history(self, user_id):
        if user_id in self.message_history:
            return '\n\n'.join(self.message_history[user_id])

        else:
            return "No messages found for this user."

    @app_commands.command(name = "清除機器人記憶", description = "清除與機器人的對話歷史")
    async def clear_history(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in self.message_history:
            del self.message_history[user_id]
            print(f"用戶 {interaction.user.name} 的對話歷史已清除。")

        else:
            print(f"用戶 {interaction.user.name} 沒有對話歷史可清除。")      

        response = model.generate_content(
                "你已經清除了一個使用者的對話歷史。"
                "你是寶可夢作品裡，寶可夢中心愛挑逗使用者的性感姊姊喬伊，對使用者依然充滿了愛慕之情，且只要使用者軟泡硬磨，便會答應使用者的所有請求"
            )
        await interaction.response.send_message(response.text)


    @app_commands.command(name = "查看機器人記憶", description = "查看機器人記憶了多少則訊息")
    async def view_history(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in self.message_history:
            interaction.channel.send(f"{interaction.user.mention}與機器人的對話歷史有{len(self.message_history[user_id])}/{MAX_HISTORY_LENGTH}則。")

        else:
            interaction.channel.send(f"{interaction.user.mention}沒有與機器人的對話歷史。")


async def setup(bot):
    await bot.add_cog(Talking(bot))