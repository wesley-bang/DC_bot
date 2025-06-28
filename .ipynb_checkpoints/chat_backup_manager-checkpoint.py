import json
import os
import datetime
import pytz

BACKUP_DIRECTORY = "chat_backups"

def delete_old_backups(user_id: int, backup_directory: str = BACKUP_DIRECTORY):
    
    if not os.path.exists(backup_directory): return

    files_to_delete = []
    latest_timestamp = None
    latest_filepath = None

    for filename in os.listdir(backup_directory):
        if filename.startswith(f"chat_backup_{user_id}_") and filename.endswith(".json"):
            filepath = os.path.join(backup_directory, filename)
            try:
                parts = filename.split('_')
                if len(parts) >= 5:
                    timestamp_str = "_".join(parts[3:]).replace(".json", "")
                    current_timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if latest_timestamp is None or current_timestamp > latest_timestamp:
                        if latest_filepath:
                            files_to_delete.append(latest_filepath)
                            
                        latest_timestamp = current_timestamp
                        latest_filepath = filepath

                    else: files_to_delete.append(filepath)

                else: print(f"跳過用戶 {user_id} 不符合命名規則的檔案: {filename}")
            
            except ValueError:
                print(f"解析用戶 {user_id} 的備份檔案名 '{filename}' 中的時間戳格式錯誤，跳過此檔案。")

            except Exception as e:
                print(f"處理用戶 {user_id} 的備份檔案 '{filename}' 時發生錯誤: {e}")
                continue

    for old_file_path in files_to_delete:
        try:
            os.remove(old_file_path)
            print(f"  - 已刪除舊備份檔{os.path.basename(old_file_path)}")

        except OSError as e:
            print(f"  - 無法刪除舊備份檔案 {os.path.basename(old_file_path)}: {e}")
                            
        


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
            delete_old_backups(user_id, backup_directory)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
                if len(parts) >= 5:
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
            with open(filepath, 'r', encoding = 'utf-8') as f:
                history = json.load(f)
                loaded_history[user_id] = history
                print(f"  - 已載入用戶 (ID: {user_id}) 的最新聊天記錄: {os.path.basename(filepath)}")
        
        except Exception as e:
            print(f"  - 載入備份檔'{filepath}'時發生錯誤: {e}")
            continue

    print(f"聊天紀錄載入完成。共載入 {len(loaded_history)} 位使用者的紀錄。\n\n")
    return loaded_history
