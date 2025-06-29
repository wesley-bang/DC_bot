import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
import os
import datetime
import pytz

import chat_backup_manager

class ManualBackup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name = "手動備份對話", description = "備份你跟機器人的騷話")
    async def manual_backup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral = True)
        try:
            talking_cog = self.bot.get_cog("Talking")
            if not talking_cog:
                await interaction.followup.send("錯誤: Talking Cog 未載入")
                return

            chat_backup_manager.save_chat_history(talking_cog.message_history)
            await interaction.followup.send(f"備份成功！共{len(talking_cog.message_history.get(interaction.user.id))}則訊息被記錄！")
            print(f"用戶 {interaction.user.name} 手動備份成功")

        except Exception as e:
            await interaction.followup.send(f"備份失敗: {e}，稍後在試")
            print(f"用戶 {interaction.user.name} 手動備份發生錯誤: {e}")


    @app_commands.command(name = "查看備份狀態", description = "上次備份時間和最後對話")
    async def check_backup_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral = True)
        user_id = interaction.user.id

        talking_cog = self.bot.get_cog("Talking")
        if not talking_cog:
            await interaction.followup.send("錯誤: Talking Cog 未載入")
            return

        embed = Embed(
            title = "✨ 對話備份狀態 ✨",
            description = f"{interaction.user.display_name}和喬伊小姐的對話",
            color = Color.red()
        )

        latest_backup_time = chat_backup_manager.get_latest_timestamp(user_id, chat_backup_manager.BACKUP_DIRECTORY)

        if latest_backup_time:
            embed.add_field(
                name = "上次備份時間 🕒",
                value = f"```\n{latest_backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n```",
                inline = False
            )
        else:
            embed.add_field(
                name = "上次備份時間 🕒",
                value = "```\n無備份紀錄\n```",
                inline = False
            )

        user_history = talking_cog.message_history.get(user_id)
        last_user_msg = "無"
        last_bot_msg = "無"

        if user_history:
            found_user_msg = False
            found_bot_msg = False

            for i in reversed(range(len(user_history))):
                msg = user_history[i]
                if msg["sender"] == "user" and not found_user_msg:
                    last_user_msg = msg["content"]
                    found_user_msg = True

                elif msg["sender"] == "bot" and not found_bot_msg:
                    last_bot_msg = msg["content"]
                    found_bot_msg = True

                if found_bot_msg and found_user_msg:
                    break;

            if not found_user_msg and len(user_history) > 0 and user_history[-1]["sender"] == "user":
                last_user_msg = user_history[-1]["content"]
                
            if not found_bot_msg and len(user_history) > 0 and user_history[-1]["sender"] == "bot":
                last_bot_msg = user_history[-1]["content"]

        embed.add_field(
            name = "你最後的騷話🗣️",
            value = f"```{last_user_msg if len(last_user_msg) < 150 else last_user_msg[:147] + '...'}\n```",
            inline = False
        )
        embed.add_field(
            name = "喬伊小姐最後的回覆💬",
            value = f"```{last_bot_msg if len(last_bot_msg) < 150 else last_bot_msg[:147] + '...'}\n```",
            inline = False
        )

        taiwan_tz = pytz.timezone('Asia/Taipei')
        now = datetime.datetime.now(taiwan_tz)
        
        backup_minutes = [0, 15, 30, 45]
        next_backup_time = None

        for minute in backup_minutes:
            potential_time = now.replace(minute = minute, second = 0)
            if potential_time > now:
                next_backup_time = potential_time
                break;

        if next_backup_time is None:
            next_backup_time = now.replace(minute = 0, second = 0) + datetime.timedelta(hours = 1)


        embed.add_field(
            name = "下次定期備份時間⏰",
            value = f"```\n{next_backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n```",
            inline = False
        )

        await interaction.followup.send(embed = embed)
        
async def setup(bot):
    await bot.add_cog(ManualBackup(bot))
            