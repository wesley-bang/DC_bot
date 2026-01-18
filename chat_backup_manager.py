import json
import os
import datetime
import pytz
import asyncio
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from collections import deque

class BackupManager:
    """統一的備份管理系統"""
    
    def __init__(self, backup_directory: str = "chat_backups", memory_directory: str = "joy_memory"):
        self.backup_directory = backup_directory
        self.memory_directory = memory_directory
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        
        # 創建必要的目錄
        os.makedirs(self.backup_directory, exist_ok=True)
        os.makedirs(self.memory_directory, exist_ok=True)
        
        # 備份任務相關
        self._backup_task = None
        self._is_running = False
        
    async def start_backup_loop(self, message_history_ref: Dict, memory_manager_ref: Any, 
                               interval_minutes: int = 15) -> None:
        """啟動定時備份循環"""
        if self._is_running:
            print("備份循環已經在運行中")
            return
            
        self._is_running = True
        print(f"備份循環已啟動，每 {interval_minutes} 分鐘執行一次")
        
        while self._is_running:
            try:
                now = datetime.datetime.now(self.taiwan_tz)
                next_minute = (now.minute // interval_minutes + 1) * interval_minutes
                
                if next_minute >= 60:
                    next_minute = 0
                    next_hour = (now.hour + 1) % 24
                else:
                    next_hour = now.hour

                next_run_time = now.replace(
                    hour=next_hour,
                    minute=next_minute,
                    second=0,
                    microsecond=0
                )
            
                if next_run_time <= now:
                    next_run_time += datetime.timedelta(minutes=interval_minutes)

                wait_seconds = (next_run_time - now).total_seconds()
                print(f"下一次自動備份將在 {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} 執行\n")
                
                await asyncio.sleep(wait_seconds)
                
                if self._is_running:  # 檢查是否仍在運行
                    await self.perform_backup(message_history_ref, memory_manager_ref)
                
            except asyncio.CancelledError:
                print("定時備份任務已取消")
                break
                
            except Exception as e:
                print(f"備份任務錯誤: {e}")
                print("一分鐘後自動重試")
                await asyncio.sleep(60) 

    async def perform_backup(self, message_history: Dict, memory_manager: Any) -> None:
        """執行完整備份"""
        try:
            print(f"正在執行完整備份... 時間(UTC+8): {datetime.datetime.now(self.taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 備份聊天歷史
            if message_history:
                self.save_chat_history(message_history)
                
            # 備份記憶系統
            if memory_manager:
                self.save_memory_system(memory_manager)
                
            print(f"完整備份完成 時間(UTC+8): {datetime.datetime.now(self.taiwan_tz).strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        except Exception as e:
            print(f"執行備份時發生錯誤: {e}")

    def stop_backup_loop(self) -> None:
        """停止備份循環"""
        self._is_running = False
        print("備份循環已停止")

    def final_backup(self, message_history: Dict, memory_manager: Any) -> None:
        """最終備份（同步執行）"""
        try:
            print("\n 執行最終備份...")
            
            if message_history:
                self.save_chat_history(message_history)
                
            if memory_manager:
                self.save_memory_system(memory_manager)
                
            print("最終備份完成\n")
            
        except Exception as e:
            print(f"最終備份失敗: {e}")

    # ==================== 聊天記錄備份 ====================
    
    def delete_old_chat_backups(self, user_id: int) -> None:
        """刪除指定用戶的舊聊天備份"""
        abs_path = os.path.abspath(self.backup_directory)
        
        if not os.path.exists(abs_path):
            return

        old_backups = []
        for filename in os.listdir(abs_path):
            if filename.startswith(f"chat_backup_{user_id}_") and filename.endswith(".json"):
                filepath = os.path.join(abs_path, filename)
                old_backups.append(filepath)

        if not old_backups:
            return

        for old_file_path in old_backups:
            try:
                os.remove(old_file_path)
                print(f"  - 已刪除舊聊天備份: {os.path.basename(old_file_path)}")
                
            except OSError as e:
                print(f"  - 無法刪除備份檔案 {os.path.basename(old_file_path)}: {e}")

    def save_chat_history(self, message_history_data: Dict) -> None:
        """保存聊天歷史"""
        if not message_history_data:
            print("無聊天紀錄可備份")
            return

        abs_path = os.path.abspath(self.backup_directory)
        os.makedirs(abs_path, exist_ok=True)

        for user_id, history in message_history_data.items():
            if not history:
                continue

            try:
                self.delete_old_chat_backups(user_id)

                timestamp = datetime.datetime.now(self.taiwan_tz).strftime("%Y%m%d_%H%M%S_%f")
                backup_file = os.path.join(abs_path, f"chat_backup_{user_id}_{timestamp}.json")
                
                # 確保歷史記錄是可序列化的
                serializable_history = self._make_serializable(history)
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "user_id": user_id,
                        "backup_time": datetime.datetime.now(self.taiwan_tz).isoformat(),
                        "message_count": len(serializable_history),
                        "messages": serializable_history
                    }, f, ensure_ascii=False, indent=2)

                print(f"已備份用戶 {user_id} 的 {len(history)} 則聊天記錄")

            except Exception as e:
                print(f"儲存用戶 {user_id} 聊天紀錄時發生錯誤: {e}")
                continue
        
        print("聊天紀錄備份完成\n")

    def load_chat_history(self) -> Dict:
        """載入聊天歷史"""
        
        loaded_history = {}
        abs_path = os.path.abspath(self.backup_directory)
        
        if not os.path.exists(abs_path):
            print(f"備份目錄 {abs_path} 不存在")
            return loaded_history
        
        print(f"正在從 {abs_path} 載入聊天紀錄...")

        latest_user_backups = {}  # {user_id: (timestamp_obj, file_path)}

        for filename in os.listdir(abs_path):
            if filename.startswith('chat_backup_') and filename.endswith('.json'):
                filepath = os.path.join(abs_path, filename)
                try:
                    parts = filename.split('_')
                    if len(parts) >= 6:
                        user_id = int(parts[2])
                        timestamp_str = f"{parts[3]}_{parts[4]}_{parts[5].split('.')[0]}"
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")

                        if user_id not in latest_user_backups or timestamp > latest_user_backups[user_id][0]:
                            latest_user_backups[user_id] = (timestamp, filepath)

                except Exception as e:
                    print(f"解析檔案 {filename} 時發生錯誤: {e}")
                    continue

        for user_id, (timestamp, filepath) in latest_user_backups.items():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    
                    # 兼容舊格式和新格式
                    if isinstance(backup_data, list):
                        # 舊格式：直接是訊息列表
                        loaded_history[user_id] = backup_data
                        message_count = len(backup_data)
                    else:
                        # 新格式：包含metadata的物件
                        loaded_history[user_id] = backup_data.get("messages", [])
                        message_count = backup_data.get("message_count", len(loaded_history[user_id]))
                    
                    print(f" 已載入用戶 {user_id} 的 {message_count} 則聊天記錄")
            
            except Exception as e:
                print(f" 載入備份檔 {filepath} 時發生錯誤: {e}")
                continue

        return loaded_history

    # ==================== 記憶系統備份 ====================
    
    def save_memory_system(self, memory_manager: Any) -> None:
        """保存記憶系統數據"""
        
        try:
            if not hasattr(memory_manager, 'short_term_memory'):
                print("記憶管理器結構異常，跳過備份")
                return
                
            # 遍歷所有用戶並保存其記憶
            saved_count = 0
            for user_id in memory_manager.short_term_memory.keys():
                memory_data = self._extract_memory_data(memory_manager, user_id)
                if memory_data:
                    self.save_user_memory(user_id, memory_data)
                    saved_count += 1
            
            print(f"記憶系統備份完成 - 已備份 {saved_count} 位用戶的記憶")
            
        except Exception as e:
            print(f"保存記憶系統時發生錯誤: {e}")

    def _extract_memory_data(self, memory_manager: Any, user_id: int) -> Optional[Dict]:
        """提取用戶記憶數據"""
        
        try:
            if user_id not in memory_manager.short_term_memory:
                return None
                
            memory_data = {
                "user_id": user_id,
                "last_updated": datetime.datetime.now(self.taiwan_tz).isoformat(),
                "short_term": list(memory_manager.short_term_memory[user_id]),
                "important": memory_manager.important_memory.get(user_id, []),
                "profile": memory_manager.user_profiles.get(user_id, {}),
                "conversation_summaries": memory_manager.conversation_summaries.get(user_id, ""),
                "version": "2.0"  # 版本標識
            }
            
            # 確保所有數據都是可序列化的
            memory_data = self._make_serializable(memory_data)
            return memory_data
            
        except Exception as e:
            print(f"提取用戶 {user_id} 記憶數據失敗: {e}")
            return None

    def save_user_memory(self, user_id: int, memory_data: Dict) -> None:
        """保存單個用戶的記憶數據"""
        
        # 保存新的JSON檔案
        memory_file = Path(self.memory_directory) / f"memory_{user_id}.json"
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
            print(f"已保存用戶 {user_id} 的記憶數據")
            
        except Exception as e:
            print(f"保存用戶 {user_id} 記憶失敗: {e}")

    def load_user_memory(self, user_id: int) -> Optional[Dict]:
        """載入單個用戶的記憶數據"""
        
        json_file = Path(self.memory_directory) / f"memory_{user_id}.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                print(f"已載入用戶 {user_id} 的記憶數據")
                return memory_data
            except Exception as e:
                print(f"載入用戶 {user_id} 記憶失敗: {e}")
    
        return None

    def clear_user_memory_storage(self, user_id: int) -> None:
        """清除用戶的記憶存儲"""

        all_memory = []
        abs_path = os.path.abspath(self.memory_directory)
        if not os.path.exists(abs_path): return
    
        for filename in os.listdir(abs_path):
            if filename.startswith(f"memory_{user_id}") and filename.endswith(".json"):
                filepath = os.path.join(abs_path, filename)
                all_memory.append(filepath)
            else: continue
            
        if not all_memory: 
            print(f"用戶 {user_id} 沒有可刪除的舊記憶")
            return

        for old_memory_path in all_memory:
            try:
                os.remove(old_memory_path)
                print(f"  - 已刪除舊記憶{os.path.basename(old_memory_path)}")
    
            except OSError as e:
                print(f"  - 無法刪除舊記憶 {os.path.basename(old_memory_path)}: {e}")
          
        

    # ==================== 工具方法 ====================
    
    def _make_serializable(self, obj: Any) -> Any:
        """遞歸地將物件轉換為可JSON序列化的格式"""
        
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, deque):
            return list(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            # 嘗試轉換為字符串
            try:
                return str(obj)
            except:
                return f"<不可序列化物件: {type(obj).__name__}>"

    def get_latest_chat_timestamp(self, user_id: int) -> Optional[datetime.datetime]:
        """獲取用戶最新聊天備份時間"""
        
        abs_path = os.path.abspath(self.backup_directory)
        
        if not os.path.exists(abs_path):
            return None

        latest_timestamp = None

        for filename in os.listdir(abs_path):
            if filename.startswith(f"chat_backup_{user_id}_") and filename.endswith(".json"):
                try:
                    parts = filename.split('_')
                    if len(parts) >= 6:
                        timestamp_str = f"{parts[3]}_{parts[4]}_{parts[5].split('.')[0]}"
                        current_timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")
                        if latest_timestamp is None or current_timestamp > latest_timestamp:
                            latest_timestamp = current_timestamp
                except Exception as e:
                    print(f"解析備份檔 {filename} 時間時發生錯誤: {e}")

        return latest_timestamp

    def get_backup_stats(self) -> Dict[str, Any]:
        """獲取備份統計信息"""
        stats = {
            "chat_backup_count": 0,
            "memory_backup_count": 0,
            "total_users": set(),
            "memory_count": 0,
            "latest_backup": None
        }
        
        # 統計聊天備份
        abs_backup_path = os.path.abspath(self.backup_directory)
        if os.path.exists(abs_backup_path):
            for filename in os.listdir(abs_backup_path):
                if filename.startswith('chat_backup_') and filename.endswith('.json'):
                    stats["chat_backup_count"] += 1
                    try:
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            user_id = int(parts[2])
                            stats["total_users"].add(user_id)
                    except:
                        pass
        
        # 統計記憶備份
        abs_memory_path = os.path.abspath(self.memory_directory)
        if os.path.exists(abs_memory_path):
            for filename in os.listdir(abs_memory_path):
                if filename.startswith('memory_'):
                    stats["memory_count"] += 1
                    stats["memory_backup_count"] += 1
                    try:
                        user_id = int(filename.split('_')[1].split('.')[0])
                        stats["total_users"].add(user_id)
                    except:
                        pass
        
        stats["total_users"] = len(stats["total_users"])
        return stats

# ==================== 兼容性函數 ====================

# 創建全局備份管理器實例
_backup_manager = BackupManager()

def delete_old_backups(user_id: int, backup_directory: str = "chat_backups"):
    """兼容性函數 - 刪除舊備份"""
    global _backup_manager
    if backup_directory != _backup_manager.backup_directory:
        _backup_manager.backup_directory = backup_directory
    _backup_manager.delete_old_chat_backups(user_id)

def save_chat_history(message_history_data: dict, backup_directory: str = "chat_backups"):
    """兼容性函數 - 保存聊天歷史"""
    global _backup_manager
    if backup_directory != _backup_manager.backup_directory:
        _backup_manager.backup_directory = backup_directory
    _backup_manager.save_chat_history(message_history_data)

def load_chat_history(backup_directory: str = "chat_backups") -> dict:
    """兼容性函數 - 載入聊天歷史"""
    global _backup_manager
    if backup_directory != _backup_manager.backup_directory:
        _backup_manager.backup_directory = backup_directory
    return _backup_manager.load_chat_history()

def get_latest_timestamp(user_id: int, backup_directory: str) -> Optional[datetime.datetime]:
    """兼容性函數 - 獲取最新時間戳"""
    global _backup_manager
    if backup_directory != _backup_manager.backup_directory:
        _backup_manager.backup_directory = backup_directory
    return _backup_manager.get_latest_chat_timestamp(user_id)
