import requests
import os
import time

def download_pokemon_images(start_id, end_id, save_directory="ExtradimensionalCrisis"):
    """
    根據編號範圍下載寶可夢卡牌圖片，並在每張圖片下載後間隔 1 秒。
    優化：僅嘗試下載六位數編號中尾數為 0 的圖片。
    對於每個編號，會嘗試下載 _00, _01, _02 變體，並跳過不存在的 URL。
    圖片將儲存到與程式碼同路徑的指定資料夾中，並以 1, 2, 3... 依序命名。
    """
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        print(f"已建立資料夾: {save_directory}")

    base_url_prefix = "https://ptcgp.twgamedb.com/Cards/07/"
    
    # 【重新引入圖片計數器】
    image_counter = 1

    # 迴圈步長設定為 10，只處理尾數為 0 的編號
    for i in range(start_id, end_id + 1):
        pokemon_id_str = str(i).zfill(3) # 六位數編號，前面補零
        
        # --- 針對每種後兩碼變體進行嘗試下載 ---
        #for suffix in possible_suffixes:
        image_url = f"{base_url_prefix}{pokemon_id_str}.webp"
        print(f"嘗試下載圖片: {image_url}")

        # 【根據計數器生成新的檔名】
        new_file_name = f"{image_counter}.webp" 
        file_path = os.path.join(save_directory, new_file_name)

        print(f"嘗試下載: {image_url}")
        try:
            # 發送 GET 請求來下載圖片內容，並設置超時
            response = requests.get(image_url, stream=True, timeout=10) 

            # 檢查回應的狀態碼
            if response.status_code == 200: # 如果狀態碼是 200 OK，表示圖片存在且成功獲取
                # 檢查 Content-Type 標頭
                content_type = response.headers.get('Content-Type', '').lower()
                if 'image/' in content_type: # 判斷是否為圖像類型
                    print(f"URL {image_url} 存在且 Content-Type 為 '{content_type}'，開始儲存為 {new_file_name}...")

                    # 確保請求沒有其他 HTTP 錯誤（如 5xx 系列伺服器錯誤）
                    response.raise_for_status() 

                    with open(file_path, 'wb') as file: # 使用 file_path 儲存
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    print(f"成功下載: {new_file_name} (原編號: {pokemon_id_str}) 到 {save_directory}")
                    image_counter += 1 # 【成功下載後，計數器加 1】
                else:
                    print(f"URL {image_url} 回應狀態碼為 200，但 Content-Type 為 '{content_type}' (非圖像類型)。跳過下載。")

            elif response.status_code == 404: # 如果狀態碼是 404 Not Found
                print(f"URL {image_url} 不存在 (狀態碼: 404)，跳過下載。")
            else: # 其他非 200/404 的狀態碼
                print(f"URL {image_url} 訪問異常 (狀態碼: {response.status_code})，跳過下載。")

        except requests.exceptions.Timeout:
            print(f"下載 {image_url} 時超時，可能網路問題或伺服器無響應。跳過。")
        except requests.exceptions.ConnectionError:
            print(f"下載 {image_url} 時連接錯誤，可能網路問題。跳過。")
        except requests.exceptions.HTTPError as e: # 捕獲由 raise_for_status() 引發的 HTTP 錯誤
            print(f"下載 {image_url} 時發生 HTTP 錯誤: {e}。跳過。")
        except requests.exceptions.RequestException as e: # 捕獲所有其他 requests 相關錯誤
            print(f"下載 {image_url} 時發生請求錯誤: {e}。跳過。")
        except Exception as e: # 捕獲任何其他未知錯誤
            print(f"處理 {image_url} 時發生未知錯誤: {e}。跳過。")
    
    # 每檢查/下載一個變體後，暫停 1 秒
        time.sleep(0.2) 
        print("等待 1 秒... (避免過於頻繁的請求)")

# --- 如何使用 --- 
# 請設定您找到的實際寶可夢圖片編號範圍
# 程式會自動調整 start_id 和 end_id，確保它們以 0 結尾並按 10 遞增
start_pokemon_id = 1
end_pokemon_id = 103

download_pokemon_images(start_pokemon_id, end_pokemon_id, save_directory="ExtradimensionalCrisis")

print("圖片下載過程已完成。")
