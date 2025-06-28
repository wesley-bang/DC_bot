import json
import os
import datetime
import pytz

BACKUP_DIRECTORY = "chat_backups"

def save_chat_history(message_history_data: dict, backup_directory: str = BACKUP_DIRECTORY):
    
    if not message_history_data:
        print("無聊天紀錄可備份。")
        return
    
    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)

    for user_id, history in message_history_data.items():
        if not history:
           print(f"用戶 {user_id} 沒有聊天紀錄，跳過備份。")
           continue

        try:
            taiwan_tz = pytz.timezone('Asia/Taipei')
            timestamp = datetime.datetime.now(taiwan_tz).strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_directory, f"chat_backup_{user_id}_{timestamp}.json")
            
            with open(backup_file, 'w', encoding = 'utf-8') as f:
                json.dump(history, f, ensure_ascii = False, indent = 4)

        except Exception as e:
               print(f"處理用戶 {user_id} 的聊天紀錄時發生錯誤: {e}")
               continue
        
    print("所有聊天紀錄已成功備份。")


def load_chat_history(backup_directory: str = BACKUP_DIRECTORY) -> dict:
    
    loaded_history = {}
    if not os.path.exists(backup_directory):
        print(f"備份目錄{backup_directory}不存在，無法載入聊天紀錄。")
        return loaded_history
    
    print(f"正在從{backup_directory}載入聊天紀錄...")

    lastest_user_backups = {} #{user_id: (timestamp_obj, file_path)}

    for filename in os.listdir(backup_directory):
        if filename.startswith('chat_backup_') and filename.endswith('.json'):
            try:
                parts = filename.split('_')
                if len(parts) >= 4:
                    user_id = int(parts[2])
                    timestamp_str = f"{parts[3]}_{parts[4].split('.')[0]}" #YYYYMMDD_HHMMSS.json
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    filepath = os.path.join(backup_directory, filename)

                    if user_id not in lastest_user_backups or timestamp > lastest_user_backups[user_id][0]:
                        lastest_user_backups[user_id] = (timestamp, filepath)

            except Exception as e:
                print(f"解析檔案 {filename} 時發生錯誤: {e}")
                continue

    for user_id, (timestamp, filepath) in lastest_user_backups.items():
        try:
            with open(filename, 'r', encoding = 'utf-8') as f:
                history = json.load(f)
                loaded_history[user_id] = history
                print(f"  - 已載入用戶 (ID: {user_id}) 的最新聊天記錄: {os.path.basename(filepath)}")
        
        except Exception as e:
            print(f"  - 載入備份檔'{filepath}'時發生錯誤: {e}")
            continue

    print(f"聊天紀錄載入完成。共載入 {len(loaded_history)} 位使用者的紀錄。")
    return 
