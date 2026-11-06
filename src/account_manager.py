import os
from pathlib import Path
from src.driver_manager import DriverManager

class AccountManager:
    """Quản lý các profile tài khoản Facebook độc lập"""

    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir).resolve()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_accounts(self) -> list[str]:
        """Lấy danh sách các tài khoản đã được thiết lập profile"""
        if not self.profiles_dir.exists():
            return []
        accounts = [d.name for d in self.profiles_dir.iterdir() if d.is_dir()]
        return sorted(accounts)

    def get_profile_path(self, account_name: str) -> str:
        """Đường dẫn thư mục profile của tài khoản"""
        acc_path = self.profiles_dir / account_name.strip()
        acc_path.mkdir(parents=True, exist_ok=True)
        return str(acc_path)

    def login_account(self, account_name: str):
        """Mở trình duyệt để người dùng đăng nhập tài khoản"""
        profile_path = self.get_profile_path(account_name)
        print(f"\n🚀 Đang mở trình duyệt cho tài khoản [{account_name}]...")
        print("👉 Hãy đăng nhập nick Facebook của bạn (mật khẩu, 2FA).")
        print("👉 Sau khi vào được trang Facebook cá nhân, quay lại đây bấm ENTER.\n")

        mgr = DriverManager(profile_dir=profile_path, headless=False)
        driver = mgr.get_driver()
        driver.get("https://www.facebook.com/")

        input(f"\n👉 Sau khi đăng nhập thành công nick [{account_name}], bấm [ENTER] để lưu phiên: ")
        print(f"✅ Đã lưu phiên đăng nhập cho tài khoản [{account_name}] vĩnh viễn!")
        driver.quit()
