import discord
from discord.ext import commands
from discord import app_commands
import requests
import io
import os
from gradio_client import Client, utils
import asyncio
import traceback # 新增：用於打印完整的錯誤堆疊追蹤

HF_TOKEN = os.getenv("HUGGING_FACE_API_KEY")

class ImageGenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.space_api_url 可以是完整的 URL 或 "user/space" 格式，這裡使用您提供的 "user/space"
        self.space_api_url = "Asahina2K/animagine-xl-4.0"
        try:
            # 確保 Client 初始化時傳遞 hf_token，這是推薦的做法
            self.client = Client(self.space_api_url, hf_token=HF_TOKEN if HF_TOKEN else None)
            print(f"Gradio Client initialized for Space: {self.space_api_url}")
           #print("\n--- Gradio API 介面資訊 ---")
           #print(self.client.view_api())
           #print("--- 介面資訊結束 ---\n")

        except Exception as e:
            print(f"初始化 Gradio Client 時發生錯誤：{e}")
            # 如果初始化失敗，讓 Bot 停止運行，因為後續操作會依賴它
            raise

        self.fixed_prompt_base = "1girl, nurse Joy, Pokemon, sensitive, sexy body, medium breasts, rose red hair, wearing pink nurse uniform, lovely, full of love, hetero, parted lips, wearing lace underwear, blue eyes"

        #print(f"ImageGenCog 初始化成功")
        #print(f"固定 Prompt: {self.fixed_prompt_base}")

    
    @app_commands.command(name = "生圖片！", description = "使用 AI 生成(色)圖片！")
    @app_commands.describe(user_prompt = "輸入您想在圖片中呈現的內容(英文！)")
    async def generate_image(self, interaction: discord.Interaction, user_prompt: str):
        await interaction.response.defer(thinking = True)

        # 合併固定 prompt 和使用者輸入的 prompt
        final_prompt = f"{self.fixed_prompt_base}{user_prompt}" + ", masterpiece, high score, great score, absurdres"
        # 設定負面提示詞
        negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry"

        try:
            #print(f"正在透過 Gradio Client 呼叫 Space: {self.space_api_url}")
            #print(f"最終 Prompt: {final_prompt}")
            #print(f"負面 Prompt: {negative_prompt}")

            # 定義一個同步的函數來執行 self.client.predict()
            # 由於我們已知 predict() 在您的環境中是同步返回結果的
            def _sync_predict_call():
                # 這個呼叫將是阻塞的，並直接返回 tuple 結果
                return self.client.predict(
                    final_prompt,             # 1. prompt
                    negative_prompt,          # 2. negative_prompt
                    0,                        # 3. seed
                    1024,                     # 4. custom_width
                    1024,                     # 5. custom_height
                    7.5,                      # 6. guidance_scale
                    50,                       # 7. num_inference_steps
                    'Euler a',                # 8. sampler
                    'Custom',                 # 9. aspect_ratio_selector
                    '(None)',                 # 10. style_selector
                    False,                    # 11. use_upscaler
                    0.55,                     # 12. upscaler_strength
                    1.5,                      # 13. upscale_by
                    True,                     # 14. add_quality_tags
                    api_name="/generate"      # api_name
                )

            # 獲取當前運行的事件循環
            loop = asyncio.get_running_loop()

            # 在單獨的線程中運行同步的 _sync_predict_call 函數
            # loop.run_in_executor 會返回一個 Future，這是一個可等待物件
            (generated_images_list, image_metadata_dict) = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_predict_call), # 將 _sync_predict_call 傳遞給 executor
                timeout=300 # 5分鐘超時
            )
            print("Hugging face space 已接收prompt，並返回結果。")

            # 從返回的圖片列表中提取第一張圖片的路徑
            # 假設至少有一張圖片，並且字典中包含 'image' 鍵
            if generated_images_list and len(generated_images_list) > 0 and 'image' in generated_images_list[0]:
                image_path_from_client = generated_images_list[0]['image']
            else:
                raise ValueError(f"Gradio Client 沒有返回有效的圖片數據列表或圖片路徑: {generated_images_list}")

            # 接下來的檔案處理保持不變，使用 image_path_from_client 變數
            if isinstance(image_path_from_client, str) and os.path.exists(image_path_from_client):
                with open(image_path_from_client, 'rb') as f:
                    image_bytes = f.read()
                os.remove(image_path_from_client) # 清理臨時文件
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
        except Exception as e:
            full_traceback = traceback.format_exc()
            print(f"圖片生成時發生錯誤：{type(e).__name__}: {e}")
            print("--- 完整錯誤堆疊追蹤 ---")
            print(full_traceback)
            print("------------------------")

            error_message_for_user = "發生未知錯誤。"
            if isinstance(e, ValueError) or isinstance(e, TypeError):
                error_message_for_user = f"程式碼內部錯誤：`{e}`"
            elif hasattr(e, 'response') and hasattr(e.response, 'text'):
                status_code = getattr(e.response, 'status_code', '未知狀態碼')
                api_response_text = e.response.text
                error_message_for_user = f"Hugging Face Space API 回傳錯誤（狀態碼: {status_code}）：`{api_response_text[:500]}...`"
            else:
                error_message_for_user = f"發生錯誤 ({type(e).__name__})：`{str(e)[:500]}`"
            
            await interaction.followup.send(
                f"Oops！圖片生成失敗，{error_message_for_user}\n請稍後再試，或聯繫管理員。"
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageGenCog(bot))
    print("ImageGenCog 已載入。")