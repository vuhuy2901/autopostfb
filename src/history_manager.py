import json
import time
from pathlib import Path
from datetime import datetime, timedelta, date

class HistoryManager:
    """Quản lý lịch sử đăng bài, chống đăng trùng lặp nhóm và xuất file log chi tiết"""

    def __init__(self, history_file: str = "data/history.json", log_file: str = "logs/posting.log"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.history_file.exists():
            self._save_data([])

    def _load_data(self) -> list[dict]:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, data: list[dict]):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_recently_posted(self, group_url: str, cooldown_hours: int = 24) -> tuple[bool, str]:
        """Kiểm tra xem nhóm này đã được đăng thành công trong vòng `cooldown_hours` qua chưa"""
        records = self._load_data()
        clean_url = group_url.strip().lower().rstrip('/')
        cutoff_time = datetime.now() - timedelta(hours=cooldown_hours)

        for rec in reversed(records):
            rec_url = rec.get("group_url", "").strip().lower().rstrip('/')
            if rec_url == clean_url and rec.get("status") == "success":
                posted_time_str = rec.get("timestamp", "")
                try:
                    posted_time = datetime.fromisoformat(posted_time_str)
                    if posted_time > cutoff_time:
                        return True, posted_time_str
                except Exception:
                    pass

        return False, ""

    def get_account_posts_today(self, account_name: str) -> int:
        """Đếm số bài đăng thành công của 1 tài khoản trong ngày hôm nay"""
        records = self._load_data()
        today_str = date.today().isoformat()
        count = 0
        for rec in records:
            if rec.get("account_name") == account_name and rec.get("status") == "success":
                rec_ts = rec.get("timestamp", "")
                if rec_ts.startswith(today_str):
                    count += 1
        return count

    def record_post(self, group_url: str, post_folder: str, status: str, message: str = "", account_name: str = "default"):
        """Ghi nhận một lượt đăng bài kèm tên nick đăng và ghi file log text"""
        now = datetime.now()
        timestamp_str = now.isoformat()
        clean_time = now.strftime("%Y-%m-%d %H:%M:%S")

        records = self._load_data()
        records.append({
            "timestamp": timestamp_str,
            "account_name": account_name,
            "group_url": group_url.strip(),
            "post_folder": post_folder,
            "status": status,
            "message": message
        })
        self._save_data(records)

        # Ghi thêm vào file text logs/posting.log để người dùng đọc dễ dàng
        try:
            with open(self.log_file, "a", encoding="utf-8") as lf:
                lf.write(f"[{clean_time}] [{status.upper()}] {group_url.strip()}\n")
                lf.write(f"       -> Trạng thái: {message}\n\n")
        except Exception:
            pass

    def get_summary(self) -> dict:
        records = self._load_data()
        total = len(records)
        success = sum(1 for r in records if r.get("status") == "success")
        failed = sum(1 for r in records if r.get("status") != "success")
        return {"total": total, "success": success, "failed": failed}
