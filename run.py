import os
import sys
import random
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.driver_manager import DriverManager
from src.fb_poster import FBGroupPoster
from src.spintax import SpintaxEngine
from src.image_mutator import ImageMutator
from src.history_manager import HistoryManager
from src.humanizer import Humanizer

def load_settings() -> dict:
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        print("❌ Không tìm thấy file config/settings.yaml!")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_groups(groups_file: str) -> list[str]:
    path = Path(groups_file)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip().lstrip('\ufeff\u200b') for line in f if line.strip() and not line.strip().startswith("#")]
    return lines

def load_post_data(post_folder_str: str) -> tuple[str, list[str]]:
    folder = Path(post_folder_str)
    content_file = folder / "content.txt"
    images_dir = folder / "images"

    content = ""
    if content_file.exists():
        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read()

    images = []
    if images_dir.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            images.extend(list(images_dir.glob(ext)))
    
    return content, [str(p) for p in images]

def menu_login(settings: dict):
    print("\n" + "="*60)
    print("🔑 ĐĂNG NHẬP FACEBOOK (LƯU DUY NHẤT 1 LẦN VÀO PROFILE MÁY)")
    print("="*60)
    print("Hệ thống sẽ mở trình duyệt Chrome.")
    print("👉 Hãy đăng nhập tài khoản Facebook của bạn (mật khẩu, mã 2FA).")
    print("👉 Sau khi vào được trang Facebook chính, quay lại đây bấm ENTER.")
    print("="*60)

    profile_dir = settings["browser"].get("user_data_dir", "chrome_profile")
    mgr = DriverManager(profile_dir=profile_dir, headless=False)
    driver = mgr.get_driver()
    driver.get("https://www.facebook.com/")

    input("\n👉 Sau khi đăng nhập thành công vào Facebook, bấm [ENTER] tại đây: ")
    print("✅ Đã lưu phiên đăng nhập thành công! Từ nay bạn không cần nhập lại mật khẩu nữa.")
    driver.quit()

def menu_test_post(settings: dict):
    print("\n" + "="*60)
    print("🔍 XEM THỬ NGHIỆM BIẾN THIÊN NỘI DUNG & ẢNH (ANTI-BAN PRO)")
    print("="*60)
    post_folder = settings.get("active_post_folder", "posts/sample_post")
    content, images = load_post_data(post_folder)

    if not content:
        print(f"⚠️ Chưa có nội dung trong {post_folder}/content.txt")
        return

    anti_cfg = settings.get("anti_duplicate", {})
    print(f"📁 Thư mục bài đăng: {post_folder}")
    print(f"🖼️ Số lượng ảnh gốc: {len(images)}")
    for img in images:
        print(f"   - {Path(img).name}")

    print("\n📝 3 Bản biến thiên (Spintax + Zero-Width Invisible Salt + Chữ ký động):")
    for i in range(3):
        print(f"\n--- [Bản biến thể {i+1}] ---")
        processed = SpintaxEngine.process_content(
            content,
            use_spintax=anti_cfg.get("use_spintax", True),
            append_signature=anti_cfg.get("append_random_signature", True),
            inject_zero_width=anti_cfg.get("inject_zero_width", True)
        )
        print(processed)

    if images and anti_cfg.get("mutate_image_hash", True):
        mutator = ImageMutator()
        mutated = mutator.prepare_images(images, mutate=True)
        print("\n🛡️ Đã tạo ảnh biến đổi chống quét PhotoDNA / pHash:")
        for m_path in mutated:
            print(f"   -> File tải lên giả lập ảnh chụp điện thoại: {Path(m_path).name}")

def menu_view_history():
    history = HistoryManager()
    summary = history.get_summary()
    records = history._load_data()
    print("\n" + "="*60)
    print("📊 LỊCH SỬ ĐĂNG BÀI")
    print("="*60)
    print(f"Tổng số lượt thao tác: {summary['total']}")
    print(f"Thành công: {summary['success']} | Thất bại: {summary['failed']}")
    print("-" * 60)
    for rec in records[-15:]:
        print(f"[{rec['timestamp'][:19]}] {rec['status'].upper()}: {rec['group_url']} ({rec.get('message', '')})")

def menu_start_posting(settings: dict, auto_confirm: bool = False):
    print("\n" + "="*60)
    print("⚡ CHIẾN DỊCH ĐĂNG 30 NHÓM TỐC ĐỘ NHANH & CHỐNG KHÓA ĐA TẦNG")
    print("="*60)

    groups_file = settings.get("groups_file", "config/groups.txt")
    groups = load_groups(groups_file)
    if not groups:
        print(f"❌ Không có nhóm nào trong file '{groups_file}'! Vui lòng thêm link nhóm vào file trước.")
        return

    post_folder = settings.get("active_post_folder", "posts/sample_post")
    raw_content, raw_images = load_post_data(post_folder)
    if not raw_content:
        print(f"❌ File nội dung '{post_folder}/content.txt' đang trống!")
        return

    history = HistoryManager()
    cooldown = settings.get("repost_cooldown_hours", 20)
    max_limit = settings.get("max_posts_per_run", 30)

    eligible_groups = []
    for g in groups:
        recently, last_time = history.is_recently_posted(g, cooldown)
        if recently:
            print(f"⏭️ Bỏ qua nhóm đã đăng gần đây ({last_time[:16]}): {g}")
        else:
            eligible_groups.append(g)

    if not eligible_groups:
        print(f"✅ Tất cả các nhóm đều đã được đăng trong {cooldown}h qua!")
        return

    # Xáo trộn ngẫu nhiên thứ tự nhóm để không tạo quy luật lặp lại mỗi ngày
    random.shuffle(eligible_groups)
    target_groups = eligible_groups[:max_limit]

    delay_cfg = settings.get("delay_between_groups", {})
    break_cfg = settings.get("break_after_posts", {})
    anti_cfg = settings.get("anti_duplicate", {})

    print(f"\n📋 Đã sẵn sàng {len(target_groups)} nhóm (Đã trộn ngẫu nhiên thứ tự nhóm).")
    print("🛡️ CƠ CHẾ TĂNG TỐC & CHỐNG BAN ĐANG BẬT:")
    print(f"   • Giãn cách rút gọn: {delay_cfg.get('min_seconds', 45)}s – {delay_cfg.get('max_seconds', 85)}s giữa mỗi bài.")
    print(f"   • Cứ sau {break_cfg.get('count', 6)} nhóm nghỉ {break_cfg.get('duration_min_seconds', 180)//60}–{break_cfg.get('duration_max_seconds', 300)//60} phút & tự lướt Newsfeed nuôi Trust.")
    print("   • Gõ phím giả lập gõ nhầm + Backspace, hỗ trợ đầy đủ Emoji (CDP).")
    print("   • Chèn ký tự vô hình Zero-Width + Đổi pHash ảnh & giả lập tên ảnh chụp điện thoại.")
    print("   • Tự động thả Like dạo ngẫu nhiên trong nhóm trước khi đăng.")
    print("="*60)

    if not auto_confirm:
        confirm = input("👉 Bắt đầu chạy ngay? (y/n): ").strip().lower()
        if confirm not in ("y", "yes", "co", "c", ""):
            print("Đã hủy tác vụ.")
            return

    profile_dir = settings["browser"].get("user_data_dir", "chrome_profile")
    mgr = DriverManager(profile_dir=profile_dir, headless=settings["browser"]["headless"])
    driver = mgr.get_driver()
    poster = FBGroupPoster(driver)
    mutator = ImageMutator()

    try:
        if not poster.is_logged_in():
            fb_email = os.getenv("FB_EMAIL")
            fb_pass = os.getenv("FB_PASSWORD")
            if fb_email and fb_pass:
                print(f"🤖 ĐÃ TÌM THẤY TÀI KHOẢN TRONG FILE .env ({fb_email})!")
                login_ok, login_msg = poster.auto_login(fb_email, fb_pass)
                if not login_ok:
                    print(f"⚠️ {login_msg}")
                    input("\n👉 Hãy hoàn tất đăng nhập trên Chrome rồi bấm [ENTER]: ")
            else:
                print("\n" + "="*60)
                print("⚠️ CHƯA ĐĂNG NHẬP FACEBOOK TRÊN CỬA SỔ CHROME NÀY!")
                print("👉 Bạn hãy nhập tài khoản & mật khẩu của bạn vào cửa sổ Chrome đang mở trên màn hình.")
                print("👉 Sau khi vào được trang Facebook, hãy quay lại đây bấm ENTER để công cụ bắt đầu đăng!")
                print("="*60)
                input("\n👉 Bấm [ENTER] sau khi bạn đã đăng nhập xong trên Chrome: ")
                time.sleep(2)

        success_count = 0
        total_targets = len(target_groups)

        for idx, group_url in enumerate(target_groups, 1):
            print(f"\n" + "="*50)
            print(f"📌 Đang đăng Nhóm {idx}/{total_targets}: {group_url}")
            print("="*50)

            post_content = SpintaxEngine.process_content(
                raw_content,
                use_spintax=anti_cfg.get("use_spintax", True),
                append_signature=anti_cfg.get("append_random_signature", True),
                inject_zero_width=anti_cfg.get("inject_zero_width", True)
            )
            images_to_upload = mutator.prepare_images(
                raw_images,
                mutate=anti_cfg.get("mutate_image_hash", True)
            )

            success, msg = poster.post_to_group(
                group_url,
                post_content,
                images_to_upload,
                simulate_typo=anti_cfg.get("simulate_typo_and_fix", True),
                random_engagement=anti_cfg.get("random_group_engagement", True)
            )
            status_str = "success" if success else "failed"
            history.record_post(group_url, post_folder, status_str, msg, account_name="my_account")

            if success:
                success_count += 1
                print("🎉 Kết quả: ĐĂNG THÀNH CÔNG!")
            else:
                print(f"❌ Kết quả THẤT BẠI: {msg}")
                if "DỪNG KHẨN CẤP" in msg or "checkpoint" in msg.lower():
                    print("🛑 CẦU DAO TỰ NGẮT KÍCH HOẠT: Phát hiện cảnh báo từ Facebook, dừng ngay để bảo vệ nick!")
                    break

            # Kiểm tra thời gian nghỉ giữa các bài
            if idx < total_targets:
                break_count = break_cfg.get("count", 6)

                if idx % break_count == 0:
                    long_break = random.randint(
                        break_cfg.get("duration_min_seconds", 180),
                        break_cfg.get("duration_max_seconds", 300)
                    )
                    if break_cfg.get("browse_newsfeed_during_break", True):
                        Humanizer.browse_newsfeed_during_break(driver, long_break)
                    else:
                        Humanizer.countdown(long_break, f"☕ Nghỉ giải lao ngắn sau {idx} nhóm")
                else:
                    delay = random.randint(
                        delay_cfg.get("min_seconds", 45),
                        delay_cfg.get("max_seconds", 85)
                    )
                    Humanizer.countdown(delay, "⚡ Giãn cách nhanh an toàn trước nhóm tiếp theo")

        print("\n" + "="*60)
        print(f"🏁 KẾT THÚC: Thành công {success_count}/{total_targets} nhóm.")
        print("="*60)

    except KeyboardInterrupt:
        print("\n⚠️ Bạn đã bấm dừng chương trình (Ctrl+C).")
    finally:
        mutator.clean_temp()
        try:
            mgr.close_driver(driver)
        except Exception:
            pass

def main():
    while True:
        settings = load_settings()
        print("\n" + "="*60)
        print("  🤖 HỆ THỐNG TỰ ĐỘNG ĐĂNG 30 NHÓM TỐC ĐỘ NHANH (ANTI-BAN PRO) 🤖")
        print("="*60)
        print("1. 🔑 Đăng nhập Facebook (Lưu nick duy nhất vào máy)")
        print("2. ⚡ Bắt đầu tự động đăng bài (Nhanh & Chống khóa đa tầng)")
        print("3. 📝 Xem trước nội dung biến thiên (Spintax) & Ảnh")
        print("4. 📊 Xem lịch sử các bài đã đăng")
        print("0. ❌ Thoát")
        print("="*60)

        choice = input("👉 Nhập lựa chọn của bạn (0-4): ").strip()
        if choice == "1":
            menu_login(settings)
        elif choice == "2":
            menu_start_posting(settings)
        elif choice == "3":
            menu_test_post(settings)
        elif choice == "4":
            menu_view_history()
        elif choice == "0":
            print("Tạm biệt! Chúc bạn kinh doanh hiệu quả.")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng nhập lại.")

if __name__ == "__main__":
    main()
