import json
import os
import datetime
import pytz

BACKUP_DIRECTORY = "chat_backups"

def delete_old_backups(user_id: int, backup_directory: str = BACKUP_DIRECTORY):
    

    all_backups = []
    abs_path = os.path.abspath(backup_directory)
    print(f"絕對路徑: {abs_path}\n")
    
    if not os.path.exists(abs_path): return

    for filename in os.listdir(abs_path):
        if filename.startswith(f"chat_backup_{user_id}_") and filename.endswith(".json"):
            filepath = os.path.join(abs_path, filename)
            all_backups.append(filepath)

        else: continue
            
                
    if not all_backups: 
        print(f"用戶 {user_id} 沒有可刪除的舊備份")
        return


    for old_file_path in all_backups:
        try:
            os.remove(old_file_path)
            print(f"  - 已刪除舊備份檔{os.path.basename(old_file_path)}")

        except OSError as e:
            print(f"  - 無法刪除舊備份檔案 {os.path.basename(old_file_path)}: {e}")
                            
        


def save_chat_history(message_history_data: dict, backup_directory: str = BACKUP_DIRECTORY):
    
    if not message_history_data:
        print("無聊天紀錄可備份。")
        return

    abs_path = os.path.abspath(backup_directory)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path)

    for user_id, history in message_history_data.items():
        if not history:
           print(f"用戶 {user_id} 沒有聊天紀錄，跳過備份。")
           continue

        try:
            delete_old_backups(user_id, abs_path)

            taiwan_tz = pytz.timezone('Asia/Taipei')
            timestamp = datetime.datetime.now(taiwan_tz).strftime("%Y%m%d_%H%M%S_%f")
            backup_file = os.path.join(abs_path, f"chat_backup_{user_id}_{timestamp}.json")
            
            with open(backup_file, 'w', encoding = 'utf-8') as f:
                json.dump(history, f, ensure_ascii = False, indent = 4)

        except Exception as e:
               print(f"處理用戶 {user_id} 的聊天紀錄時發生錯誤: {e}")
               continue
        
    print("所有聊天紀錄已成功備份。")


def load_chat_history(backup_directory: str = BACKUP_DIRECTORY) -> dict:
    
    loaded_history = {}
    abs_path = os.path.abspath(backup_directory)
    
    if not os.path.exists(abs_path):
        print(f"備份目錄{abs_path}不存在，無法載入聊天紀錄。")
        return loaded_history
    
    print(f"正在從{abs_path}載入聊天紀錄...")

    lastest_user_backups = {} #{user_id: (timestamp_obj, file_path)}

    for filename in os.listdir(abs_path):
        if filename.startswith('chat_backup_') and filename.endswith('.json'):
            filepath = os.path.join(abs_path, filename)
            try:
                parts = filename.split('_')
                if len(parts) >= 6:
                    user_id = int(parts[2])
                    timestamp_str = f"{parts[3]}_{parts[4]}_{parts[5].split('.')[0]}" #YYYYMMDD_HHMMSS_milisec.json
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")

                    if user_id not in lastest_user_backups or timestamp > lastest_user_backups[user_id][0]:
                        lastest_user_backups[user_id] = (timestamp, filepath)

            except Exception as e:
                print(f"解析檔案 {filename} 時發生錯誤: {e}")
                continue

    for user_id, (timestamp, filepath) in lastest_user_backups.items():
        try:
            with open(filepath, 'r', encoding = 'utf-8') as f:
                history = json.load(f)
                loaded_history[user_id] = history
                print(f"  - 已載入用戶 (ID: {user_id}) 的最新聊天記錄: {os.path.basename(filepath)}")
        
        except Exception as e:
            print(f"  - 載入備份檔'{filepath}'時發生錯誤: {e}")
            continue

    return loaded_history


def get_latest_timestamp(user_id: int, backup_directory: str) -> datetime.datetime or None:

    print(f"正在獲取用戶 {user_id} 的最新備份時間")
    abs_path = os.path.abspath(backup_directory)
    
    if not os.path.exists(abs_path):
        print(f"目錄 {abs_path} 不存在")
        return None

    latest_timestamp = None

    for filename in os.listdir(abs_path):
        if filename.startswith(f"chat_backup_{user_id}_") and filename.endswith(".json"):
            try:
                parts = filename.split('_')
                if len(parts) >= 6:
                    user_id = int(parts[2])
                    timestamp_str = f"{parts[3]}_{parts[4]}_{parts[5].split('.')[0]}" #YYYYMMDD_HHMMSS_milisec.json
                    current_timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")
                    if latest_timestamp is None or current_timestamp > latest_timestamp:
                        latest_timestamp = current_timestamp

                else: print(f"跳過用戶 {user_id} 不符合命名規則的檔案 '{filename}'")

            except ValueError:
                print(f"解析用戶 {user_id} 的備份檔 '{filename}' 中的時間格式錯誤")

            except Exception as e:
                print(f"解析用戶 {user_id} 的備份檔 '{filename}' 時發生錯誤: {e}")

            return latest_timestamp


    
