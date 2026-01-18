import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
import os
import datetime
import pytz

from chat_backup_manager import BackupManager

class ManualBackup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        # 初始化備份管理器（與主系統使用相同的目錄）
        self.backup_manager = BackupManager("chat_backups", "joy_memory")

    @app_commands.command(name="手動備份對話", description="備份你跟機器人的騷話")
    async def manual_backup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            talking_cog = self.bot.get_cog("Talking")
            if not talking_cog:
                embed = Embed(
                    title="❌ 備份失敗",
                    description="錯誤: Talking Cog 未載入",
                    color=Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            # 獲取用戶的聊天記錄數量
            user_id = interaction.user.id
            user_history = talking_cog.message_history.get(user_id, [])
            message_count = len(user_history)

            # 使用統一備份管理器執行備份
            await self.backup_manager.perform_backup(
                talking_cog.message_history, 
                talking_cog.memory_manager if hasattr(talking_cog, 'memory_manager') else None
            )

            # 創建成功的回應嵌入
            embed = Embed(
                title="✅ 備份成功！",
                description=f"你和喬伊小姐的對話已安全備份",
                color=Color.green()
            )
            
            embed.add_field(
                name="備份詳情 📊",
                value=f"```\n共備份 {message_count} 則訊息\n備份時間: {datetime.datetime.now(self.taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')}\n```",
                inline=False
            )

            # 如果有記憶系統，顯示記憶統計
            if hasattr(talking_cog, 'memory_manager'):
                memory_stats = talking_cog.memory_manager.get_memory_stats(user_id)
                embed.add_field(
                    name="記憶系統 🧠",
                    value=f"```\n短期記憶: {memory_stats['short']}\n重要記憶: {memory_stats['important']}\n個人檔案: {memory_stats['profile_items']}\n```",
                    inline=False
                )

            embed.set_footer(text=f"用戶: {interaction.user.display_name}")
            await interaction.followup.send(embed=embed)
            
            print(f"用戶 {interaction.user.name} ({user_id}) 手動備份成功 - {message_count} 則訊息")

        except Exception as e:
            error_embed = Embed(
                title="❌ 備份失敗",
                description=f"```\n{str(e)}\n```\n稍後再試試看吧！",
                color=Color.red()
            )
            await interaction.followup.send(embed=error_embed)
            print(f"用戶 {interaction.user.name} ({interaction.user.id}) 手動備份發生錯誤: {e}")

    @app_commands.command(name="查看備份狀態", description="查看上次備份時間和最後對話記錄")
    async def check_backup_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        talking_cog = self.bot.get_cog("Talking")
        if not talking_cog:
            error_embed = Embed(
                title="❌ 系統錯誤",
                description="錯誤: Talking Cog 未載入",
                color=Color.red()
            )
            await interaction.followup.send(embed=error_embed)
            return

        # 創建狀態嵌入
        embed = Embed(
            title="✨ 對話備份狀態 ✨",
            description=f"{interaction.user.display_name} 和喬伊小姐的對話紀錄",
            color=Color.blue()
        )

        # 獲取最新備份時間
        latest_backup_time = self.backup_manager.get_latest_chat_timestamp(user_id)

        if latest_backup_time:
            # 轉換為台灣時區
            if latest_backup_time.tzinfo is None:
                latest_backup_time = self.taiwan_tz.localize(latest_backup_time)
                
            else:
                latest_backup_time = latest_backup_time.astimezone(self.taiwan_tz)
                
            embed.add_field(
                name="上次備份時間 🕒",
                value=f"```\n{latest_backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n```",
                inline=False
            )
        else:
            embed.add_field(
                name="上次備份時間 🕒",
                value="```\n無備份紀錄\n```",
                inline=False
            )

        # 獲取用戶聊天歷史
        user_history = talking_cog.message_history.get(user_id, [])
        last_user_msg = "無"
        last_bot_msg = "無"

        if user_history:
            # 找最後的用戶訊息和機器人回覆
            for message in reversed(user_history):
                if message["sender"] == "user" and last_user_msg == "無":
                    last_user_msg = message["content"]
                elif message["sender"] == "bot" and last_bot_msg == "無":
                    last_bot_msg = message["content"]
                
                if last_user_msg != "無" and last_bot_msg != "無":
                    break

        # 顯示最後的對話
        embed.add_field(
            name="你最後的騷話 🗣️",
            value=f"```{self._truncate_message(last_user_msg, 150)}\n```",
            inline=False
        )
        
        embed.add_field(
            name="喬伊小姐最後的回覆 💬",
            value=f"```{self._truncate_message(last_bot_msg, 150)}\n```",
            inline=False
        )

        # 顯示記憶系統狀態（如果有）
        if hasattr(talking_cog, 'memory_manager'):
            memory_stats = talking_cog.memory_manager.get_memory_stats(user_id)
            embed.add_field(
                name="記憶系統狀態 🧠",
                value=f"```\n短期記憶: {memory_stats['short']} 條\n重要記憶: {memory_stats['important']} 條\n個人檔案: {memory_stats['profile_items']} 項\n```",
                inline=False
            )

        # 計算下次定期備份時間
        now = datetime.datetime.now(self.taiwan_tz)
        next_backup_time = self._calculate_next_backup_time(now)

        embed.add_field(
            name="下次定期備份時間 ⏰",
            value=f"```\n{next_backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n```",
            inline=False
        )

        # 顯示總對話數量
        embed.add_field(
            name="總對話數量 📈",
            value=f"```\n{len(user_history)} 則訊息\n```",
            inline=True
        )

        # 獲取系統統計
        backup_stats = self.backup_manager.get_backup_stats()
        embed.add_field(
            name="系統統計 📊",
            value=f"```\n總用戶: {backup_stats['total_users']}\n聊天備份: {backup_stats['chat_backup_count']}\n記憶備份: {backup_stats['memory_backup_count']}\n```",
            inline=True
        )

        embed.set_footer(text=f"查詢時間: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="備份統計", description="查看完整的備份系統統計")
    @app_commands.describe(show_details="是否顯示詳細信息")
    async def backup_statistics(self, interaction: discord.Interaction, show_details: bool = False):
        """查看備份系統統計"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 獲取統計數據
            backup_stats = self.backup_manager.get_backup_stats()
            
            embed = Embed(
                title="📊 備份系統統計",
                description="喬伊記憶與對話備份系統概況",
                color=Color.gold()
            )
            
            embed.add_field(
                name="系統統計 🎯",
                value=f"```\n總註冊用戶: {backup_stats['total_users']}\n聊天備份檔案: {backup_stats['chat_backup_count']}\n記憶備份檔案: {backup_stats['memory_backup_count']}\n```",
                inline=False
            )
            
            
            # 如果要顯示詳細信息
            if show_details:
                talking_cog = self.bot.get_cog("Talking")
                if talking_cog:
                    active_users = len(talking_cog.message_history)
                    total_messages = sum(len(history) for history in talking_cog.message_history.values())
                    
                    embed.add_field(
                        name="當前會話 💬",
                        value=f"```\n活躍用戶: {active_users}\n總訊息數: {total_messages}\n```",
                        inline=True
                    )
                    
                    if hasattr(talking_cog, 'memory_manager'):
                        # 統計所有用戶的記憶
                        total_short = sum(talking_cog.memory_manager.get_memory_stats(uid)['short'] 
                                        for uid in talking_cog.message_history.keys())
                        total_important = sum(talking_cog.memory_manager.get_memory_stats(uid)['important'] 
                                            for uid in talking_cog.message_history.keys())
                        
                        embed.add_field(
                            name="記憶系統 🧠",
                            value=f"```\n總短期記憶: {total_short}\n總重要記憶: {total_important}\n```",
                            inline=True
                        )
            
            current_time = datetime.datetime.now(self.taiwan_tz)
            embed.set_footer(text=f"統計時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = Embed(
                title="❌ 統計查詢失敗",
                description=f"```\n{str(e)}\n```",
                color=Color.red()
            )
            await interaction.followup.send(embed=error_embed)


    @app_commands.command(name="系統健康檢查", description="檢查備份系統健康狀態")
    async def system_health_check(self, interaction: discord.Interaction):
        """系統健康檢查"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            embed = Embed(
                title="🔍 系統健康檢查",
                description="正在檢查備份系統的健康狀態...",
                color=Color.blue()
            )
            
            health_issues = []
            health_status = "健康"
            
            # 檢查備份目錄
            backup_path = os.path.abspath(self.backup_manager.backup_directory)
            memory_path = os.path.abspath(self.backup_manager.memory_directory)
            
            if not os.path.exists(backup_path):
                health_issues.append("❌ 聊天備份目錄不存在")
            
            if not os.path.exists(memory_path):
                health_issues.append("❌ 記憶備份目錄不存在")
            
            
            # 檢查Talking Cog狀態
            talking_cog = self.bot.get_cog("Talking")
            if not talking_cog:
                health_issues.append("❌ Talking Cog 未載入")
                health_status = "異常"
            elif not hasattr(talking_cog, 'backup_manager'):
                health_issues.append("⚠️ Talking Cog 缺少備份管理器")
                health_status = "需要維護"
            elif not hasattr(talking_cog, 'memory_manager'):
                health_issues.append("⚠️ Talking Cog 缺少記憶管理器")
                health_status = "需要維護"
            
            # 檢查備份循環狀態
            if talking_cog and hasattr(talking_cog, 'backup_manager'):
                if not talking_cog.backup_manager._is_running:
                    health_issues.append("⚠️ 自動備份循環未運行")
                    health_status = "需要維護"
            
            # 設置顏色
            if health_status == "健康":
                embed.color = Color.green()
            elif health_status == "需要維護":
                embed.color = Color.orange()
            else:
                embed.color = Color.red()
            
            # 更新嵌入內容
            embed.title = f"🔍 系統健康檢查 - {health_status}"
            
            if health_issues:
                issues_text = "\n".join(health_issues)
                embed.add_field(
                    name="發現的問題 🔧",
                    value=f"```\n{issues_text}\n```",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ 系統狀態",
                    value="```\n所有檢查項目都正常\n系統運行狀況良好\n```",
                    inline=False
                )
            
            embed.add_field(
                name="目錄路徑 📁",
                value=f"```\n聊天備份: {backup_path}\n記憶備份: {memory_path}\n```",
                inline=False
            )
            
            current_time = datetime.datetime.now(self.taiwan_tz)
            embed.set_footer(text=f"檢查時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = Embed(
                title="❌ 健康檢查失敗",
                description=f"```\n{str(e)}\n```",
                color=Color.red()
            )
            await interaction.followup.send(embed=error_embed)

    def _truncate_message(self, message: str, max_length: int = 150) -> str:
        """截斷過長的訊息"""
        if len(message) <= max_length:
            return message
        return message[:max_length - 3] + "..."

    def _calculate_next_backup_time(self, current_time: datetime.datetime) -> datetime.datetime:
        """計算下次備份時間（每15分鐘一次）"""
        backup_minutes = [0, 15, 30, 45]
        
        for minute in backup_minutes:
            potential_time = current_time.replace(minute=minute, second=0, microsecond=0)
            if potential_time > current_time:
                return potential_time
        
        # 如果當前小時內沒有下次備份時間，則返回下一小時的00分
        next_hour_time = current_time.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        return next_hour_time


async def setup(bot):
    await bot.add_cog(ManualBackup(bot))