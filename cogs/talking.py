import discord
from discord.ext import commands
import os
import google.generativeai as genai
from bs4 import BeautifulSoup
from google.generativeai.types import BlockedPromptException

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')
GENERATION_CONFIG = {
    "temperature": 0.6,
    "max_output_tokens": 1500,
    "top_p": 0.9,
    "top_k": 30,
}

SAFETY = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
]

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

            if "奶龍" in content:
                await message.channel.send(file = discord.File("C:/Users/user/Desktop/DC_bot/cogs/nailong.png"))
                return
            
            if "得卡" in content: return

            else: 
                try:
                    async with message.channel.typing():
                        role_prompt = (
                            "你是寶可夢作品裡，寶可夢中心的姊姊，用繁體中文回答問題。"
                            "你性格有點高冷，但對使用者(或訓練員)的心意是**喜歡**的"
                            "並使用繁體中文**純文字**或**標準 Markdown 格式**回答以下問題，"
                            "**不要包含任何 HTML 標籤或其他程式碼片段**。"
                        )
                        full_prompt = f"{role_prompt}\n\n使用者問題：{content}"
                        response = model.generate_content(full_prompt, generation_config = GENERATION_CONFIG, safety_settings = SAFETY)
                        gemini_text = response.text

                        if '<div' in gemini_text or '<p' in gemini_text or '<br>' in gemini_text:
                            soup = BeautifulSoup(gemini_text, 'html.parser')
                            gemini_text_cleaned = soup.get_text(separator=' ', strip=True)
                            gemini_text = gemini_text_cleaned.replace('\n', ' ').replace('  ', ' ')

                        await message.reply(gemini_text)
                except BlockedPromptException as e:
                    print(f"Blocked prompt: {e}")
                    await message.reply("抱歉，我無法回答這個問題。請嘗試其他問題。")
                except Exception as e:
                    await message.reply(f"發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(Talking(bot))