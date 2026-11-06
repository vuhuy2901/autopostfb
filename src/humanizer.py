import time
import random
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class Humanizer:
    """
    Bộ mô phỏng hành vi sinh trắc học người thật (Human Behavioral Biometrics):
    - Gõ phím nhịp điệu biến thiên + giả lập gõ nhầm và bấm Backspace sửa lỗi.
    - Hỗ trợ đầy đủ Emoji (vượt giới hạn BMP của ChromeDriver bằng CDP Input.insertText).
    - Cuộn trang quán tính tự nhiên, di chuột lệch tâm ngẫu nhiên.
    - Lướt bảng tin Newsfeed trong lúc nghỉ giải lao.
    """

    @staticmethod
    def sleep_random(min_seconds: float, max_seconds: float, label: str = ""):
        """Nghỉ ngẫu nhiên theo phân phối tự nhiên (Gaussian-like)"""
        mid = (min_seconds + max_seconds) / 2
        spread = (max_seconds - min_seconds) / 4
        duration = random.gauss(mid, spread)
        duration = max(min_seconds, min(max_seconds, duration))
        if label:
            print(f"⏳ {label} (~{duration:.1f}s)...")
        time.sleep(duration)

    @staticmethod
    def countdown(total_seconds: int, message: str = "Nghỉ an toàn trước nhóm tiếp theo"):
        """Đếm ngược từng giây hiển thị trực quan"""
        print(f"\n⏳ {message}: {total_seconds} giây")
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer_format = f"{mins:02d}:{secs:02d}"
            print(f"\r⏱️  Chờ: {timer_format} còn lại...", end="", flush=True)
            time.sleep(1)
        print("\r✅ Hết thời gian chờ. Tiếp tục thực hiện!            \n")

    @staticmethod
    def browse_newsfeed_during_break(driver, total_seconds: int):
        """
        Thay vì đứng im một chỗ trong lúc nghỉ giải lao giữa các đợt,
        trình duyệt sẽ quay về trang chủ Facebook và lướt đọc bảng tin như người thật.
        """
        print(f"\n☕ Nghỉ giải lao & Lướt bảng tin tự nhiên trong {total_seconds} giây (tăng độ Trust cho nick)...")
        try:
            driver.get("https://www.facebook.com/")
            time.sleep(random.uniform(3.0, 5.0))
        except Exception:
            pass

        start_time = time.time()
        while True:
            elapsed = int(time.time() - start_time)
            remaining = total_seconds - elapsed
            if remaining <= 0:
                break

            # Cứ mỗi 12-20 giây lại cuộn chuột nhẹ 1 lần trên Newsfeed
            if random.random() < 0.15:
                try:
                    scroll_px = random.randint(250, 650)
                    driver.execute_script(f"window.scrollBy({{top: {scroll_px}, behavior: 'smooth'}});")
                except Exception:
                    pass

            mins, secs = divmod(remaining, 60)
            print(f"\r☕ Đang lướt dạo Newsfeed & hạ nhiệt tài khoản: còn {mins:02d}:{secs:02d}...", end="", flush=True)
            time.sleep(1)

        print("\r✅ Đã nghỉ ngơi & tương tác dạo xong! Tiếp tục đợt đăng tiếp theo.          \n")

    @staticmethod
    def type_like_human(
        driver,
        element: WebElement,
        text: str,
        min_delay: float = 0.015,
        max_delay: float = 0.055,
        simulate_typo: bool = True
    ):
        """
        Gõ văn bản siêu thực:
        - Tự động xử lý Emoji (Unicode ngoài BMP) thông qua CDP để không bao giờ bị lỗi ChromeDriver.
        - Nhịp gõ nhanh chậm theo cụm từ.
        - Thỉnh thoảng gõ nhầm 1 ký tự rồi bấm Backspace xóa đi viết lại (đánh lừa bộ đo sinh trắc học của FB).
        """
        typo_chars = "abcdefghiklmnopqrstuvxy"
        chars_since_last_typo = 0

        # Đảm bảo ô soạn thảo Lexical đang được focus trước khi gõ
        try:
            element.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].focus(); arguments[0].click();", element)
            except Exception:
                pass
        time.sleep(0.3)

        for idx, char in enumerate(text):
            # 1. Xử lý xuống dòng trong trình soạn thảo Lexical của Facebook
            if char == '\n':
                element.send_keys(Keys.SHIFT, Keys.ENTER)
                time.sleep(random.uniform(0.12, 0.28))
                continue

            # 2. Giả lập gõ nhầm 1 chữ rồi bấm Backspace sửa lại (khoảng 1 lần mỗi 45-70 ký tự)
            chars_since_last_typo += 1
            if simulate_typo and chars_since_last_typo > random.randint(45, 70) and char.isalpha():
                chars_since_last_typo = 0
                wrong_char = random.choice(typo_chars)
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.08, 0.18))
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.06, 0.14))

            # 3. Nếu là Emoji hoặc ký tự ngoài BMP (ord > 65535), chèn qua CDP Input.insertText
            if ord(char) > 0xFFFF:
                try:
                    driver.execute_cdp_cmd("Input.insertText", {"text": char})
                except Exception:
                    # Fallback bằng JS nếu CDP không khả dụng
                    driver.execute_script(
                        "document.execCommand('insertText', false, arguments[0]);", char
                    )
                time.sleep(random.uniform(0.05, 0.12))
            else:
                element.send_keys(char)

            # 4. Nhịp nghỉ tự nhiên
            if char in ('.', ',', '!', '?', ':'):
                time.sleep(random.uniform(0.08, 0.18))
            elif char == ' ':
                time.sleep(random.uniform(0.02, 0.07))
            else:
                time.sleep(random.uniform(min_delay, max_delay))

    @staticmethod
    def smooth_scroll(driver, scroll_count: int = 2):
        """Cuộn trang ngẫu nhiên lên xuống để mô phỏng hành vi đọc bài trong nhóm"""
        for _ in range(scroll_count):
            scroll_amount = random.randint(280, 620)
            driver.execute_script(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
            time.sleep(random.uniform(1.0, 2.2))
            if random.random() > 0.65:
                back_amount = random.randint(-180, -80)
                driver.execute_script(f"window.scrollBy({{top: {back_amount}, behavior: 'smooth'}});")
                time.sleep(random.uniform(0.6, 1.2))
        # Cuộn nhẹ lại lên đầu trang để thấy rõ ô đăng bài
        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
        time.sleep(random.uniform(0.8, 1.4))

    @staticmethod
    def move_and_click(driver, element: WebElement):
        """Di chuyển chuột lệch tâm ngẫu nhiên vài pixel rồi mới click (tránh click chính xác tọa độ tâm 100%)"""
        try:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-3, 3)
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(element, offset_x, offset_y)
            actions.pause(random.uniform(0.15, 0.35))
            actions.click()
            actions.perform()
        except Exception:
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
