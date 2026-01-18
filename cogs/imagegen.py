import discord
from discord.ext import commands
from discord import app_commands
import requests
import io
import os
import json
from gradio_client import Client, utils
import asyncio
import traceback # 新增：用於打印完整的錯誤堆疊追蹤
from gradio_client.exceptions import AppError # 移除 ServerError，因為它可能已在函式庫中被移除

HF_TOKEN = os.getenv("HUGGING_FACE_API_KEY")

class ImageGenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.space_api_url = "Asahina2K/animagine-xl-4.0"
        try:
            # 確保 Client 初始化時傳遞 hf_token，這是推薦的做法
            self.client = Client(self.space_api_url, hf_token=HF_TOKEN if HF_TOKEN else None)
            print(f"Gradio Client initialized for Space: {self.space_api_url}")
            # >>> 這是最重要的除錯工具！它會列印出所有 API 的端點、參數名稱和類型。 <<<
            # >>> 請用這個來確認你的 predict 呼叫是否正確。 <<<
            # print("\n--- Gradio API 介面資訊 ---")
            # print(self.client.view_api())
            # print("--- 介面資訊結束 ---\n")

        except Exception as e:
            print(f"初始化 Gradio Client 時發生錯誤：{e}")
            raise

        self.fixed_prompt_base = os.getenv("IMAGE_PROMPT_BASE")

    @app_commands.command(name = "想要喬伊做什麼都可以喔", description = "生成(色)圖片！")
    @app_commands.describe(user_prompt = "輸入您想在圖片中呈現的內容(英文！)")
    async def generate_image(self, interaction: discord.Interaction, user_prompt: str):
        await interaction.response.defer(thinking = True)

        # 合併固定 prompt 和使用者輸入的 prompt
        final_prompt = f"{self.fixed_prompt_base}{user_prompt}" + ", year 2023, best quality, masterpiece, high score, great score, absurdres"
        # 設定負面提示詞
        negative_prompt = "lowres, bad anatomy, bad hands, bad eyes, bad pussy, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry, rough, multiple girls, year 2010-2012"

        try:
            print(f"正在透過 Gradio Client 呼叫 Space: {self.space_api_url}")
            # print(f"最終 Prompt: {final_prompt}")
            # print(f"負面 Prompt: {negative_prompt}")

            # 定義一個同步的函數來執行 self.client.predict()
            def _sync_predict_call():
                # 根據 view_api() 的輸出，精確地調整參數順序和名稱
                return self.client.predict(
                    prompt=final_prompt,
            		negative_prompt=negative_prompt,
            		seed=0,
            		custom_width=1024,
            		custom_height=1024,
            		guidance_scale=5,
            		num_inference_steps=28,
            		sampler="Euler a",
            		aspect_ratio_selector="832 x 1216",
            		style_selector="(None)",
            		use_upscaler=False,
            		upscaler_strength=0.55,
            		upscale_by=1.5,
            		add_quality_tags=True,
            		api_name="/generate")

            loop = asyncio.get_running_loop()
            (generated_images_list, image_metadata_dict) = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_predict_call),
                timeout=300 # 5分鐘超時
            )
            print("Hugging face space 已接收prompt，並返回結果。")

            if generated_images_list and len(generated_images_list) > 0 and 'image' in generated_images_list[0]:
                image_path_from_client = generated_images_list[0]['image']
            else:
                raise ValueError(f"Gradio Client 沒有返回有效的圖片數據列表或圖片路徑: {generated_images_list}")

            if isinstance(image_path_from_client, str) and os.path.exists(image_path_from_client):
                with open(image_path_from_client, 'rb') as f:
                    image_bytes = f.read()
                os.remove(image_path_from_client)
            else:
                raise ValueError(f"無法識別的圖片數據格式或檔案不存在: {image_path_from_client}")

            picture = discord.File(io.BytesIO(image_bytes), filename="generated_image_gradio.png")

            await interaction.followup.send(
                f"🎨 圖片生成完成！這是為你生成的圖片：",
                file=picture
            )
            print(f"圖片已成功發送到 Discord，Prompt: {user_prompt}")

        except asyncio.TimeoutError:
            print("Gradio Client 請求超時。")
            await interaction.followup.send(
                "Oops！圖片生成超時。Hugging Face Space 可能太忙或任務太複雜，請稍後再試。"
            )
        except AppError as e: # 只捕獲 AppError
            full_traceback = traceback.format_exc()
            print(f"圖片生成時發生錯誤：{type(e).__name__}: {e}")
            print("--- 完整錯誤堆疊追蹤 ---")
            print(full_traceback)
            print("------------------------")
            
            error_message_for_user = "Hugging Face Space API 回傳錯誤。"
            await interaction.followup.send(
                f"Oops！圖片生成失敗，{error_message_for_user}\n錯誤訊息：`{e}`\n請稍後再試，或聯繫管理員。"
            )
        except Exception as e:
            full_traceback = traceback.format_exc()
            print(f"圖片生成時發生錯誤：{type(e).__name__}: {e}")
            print("--- 完整錯誤堆疊追蹤 ---")
            print(full_traceback)
            print("------------------------")

            error_message_for_user = "發生未知錯誤。"
            await interaction.followup.send(
                f"Oops！圖片生成失敗，{error_message_for_user}\n請稍後再試，或聯繫管理員。"
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageGenCog(bot))
