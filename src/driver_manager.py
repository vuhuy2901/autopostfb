import time
import socket
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class DriverManager:
    """
    Quản lý kết nối trình duyệt:
    - Luôn kết nối trực tiếp vào cửa sổ Chrome qua cổng Debug 9222 (Debugger Address).
    - Nếu Chrome chưa mở: Tự động khởi động Chrome với cổng 9222 lên màn hình.
    - Nếu Chrome đã mở sẵn: Gắn thẳng vào cửa sổ Chrome đang mở của bạn!
    """

    CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    def __init__(self, profile_dir: str = "chrome_profile", headless: bool = False, debug_port: int = 9222):
        self.profile_path = Path(profile_dir).resolve()
        self.profile_path.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.debug_port = debug_port
        self.is_attached = True

    def is_debug_port_open(self) -> bool:
        """Kiểm tra xem Chrome đã mở cổng 9222 chưa"""
        try:
            with socket.create_connection(("127.0.0.1", self.debug_port), timeout=1.0):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def get_driver(self):
        """Lấy trình điều khiển kết nối thẳng vào Chrome của bạn"""
        # Nếu chưa có Chrome mở cổng 9222 -> Tự động bật Chrome lên
        if not self.is_debug_port_open():
            print(f"\n🚀 Đang tự động bật trình duyệt Chrome lên màn hình của bạn...")
            cmd = [
                self.CHROME_EXE,
                f"--remote-debugging-port={self.debug_port}",
                f"--user-data-dir={self.profile_path}",
                "--no-first-run",
                "--no-default-browser-check",
                "https://www.facebook.com"
            ]
            subprocess.Popen(cmd)
            # Chờ Chrome khởi động và mở cổng
            for _ in range(15):
                time.sleep(1)
                if self.is_debug_port_open():
                    break

        if not self.is_debug_port_open():
            raise RuntimeError("Không thể kết nối tới Chrome cổng 9222! Hãy chắc chắn Chrome không bị chặn.")

        print(f"🔗 ĐANG KẾT NỐI VÀO CỬA SỔ CHROME TRÊN MÀN HÌNH CỦA BẠN...")
        options = Options()
        options.page_load_strategy = 'eager'  # Tải nhanh DOM, không bị kẹt chờ các video/quảng cáo nặng trên FB
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(35)  # Tránh treo vô tận nếu Facebook tải trang chậm
        print("✅ ĐÃ KẾT NỐI THÀNH CÔNG VÀO TAB CHROME CỦA BẠN!")
        return driver

    def close_driver(self, driver):
        """Ngắt kết nối Selenium mà không làm tắt cửa sổ Chrome của bạn"""
        try:
            print("🔒 Đã ngắt kết nối điều khiển (giữ nguyên cửa sổ Chrome của bạn).")
        except Exception:
            pass
