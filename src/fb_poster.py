import time
import os
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)

from src.humanizer import Humanizer

class FBGroupPoster:
    """
    Xử lý quy trình đăng bài lên Group Facebook bằng Selenium Stealth:
    - Nhận diện chuẩn xác trạng thái đăng nhập (phân biệt rõ form login và trang chủ).
    - Hỗ trợ cả nhóm thường và nhóm Mua Bán (Marketplace / Buy-Sell groups).
    - Nhận diện khi tài khoản chưa tham gia nhóm (nút 'Tham gia nhóm' / 'Join Group').
    - Tương tác dạo tự nhiên trong nhóm (cuộn bài, thả Like) để nuôi Trust.
    - Click lệch tâm ngẫu nhiên, gõ phím kèm sửa lỗi Backspace và hỗ trợ đầy đủ Emoji.
    """

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def is_logged_in(self) -> bool:
        """Kiểm tra chuẩn xác xem tài khoản đã đăng nhập Facebook chưa"""
        try:
            current_url = self.driver.current_url.lower()
        except Exception:
            current_url = ""

        # Chỉ tải lại trang chủ Facebook nếu hiện tại chưa ở trên facebook.com
        if "facebook.com" not in current_url:
            try:
                self.driver.get("https://www.facebook.com/")
                time.sleep(2.5)
            except Exception:
                try:
                    self.driver.execute_script("window.stop();")
                except Exception:
                    pass

        # 1. Nếu có ô nhập email hoặc mật khẩu -> Chắc chắn CHƯA đăng nhập
        try:
            login_inputs = self.driver.find_elements(By.XPATH, "//input[@name='email' or @name='pass']")
            if login_inputs and any(inp.is_displayed() for inp in login_inputs):
                return False
        except Exception:
            login_inputs = []

        # 2. Nếu có nút "Đăng nhập" / "Log in" lớn của trang chủ -> CHƯA đăng nhập
        try:
            login_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[@name='login'] | //button[contains(text(), 'Đăng nhập') or contains(text(), 'Log in')]"
            )
            if login_buttons and any(b.is_displayed() for b in login_buttons):
                return False
        except Exception:
            pass

        # 3. Kiểm tra xem có thanh điều hướng hoặc avatar của người dùng hay không
        try:
            user_elements = self.driver.find_elements(
                By.XPATH,
                "//div[@role='navigation'] | //div[@aria-label='Tài khoản của bạn' or @aria-label='Your profile' or @aria-label='Menu'] | //input[@placeholder and contains(@placeholder, 'tìm kiếm') or contains(@placeholder, 'Search')]"
            )
            if user_elements and any(el.is_displayed() for el in user_elements):
                return True
        except Exception:
            pass

        try:
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "checkpoint" in current_url:
                return False
        except Exception:
            pass

        # Nếu không có ô login thì coi như đã đăng nhập
        return len(login_inputs) == 0

    def auto_login(self, email: str, password: str) -> tuple[bool, str]:
        """Tự động điền email và mật khẩu để đăng nhập Facebook"""
        driver = self.driver
        if self.is_logged_in():
            return True, "Đã đăng nhập sẵn."

        print(f"🔑 Đang tự động điền thông tin đăng nhập Facebook: {email}...")
        driver.get("https://www.facebook.com/")
        time.sleep(2.5)

        try:
            email_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='email' or @id='email']"))
            )
            email_field.clear()
            Humanizer.type_like_human(driver, email_field, email, simulate_typo=False)
            time.sleep(0.5)

            pass_field = driver.find_element(By.XPATH, "//input[@name='pass' or @id='pass']")
            pass_field.clear()
            Humanizer.type_like_human(driver, pass_field, password, simulate_typo=False)
            time.sleep(0.5)

            try:
                login_btn = driver.find_element(
                    By.XPATH,
                    "//a[.//span[text()='Log in' or text()='Log In' or text()='Đăng nhập']] | //div[@role='button'][.//span[text()='Log in' or text()='Log In' or text()='Đăng nhập']] | //button[@name='login' or @type='submit']"
                )
                Humanizer.move_and_click(driver, login_btn)
            except Exception:
                pass_field.send_keys(Keys.ENTER)

            print("⏳ Đang gửi yêu cầu đăng nhập lên Facebook...")
            time.sleep(8)

            # Kiểm tra xem có bị hỏi mã 2FA / Phê duyệt điện thoại không
            current_u = driver.current_url.lower()
            if "checkpoint" in current_u or "auth_platform" in current_u or "two_step" in current_u:
                print("\n" + "="*60)
                print("📱 FACEBOOK ĐÃ GỬI THÔNG BÁO XÁC MINH VỀ ĐIỆN THOẠI CỦA BẠN!")
                print("👉 Bạn hãy mở ứng dụng Facebook trên điện thoại, bấm Phê duyệt (nhấn số xác minh trên màn hình).")
                print("👉 Sau khi điện thoại báo thành công và màn hình Chrome vào Facebook, quay lại đây bấm ENTER.")
                print("="*60)
                input("\n👉 Bấm [ENTER] sau khi bạn đã xác nhận trên điện thoại: ")
                time.sleep(3)

            if self.is_logged_in():
                print("🎉 ĐĂNG NHẬP FACEBOOK THÀNH CÔNG VÀ ĐÃ LƯU PHIÊN!")
                return True, "Đăng nhập thành công"
            else:
                return False, "Chưa vào được Facebook sau khi đăng nhập."
        except Exception as e:
            return False, f"Lỗi khi tự động điền form: {e}"

    def check_for_checkpoint_or_block(self) -> tuple[bool, str]:
        """Quét xem có thông báo chặn tính năng hoặc checkpoint hay không"""
        current_url = self.driver.current_url.lower()
        if "checkpoint" in current_url:
            return True, "Tài khoản bị chuyển hướng sang trang Checkpoint"

        body_text = self.driver.page_source.lower()
        block_keywords = [
            "bạn tạm thời bị chặn",
            "bạn không thể sử dụng tính năng này ngay lúc này",
            "you’re temporarily blocked",
            "you can't use this feature right now",
            "tài khoản của bạn bị hạn chế",
            "your account is restricted"
        ]
        for kw in block_keywords:
            if kw in body_text:
                return True, f"Phát hiện cảnh báo Facebook: '{kw}'"
        return False, ""

    def _random_group_warmup(self, enable_engagement: bool = True):
        """Làm nóng tự nhiên trong nhóm trước khi đăng bài"""
        Humanizer.smooth_scroll(self.driver, scroll_count=random.randint(1, 2))

        if enable_engagement and random.random() < 0.30:
            try:
                like_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//div[@aria-label='Thích' or @aria-label='Like'][@role='button']"
                )
                visible_likes = [b for b in like_buttons if b.is_displayed()]
                if visible_likes:
                    chosen_like = random.choice(visible_likes[:3])
                    print("👍 Tương tác tự nhiên: Thả Like 1 bài viết trong nhóm để nuôi Trust...")
                    Humanizer.move_and_click(self.driver, chosen_like)
                    Humanizer.sleep_random(1.0, 2.0)
            except Exception:
                pass

        self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
        time.sleep(random.uniform(0.8, 1.5))

    def post_to_group(
        self,
        group_url: str,
        content: str,
        image_paths: list[str] = None,
        simulate_typo: bool = True,
        random_engagement: bool = True
    ) -> tuple[bool, str]:
        """Quy trình đăng bài nhanh & chống khóa tối đa vào 1 nhóm"""
        driver = self.driver
        # Chuẩn hóa sạch đường link URL (xóa bỏ BOM và khoảng trắng ẩn)
        group_url = str(group_url).strip().lstrip('\ufeff\u200b')
        if not group_url.startswith("http"):
            group_url = "https://" + group_url.lstrip('/')
        print(f"\n🌐 Đang mở nhóm: {group_url}")
        try:
            driver.get(group_url)
        except TimeoutException:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
        Humanizer.sleep_random(3.0, 5.0, "Tải trang nhóm")

        # 1. Kiểm tra an toàn trước
        is_blocked, block_msg = self.check_for_checkpoint_or_block()
        if is_blocked:
            return False, f"DỪNG KHẨN CẤP: {block_msg}"

        # 2. Kiểm tra nhóm có bị xóa / không tồn tại trên Facebook không
        unavailable_texts = [
            "Bạn hiện không xem được nội dung này",
            "Nội dung này hiện không hiển thị",
            "This content isn't available right now",
            "Trang này không hiển thị"
        ]
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if any(ut in page_text for ut in unavailable_texts):
            return False, "Nhóm không tồn tại hoặc đã bị Facebook xóa."

        # 3. Kiểm tra xem tài khoản đã tham gia nhóm chưa -> Tự động bấm Tham gia nếu chưa!
        join_buttons = driver.find_elements(
            By.XPATH,
            "//span[text()='Tham gia nhóm' or text()='Tham gia' or text()='Join group' or text()='Join Group']/ancestor::div[@role='button'][1]"
        )
        for jb in join_buttons:
            if jb.is_displayed():
                print("🤝 Tài khoản chưa tham gia nhóm -> Tự động bấm 'Tham gia nhóm'...")
                try:
                    driver.execute_script("arguments[0].click();", jb)
                    time.sleep(3.5)
                except Exception:
                    pass
                break

        # 3. Lướt xem nhóm & tương tác ngẫu nhiên
        self._random_group_warmup(enable_engagement=random_engagement)

        # 4. Nếu là Nhóm Mua Bán (Buy & Sell group - hiện nút 'Bán gì đó'), mới cần bấm sang tab 'Thảo luận'
        try:
            has_inline_composer = any(
                el.is_displayed() for el in driver.find_elements(
                    By.XPATH,
                    "//span[contains(text(), 'Bạn viết gì đi') or contains(text(), 'Write something')]/ancestor::div[@role='button'][1]"
                )
            )
            if not has_inline_composer:
                discussion_tabs = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href, '/discussion') or contains(@href, '/thao-luan')] | //span[text()='Thảo luận' or text()='Discussion']/ancestor::a"
                )
                for d_tab in discussion_tabs:
                    if d_tab.is_displayed():
                        print("📌 Nhóm mua bán: Bấm tab 'Thảo luận'...")
                        driver.execute_script("arguments[0].click();", d_tab)
                        time.sleep(2.5)
                        break
        except Exception:
            pass

        # 5. Tìm ô bắt đầu viết bài (luôn trỏ vào thẻ div[@role='button'] bao ngoài để click ăn 100%)
        print("🔍 Đang tìm ô soạn bài...")
        post_trigger = None
        trigger_xpaths = [
            "//span[contains(text(), 'Bạn viết gì đi') or contains(text(), 'Write something')]/ancestor::div[@role='button'][1]",
            "//span[contains(text(), 'Tạo bài viết công khai') or contains(text(), 'Create a public post')]/ancestor::div[@role='button'][1]",
            "//span[contains(text(), 'Bạn đang nghĩ gì') or contains(text(), \"What's on your mind\")]/ancestor::div[@role='button'][1]",
            "//span[contains(text(), 'Viết gì đó') or contains(text(), 'Viết bài')]/ancestor::div[@role='button'][1]",
            "//span[contains(text(), 'Tạo bài viết') or contains(text(), 'Create post')]/ancestor::div[@role='button'][1]",
            "//div[@data-pagelet='GroupInlineComposer']//div[@role='button'][1]"
        ]

        for xpath in trigger_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        post_trigger = el
                        break
                if post_trigger:
                    break
            except Exception:
                continue

        if not post_trigger:
            return False, "Không tìm thấy ô tạo bài viết (nhóm không tồn tại, chưa tham gia hoặc khóa đăng bài)."

        # Đưa ô soạn bài vào giữa màn hình và bấm mở hộp thoại soạn bài (kèm cơ chế tự động thử lại nếu hộp thoại chưa bung ra)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_trigger)
        time.sleep(0.8)

        real_dlg = None
        textbox = None

        for click_attempt in range(3):
            try:
                if click_attempt == 0:
                    driver.execute_script("arguments[0].click();", post_trigger)
                elif click_attempt == 1:
                    post_trigger.click()
                else:
                    Humanizer.move_and_click(driver, post_trigger)
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", post_trigger)
                except Exception:
                    pass

            Humanizer.sleep_random(2.0, 3.0, "Chờ hộp thoại soạn bài mở ra")

            # 6. Tìm chính xác hộp thoại Tạo bài viết (Tuyệt đối KHÔNG gõ vào ô bình luận)
            for _ in range(5):
                try:
                    dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
                    for dlg in dialogs:
                        tbs = dlg.find_elements(By.XPATH, ".//*[@contenteditable='true'][@role='textbox']")
                        for tb in tbs:
                            aria = (tb.get_attribute("aria-label") or "").lower()
                            # TUYỆT ĐỐI BỎ QUA Ô BÌNH LUẬN (COMMENT)
                            if any(w in aria for w in ["bình luận", "comment", "trả lời", "reply", "bày tỏ"]):
                                continue
                            if tb.is_displayed():
                                real_dlg = dlg
                                textbox = tb
                                break
                        if textbox:
                            break
                except Exception:
                    pass
                if textbox:
                    break
                time.sleep(0.8)

            if textbox:
                break
            print(f"🔄 Thử bấm lại mở ô tạo bài viết (lần {click_attempt + 2}/3)...")

        if not textbox:
            return False, "Không mở được hộp thoại tạo bài viết (nhóm có thể yêu cầu duyệt thành viên hoặc khóa đăng)."

        print("📋 Đã xác định đúng ô Tạo bài viết chính thức của nhóm!")
        print("✍️ Đang gõ nội dung bài viết...")
        try:
            textbox.click()
        except Exception:
            driver.execute_script("arguments[0].click();", textbox)
        time.sleep(0.5)
        Humanizer.type_like_human(driver, textbox, content, simulate_typo=simulate_typo)
        Humanizer.sleep_random(1.0, 2.0, "Kiểm tra lại văn bản")

        # 7. Đính kèm hình ảnh (nếu có) - Tìm chính xác input file nằm bên trong hộp thoại Tạo bài viết (real_dlg)
        if image_paths and len(image_paths) > 0:
            valid_images = [str(Path(p).resolve()) for p in image_paths if os.path.exists(p)]
            if valid_images:
                print(f"🖼️ Đang đính kèm {len(valid_images)} ảnh...")
                try:
                    file_input = None
                    file_inputs = real_dlg.find_elements(By.XPATH, ".//input[@type='file' and contains(@accept, 'image')]")
                    if file_inputs:
                        file_input = file_inputs[-1]

                    if not file_input:
                        photo_btn_xpaths = [
                            ".//div[@aria-label='Ảnh/video' or @aria-label='Photo/video']",
                            ".//span[text()='Ảnh/video' or text()='Photo/video']/ancestor::div[@role='button'][1]",
                        ]
                        for p_xpath in photo_btn_xpaths:
                            try:
                                btns = real_dlg.find_elements(By.XPATH, p_xpath)
                                for btn in btns:
                                    if btn.is_displayed():
                                        driver.execute_script("arguments[0].click();", btn)
                                        time.sleep(1.5)
                                        break
                            except Exception:
                                continue

                        file_inputs = real_dlg.find_elements(By.XPATH, ".//input[@type='file' and contains(@accept, 'image')]")
                        if file_inputs:
                            file_input = file_inputs[-1]

                    if file_input:
                        file_paths_str = "\n".join(valid_images)
                        file_input.send_keys(file_paths_str)
                        upload_wait_time = max(4.5, len(valid_images) * 2.5)
                        Humanizer.sleep_random(upload_wait_time, upload_wait_time + 2.0, "Chờ Facebook xử lý ảnh")
                    else:
                        print("[Lưu ý] Không tìm thấy ô tải ảnh, tiếp tục đăng văn bản.")
                except Exception as img_err:
                    print(f"[Cảnh báo] Lỗi khi đính kèm ảnh: {img_err}. Tiếp tục đăng văn bản.")

        # 8. Tìm và bấm nút Đăng (Post)
        print("🚀 Đang bấm nút Đăng bài...")
        post_btn = None
        for _ in range(15):
            try:
                # Quét nút Đăng trong dialog
                btns = real_dlg.find_elements(
                    By.XPATH,
                    ".//div[@role='button'][@aria-label='Đăng' or @aria-label='Post'] | .//span[text()='Đăng' or text()='Post']/ancestor::div[@role='button'][1] | .//div[@aria-label='Đăng' or @aria-label='Post']"
                )
                for btn in btns:
                    is_disabled = btn.get_attribute("aria-disabled")
                    if btn.is_displayed() and is_disabled != "true":
                        post_btn = btn
                        break
                if post_btn:
                    break
            except Exception:
                pass
            time.sleep(1)

        if not post_btn:
            return False, "Nút 'Đăng' bị khóa hoặc chưa sẵn sàng."

        try:
            post_btn.click()
        except Exception:
            Humanizer.move_and_click(driver, post_btn)
        print("⏳ Đang xác nhận bài viết được gửi đi...")

        try:
            # Đợi dialog đóng lại
            self.wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@role='dialog']")))
            print("✅ Đã đăng bài thành công lên nhóm!")
        except TimeoutException:
            is_blocked, block_msg = self.check_for_checkpoint_or_block()
            if is_blocked:
                return False, f"CẢNH BÁO: {block_msg}"
            time.sleep(3)

        Humanizer.sleep_random(2.0, 3.5, "Quan sát nhóm sau khi đăng")
        return True, "Đăng bài thành công!"
