# talking_hybrid.py - 主要的 Cog 文件（使用統一備份管理器）
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
import asyncio

# 導入我們的記憶管理模組
from memory_manager import JoyMemoryManager
# 導入統一備份管理器
from chat_backup_manager import BackupManager

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

GENERATION_CONFIG = json.loads(os.getenv("GENERATION_CONFIG_JSON", '{}'))
SAFETY = json.loads(os.getenv("SAFETY_JSON", '[]'))
MAX_HISTORY_LENGTH = 500

intents = discord.Intents.all()

class Talking(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_history = {}  # 保留原始歷史記錄用於兼容性
        
        # 初始化統一備份管理器
        self.backup_manager = BackupManager("chat_backups", "joy_memory")
        
        # 初始化記憶管理系統，傳入備份管理器引用
        self.memory_manager = JoyMemoryManager("joy_memory", self.backup_manager)
        
        self.role_prompt = os.getenv("ROLE_PROMPT_BASE")
        self.taiwan_tz = pytz.timezone('Asia/taipei')
        
        # 從備份載入歷史記錄
        self._load_existing_data()
        
        # 啟動定時備份任務
        self._start_backup_system()

    def _load_existing_data(self):
        """載入現有的數據"""
        try:
            # 載入聊天歷史
            loaded_history = self.backup_manager.load_chat_history()
            if loaded_history:
                self.message_history = loaded_history
                print(f"已載入 {len(loaded_history)} 個用戶的聊天歷史")
            else:
                print("沒有找到現有的聊天歷史")
                
        except Exception as e:
            print(f"載入數據時發生錯誤: {e}")

    def _start_backup_system(self):
        """啟動備份系統"""
        try:
            # 創建備份任務
            asyncio.create_task(self.backup_manager.start_backup_loop(
                self.message_history, 
                self.memory_manager,
                interval_minutes=15
            ))
            print("統一備份系統已啟動")
        except Exception as e:
            print(f"啟動備份系統失敗: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("\n 喬伊混合記憶系統已成功載入")
        
        # 顯示備份統計
        stats = self.backup_manager.get_backup_stats()
        print(f"備份統計：聊天備份 {stats['chat_backup_count']} 個，記憶備份 {stats['memory_backup_count']} 個，總用戶 {stats['total_users']} 人\n")

    def cog_unload(self):
        """Cog卸載時的清理工作"""
        print("\n喬伊記憶系統正在卸載...")
        
        # 停止備份循環
        self.backup_manager.stop_backup_loop()
        
        # 執行最後一次備份
        self.backup_manager.final_backup(self.message_history, self.memory_manager)
        
        print("喬伊記憶系統已安全卸載\n")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.mention_everyone: 
            return

        if self.bot.user in message.mentions:
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()

            if content == "":
                await message.add_reaction("❓")
                return

            if "奶龍" in content:
                try:
                    await message.channel.send(file=discord.File("DC_bot/cogs/nailong.png"))
                except FileNotFoundError:
                    await message.channel.send("奶龍現在在睡覺呢～訓練員")
                return
            
            if "得卡" in content: 
                return

            # 正常對話處理
            async with message.channel.typing():
                user_id = message.author.id
                
                # 更新記憶系統
                self._update_both_histories(user_id, content, "user")
                
                # 獲取智能上下文
                context = self.memory_manager.get_context_for_response(user_id)
                
                # 生成回應
                response_content = await self.generate_response_with_context(context)
                
                if response_content and response_content.strip():
                    # 檢查回應長度，避免超過Discord限制
                    if len(response_content) > 600:
                        response_content = response_content[:600] + "..."
                    
                    response_text = f"```\n{response_content}\n```"
                    await message.reply(response_text)
                    
                    # 記錄回應到記憶
                    self._update_both_histories(user_id, response_content, "bot")
                else:
                    fallback_response = "訓練員，我現在有點暈暈的，稍等一下再跟我說話好嗎？"
                    await message.reply(fallback_response)
                    print(f"Gemini API 回傳空字串，使用者ID: {user_id}")

    def _update_both_histories(self, user_id: int, content: str, sender: str):
        """同時更新原始歷史記錄和記憶管理系統"""
        
        # 更新原始記錄（用於備份兼容性）
        self.update_message_history(user_id, content, sender)
        
        # 更新智能記憶系統
        self.memory_manager.add_message(user_id, content, sender)

    async def generate_response_with_context(self, context: str) -> str:
        """使用上下文生成回應"""
        try:
            # 構建prompt
            full_prompt = f"""{self.role_prompt}{context}請根據以上記憶和對話記錄，以喬伊的身份自然回應："""

            # 記錄prompt信息
            prompt_length = len(full_prompt)
            print(f"📝 Prompt長度: {prompt_length} 字符")
            
            # 調用API
            response = model.generate_content(
                full_prompt, 
                generation_config=GENERATION_CONFIG, 
                safety_settings=SAFETY
            )
            
            gemini_text = response.text
            
            if not gemini_text or not gemini_text.strip():
                return "訓練員你有點抽象，不知道要說什麼、、、"

            # 清理HTML標籤
            if any(tag in gemini_text for tag in ['<div', '<p', '<br>', '<span']):
                soup = BeautifulSoup(gemini_text, 'html.parser')
                gemini_text = soup.get_text(separator=' ', strip=True)
                gemini_text = ' '.join(gemini_text.split())

            return gemini_text

        except BlockedPromptException as e:
            print(f"內容被Gemini阻擋: {e}")
            return "訓練員，這個話題讓我有點害羞呢，換個話題好嗎？"

        except Exception as e:
            print(f"API調用錯誤: {e}")
            return "訓練員，我的腦袋短路了一下，稍後再試試吧？"

    def update_message_history(self, user_id: int, message_content: str, sender: str):
        """維護原始訊息歷史（用於備份相容性）"""
        
        user_obj = self.bot.get_user(user_id)
        
        if user_id not in self.message_history:
            self.message_history[user_id] = []
            print(f"用戶 {user_obj.name if user_obj else user_id} 的原始歷史已初始化")

        self.message_history[user_id].append({
            "sender": sender,
            "content": message_content,
            "timestamp": datetime.datetime.now(self.taiwan_tz).isoformat("#", "seconds")
        })

        # 維持長度限制
        if len(self.message_history[user_id]) >= MAX_HISTORY_LENGTH:
            # 移除較舊的訊息，但保留最近的一些
            remove_count = len(self.message_history[user_id]) - MAX_HISTORY_LENGTH + 10
            self.message_history[user_id] = self.message_history[user_id][remove_count:]
            print(f"用戶 {user_obj.name if user_obj else user_id} 的歷史記錄已裁剪，移除 {remove_count} 條舊記錄")

    # ==================== 管理指令 ====================
    
    @app_commands.command(name="看透喬伊的小腦袋", description="查看記憶系統統計")
    async def memory_stats(self, interaction: discord.Interaction):
        """查看記憶系統統計"""
        
        user_id = interaction.user.id
        
        # 獲取記憶統計
        memory_stats = self.memory_manager.get_memory_stats(user_id)
        
        # 獲取備份統計
        backup_stats = self.backup_manager.get_backup_stats()
        
        embed = discord.Embed(
            title="🧠 記憶系統統計",
            color=0x00ff00
        )
        
        embed.add_field(
            name="本次醒來的記憶", 
            value=f"短期記憶: {memory_stats['short']}\n重要記憶: {memory_stats['important']}\n檔案信息: {memory_stats['profile_items']}", 
            inline=True
        )
        
        embed.add_field(
            name="系統總計", 
            value=f"總用戶: {backup_stats['total_users']}\n聊天備份: {backup_stats['chat_backup_count']}\n記憶備份: {backup_stats['memory_backup_count']}", 
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="消除記憶的魔法", description="真的要讓喬伊小姐忘記你嗎？")
    async def clear_memory(self, interaction: discord.Interaction):
        """清除個人記憶"""
        
        user_id = interaction.user.id
        
        # 清除記憶
        self.memory_manager.clear_user_memory(user_id)
        
        # 清除聊天歷史
        if user_id in self.message_history:
            del self.message_history[user_id]
            print(f"用戶 {user_id} 的聊天紀錄已刪除")
            self.backup_manager.delete_old_chat_backups(user_id)
        
        # 清除備份存儲
        self.backup_manager.clear_user_memory_storage(user_id)
        
        embed = discord.Embed(
            title="🧹 記憶清除完成",
            description="喬伊小姐已經忘記過去的你了！",
            color=0xff9900
        )

        print("\n")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="立即備份", description="(管理人專用！)")
    async def backup_now(self, interaction: discord.Interaction):
        """立即執行備份"""
        
        # 簡單的權限檢查（你可以根據需要調整）
        if not interaction.user.id == 536771410694111233:
            await interaction.response.send_message("此指令僅限管理人使用", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 執行備份
            await self.backup_manager.perform_backup(self.message_history, self.memory_manager)
            
            # 獲取統計信息
            stats = self.backup_manager.get_backup_stats()
            
            embed = discord.Embed(
                title="💾 備份完成",
                description=f"已備份 {stats['total_users']} 位用戶的數據",
                color=0x00ff00
            )
            
            embed.add_field(
                name="備份詳情",
                value=f"聊天備份: {stats['chat_backup_count']}\n記憶備份: {stats['memory_backup_count']}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ 備份失敗: {str(e)}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Talking(bot))