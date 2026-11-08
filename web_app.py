import os
import sys
import time
import random
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv, set_key
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

load_dotenv()

from src.driver_manager import DriverManager
from src.fb_poster import FBGroupPoster
from src.spintax import SpintaxEngine
from src.image_mutator import ImageMutator
from src.history_manager import HistoryManager
from src.humanizer import Humanizer

app = Flask(__name__, template_folder="templates", static_folder="static")

CONFIG_PATH = Path("config/settings.yaml")
ENV_PATH = Path(".env")

# Trạng thái chiến dịch chạy nền
campaign_state = {
    "is_running": False,
    "stop_requested": False,
    "current_index": 0,
    "total_targets": 0,
    "current_group": "",
    "success_count": 0,
    "failed_count": 0,
    "status_text": "Sẵn sàng",
    "logs": []
}
state_lock = threading.Lock()


def add_live_log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    with state_lock:
        campaign_state["logs"].append({"time": ts, "msg": msg, "level": level})
        if len(campaign_state["logs"]) > 200:
            campaign_state["logs"] = campaign_state["logs"][-200:]


def load_settings() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_settings(settings: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, allow_unicode=True, sort_keys=False)


def get_post_folder() -> Path:
    settings = load_settings()
    folder_str = settings.get("active_post_folder", "posts/sample_post")
    folder = Path(folder_str)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "images").mkdir(parents=True, exist_ok=True)
    return folder


def load_groups() -> list[str]:
    settings = load_settings()
    groups_file = Path(settings.get("groups_file", "config/groups.txt"))
    if not groups_file.exists():
        return []
    with open(groups_file, "r", encoding="utf-8-sig") as f:
        return [
            line.strip().lstrip("\ufeff\u200b")
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def save_groups(groups_list: list[str]):
    settings = load_settings()
    groups_file = Path(settings.get("groups_file", "config/groups.txt"))
    groups_file.parent.mkdir(parents=True, exist_ok=True)
    clean_lines = [g.strip().lstrip("\ufeff\u200b") for g in groups_list if g.strip()]
    with open(groups_file, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_lines) + ("\n" if clean_lines else ""))


def sleep_interruptible(seconds: int, prefix_text: str):
    """Đếm ngược từng giây nhưng cho phép bấm Dừng bất kỳ lúc nào"""
    for rem in range(seconds, 0, -1):
        with state_lock:
            if campaign_state["stop_requested"]:
                return False
            campaign_state["status_text"] = f"{prefix_text} (còn {rem}s)..."
        time.sleep(1)
    return True


def campaign_worker():
    with state_lock:
        campaign_state["is_running"] = True
        campaign_state["stop_requested"] = False
        campaign_state["current_index"] = 0
        campaign_state["success_count"] = 0
        campaign_state["failed_count"] = 0
        campaign_state["status_text"] = "Đang khởi tạo chiến dịch..."

    add_live_log("🚀 Bắt đầu khởi chạy chiến dịch tự động đăng bài...", "info")

    try:
        settings = load_settings()
        groups = load_groups()
        if not groups:
            add_live_log("❌ Danh sách nhóm đang trống! Hãy thêm nhóm trước.", "error")
            return

        post_folder = get_post_folder()
        content_file = post_folder / "content.txt"
        raw_content = content_file.read_text(encoding="utf-8").strip() if content_file.exists() else ""
        if not raw_content:
            add_live_log("❌ Nội dung bài viết đang trống! Hãy nhập nội dung trước.", "error")
            return

        images_dir = post_folder / "images"
        raw_images = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            raw_images.extend([str(p) for p in images_dir.glob(ext)])

        history = HistoryManager()
        cooldown = settings.get("repost_cooldown_hours", 20)
        max_limit = settings.get("max_posts_per_run", 30)

        eligible_groups = []
        for g in groups:
            recently, last_time = history.is_recently_posted(g, cooldown)
            if recently:
                add_live_log(f"⏭️ Bỏ qua nhóm đã đăng gần đây ({last_time[:16]}): {g}", "warn")
            else:
                eligible_groups.append(g)

        if not eligible_groups:
            add_live_log(f"✅ Tất cả các nhóm đều đã được đăng trong {cooldown} giờ qua!", "success")
            return

        random.shuffle(eligible_groups)
        target_groups = eligible_groups[:max_limit]

        with state_lock:
            campaign_state["total_targets"] = len(target_groups)

        add_live_log(f"📋 Đã chọn {len(target_groups)} nhóm để đăng (kèm {len(raw_images)} ảnh).", "info")

        profile_dir = settings.get("browser", {}).get("user_data_dir", "chrome_profile")
        headless = settings.get("browser", {}).get("headless", False)
        mgr = DriverManager(profile_dir=profile_dir, headless=headless)

        with state_lock:
            campaign_state["status_text"] = "Đang kết nối vào trình duyệt Chrome..."
        add_live_log("🔗 Đang kết nối vào trình duyệt Chrome (cổng 9222)...", "info")

        driver = mgr.get_driver()
        poster = FBGroupPoster(driver)
        mutator = ImageMutator()

        if not poster.is_logged_in():
            load_dotenv(override=True)
            fb_email = os.getenv("FB_EMAIL", "").strip()
            fb_pass = os.getenv("FB_PASSWORD", "").strip()
            if fb_email and fb_pass:
                add_live_log(f"🔑 Tự động đăng nhập tài khoản {fb_email}...", "info")
                login_ok, login_msg = poster.auto_login(fb_email, fb_pass)
                if not login_ok:
                    add_live_log(f"⚠️ {login_msg}", "warn")
                    return
            else:
                add_live_log("⚠️ Chưa đăng nhập Facebook trên Chrome! Hãy bấm 'Mở Chrome Đăng Nhập' hoặc điền tài khoản.", "error")
                return

        delay_cfg = settings.get("delay_between_groups", {})
        break_cfg = settings.get("break_after_posts", {})
        anti_cfg = settings.get("anti_duplicate", {})

        for idx, group_url in enumerate(target_groups, 1):
            with state_lock:
                if campaign_state["stop_requested"]:
                    add_live_log("🛑 Đã dừng chiến dịch theo yêu cầu người dùng.", "warn")
                    break
                campaign_state["current_index"] = idx
                campaign_state["current_group"] = group_url
                campaign_state["status_text"] = f"Đang đăng nhóm {idx}/{len(target_groups)}: {group_url}"

            add_live_log(f"📌 [{idx}/{len(target_groups)}] Đang mở nhóm: {group_url}", "info")

            try:
                post_content = SpintaxEngine.process_content(
                    raw_content,
                    use_spintax=anti_cfg.get("use_spintax", False),
                    append_signature=anti_cfg.get("append_random_signature", False),
                    inject_zero_width=anti_cfg.get("inject_zero_width", False)
                )
                images_to_upload = mutator.prepare_images(
                    raw_images,
                    mutate=anti_cfg.get("mutate_image_hash", True)
                )

                success, msg = poster.post_to_group(
                    group_url,
                    post_content,
                    images_to_upload,
                    simulate_typo=anti_cfg.get("simulate_typo_and_fix", False),
                    random_engagement=anti_cfg.get("random_group_engagement", True)
                )
            except Exception as grp_err:
                success = False
                msg = f"Lỗi tải nhóm hoặc kết nối: {grp_err}"
                # Nếu kết nối driver bị ngắt, thử kết nối lại
                try:
                    driver = mgr.get_driver()
                    poster = FBGroupPoster(driver)
                except Exception:
                    pass

            status_str = "success" if success else "failed"
            history.record_post(group_url, str(post_folder), status_str, msg, account_name="my_account")

            if success:
                with state_lock:
                    campaign_state["success_count"] += 1
                add_live_log(f"✅ THÀNH CÔNG: {group_url} -> {msg}", "success")
            else:
                with state_lock:
                    campaign_state["failed_count"] += 1
                add_live_log(f"❌ THẤT BẠI: {group_url} -> {msg}", "error")
                if "DỪNG KHẨN CẤP" in msg or "checkpoint" in msg.lower():
                    add_live_log("🛑 CẦU DAO BẢO VỆ KÍCH HOẠT: Dừng ngay để bảo vệ tài khoản!", "error")
                    break

            if idx < len(target_groups):
                with state_lock:
                    if campaign_state["stop_requested"]:
                        add_live_log("🛑 Đã dừng chiến dịch theo yêu cầu người dùng.", "warn")
                        break

                break_count = break_cfg.get("count", 6)
                if idx % break_count == 0:
                    long_break = random.randint(
                        break_cfg.get("duration_min_seconds", 180),
                        break_cfg.get("duration_max_seconds", 300)
                    )
                    add_live_log(f"☕ Nghỉ giải lao nuôi Trust {long_break}s sau {idx} nhóm...", "info")
                    try:
                        driver.get("https://www.facebook.com/")
                    except Exception:
                        pass
                    if not sleep_interruptible(long_break, f"☕ Nghỉ giải lao nuôi Trust sau {idx} nhóm"):
                        add_live_log("🛑 Đã dừng chiến dịch trong lúc nghỉ.", "warn")
                        break
                else:
                    delay = random.randint(
                        delay_cfg.get("min_seconds", 45),
                        delay_cfg.get("max_seconds", 85)
                    )
                    add_live_log(f"⏳ Nghỉ giãn cách an toàn {delay}s trước khi sang nhóm tiếp theo...", "info")
                    if not sleep_interruptible(delay, "⏳ Nghỉ giãn cách an toàn"):
                        add_live_log("🛑 Đã dừng chiến dịch trong lúc chờ.", "warn")
                        break

        add_live_log(
            f"🏁 Hoàn tất phiên chạy! Thành công: {campaign_state['success_count']} | Thất bại: {campaign_state['failed_count']}",
            "success"
        )
    except Exception as e:
        add_live_log(f"⚠️ Lỗi hệ thống: {str(e)}", "error")
    finally:
        with state_lock:
            campaign_state["is_running"] = False
            campaign_state["stop_requested"] = False
            campaign_state["status_text"] = "Đã hoàn tất / Sẵn sàng"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_get_state():
    history = HistoryManager()
    summary = history.get_summary()
    records = history._load_data()[-40:]
    records.reverse()

    with state_lock:
        state_copy = dict(campaign_state)
        state_copy["logs"] = list(campaign_state["logs"][-80:])

    return jsonify({
        "campaign": state_copy,
        "summary": summary,
        "history": records,
        "groups_count": len(load_groups())
    })


@app.route("/api/post-data", methods=["GET", "POST"])
def api_post_data():
    post_folder = get_post_folder()
    content_file = post_folder / "content.txt"
    images_dir = post_folder / "images"

    if request.method == "POST":
        data = request.get_json(force=True)
        new_content = data.get("content", "")
        content_file.write_text(new_content, encoding="utf-8")
        add_live_log("💾 Đã lưu nội dung bài viết mới!", "success")
        return jsonify({"ok": True, "message": "Đã lưu nội dung bài viết thành công!"})

    content = content_file.read_text(encoding="utf-8") if content_file.exists() else ""
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        for p in images_dir.glob(ext):
            images.append(p.name)

    return jsonify({"content": content, "images": images})


@app.route("/api/images/<path:filename>", methods=["GET"])
def serve_post_image(filename):
    images_dir = get_post_folder() / "images"
    return send_from_directory(images_dir.resolve(), filename)


@app.route("/api/images/upload", methods=["POST"])
def api_upload_image():
    if "files" not in request.files:
        return jsonify({"ok": False, "message": "Không tìm thấy file ảnh tải lên"}), 400

    files = request.files.getlist("files")
    images_dir = get_post_folder() / "images"
    saved = []
    for f in files:
        if f and f.filename:
            fname = secure_filename(f.filename)
            if not fname:
                fname = f"img_{int(time.time())}.jpg"
            dest = images_dir / fname
            f.save(str(dest))
            saved.append(fname)

    add_live_log(f"🖼️ Đã tải lên {len(saved)} hình ảnh mới.", "success")
    return jsonify({"ok": True, "saved": saved, "message": f"Đã thêm {len(saved)} ảnh!"})


@app.route("/api/images/delete", methods=["POST"])
def api_delete_image():
    data = request.get_json(force=True)
    filename = data.get("filename", "")
    images_dir = get_post_folder() / "images"
    target = (images_dir / filename).resolve()
    if target.exists() and target.parent == images_dir.resolve():
        target.unlink()
        add_live_log(f"🗑️ Đã xóa ảnh: {filename}", "warn")
        return jsonify({"ok": True, "message": f"Đã xóa ảnh {filename}"})
    return jsonify({"ok": False, "message": "Không tìm thấy ảnh"}), 404


@app.route("/api/groups", methods=["GET", "POST"])
def api_groups():
    if request.method == "POST":
        data = request.get_json(force=True)
        raw_text = data.get("groups_text", "")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        save_groups(lines)
        add_live_log(f"📋 Đã cập nhật danh sách {len(lines)} nhóm Facebook!", "success")
        return jsonify({"ok": True, "count": len(lines), "message": f"Đã lưu {len(lines)} nhóm thành công!"})

    groups = load_groups()
    return jsonify({"groups": groups, "groups_text": "\n".join(groups), "count": len(groups)})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    load_dotenv(override=True)
    if request.method == "POST":
        data = request.get_json(force=True)
        settings = load_settings()

        settings["max_posts_per_run"] = int(data.get("max_posts_per_run", 30))
        settings["repost_cooldown_hours"] = int(data.get("repost_cooldown_hours", 20))

        settings.setdefault("delay_between_groups", {})
        settings["delay_between_groups"]["min_seconds"] = int(data.get("delay_min", 45))
        settings["delay_between_groups"]["max_seconds"] = int(data.get("delay_max", 85))

        settings.setdefault("break_after_posts", {})
        settings["break_after_posts"]["count"] = int(data.get("break_count", 6))
        settings["break_after_posts"]["duration_min_seconds"] = int(data.get("break_min", 180))
        settings["break_after_posts"]["duration_max_seconds"] = int(data.get("break_max", 300))

        settings.setdefault("anti_duplicate", {})
        settings["anti_duplicate"]["use_spintax"] = bool(data.get("use_spintax", False))
        settings["anti_duplicate"]["inject_zero_width"] = bool(data.get("inject_zero_width", False))
        settings["anti_duplicate"]["mutate_image_hash"] = bool(data.get("mutate_image_hash", True))
        settings["anti_duplicate"]["append_random_signature"] = bool(data.get("append_random_signature", False))
        settings["anti_duplicate"]["simulate_typo_and_fix"] = bool(data.get("simulate_typo_and_fix", False))
        settings["anti_duplicate"]["random_group_engagement"] = bool(data.get("random_group_engagement", True))

        save_settings(settings)

        fb_email = data.get("fb_email", "").strip()
        fb_password = data.get("fb_password", "").strip()
        if not ENV_PATH.exists():
            ENV_PATH.write_text("", encoding="utf-8")
        if fb_email:
            set_key(str(ENV_PATH), "FB_EMAIL", fb_email)
        if fb_password and fb_password != "********":
            set_key(str(ENV_PATH), "FB_PASSWORD", fb_password)

        add_live_log("⚙️ Đã lưu cấu hình hệ thống & tài khoản!", "success")
        return jsonify({"ok": True, "message": "Đã lưu cấu hình thành công!"})

    settings = load_settings()
    fb_email = os.getenv("FB_EMAIL", "")
    has_password = bool(os.getenv("FB_PASSWORD", ""))

    return jsonify({
        "max_posts_per_run": settings.get("max_posts_per_run", 30),
        "repost_cooldown_hours": settings.get("repost_cooldown_hours", 20),
        "delay_min": settings.get("delay_between_groups", {}).get("min_seconds", 45),
        "delay_max": settings.get("delay_between_groups", {}).get("max_seconds", 85),
        "break_count": settings.get("break_after_posts", {}).get("count", 6),
        "break_min": settings.get("break_after_posts", {}).get("duration_min_seconds", 180),
        "break_max": settings.get("break_after_posts", {}).get("duration_max_seconds", 300),
        "use_spintax": settings.get("anti_duplicate", {}).get("use_spintax", False),
        "inject_zero_width": settings.get("anti_duplicate", {}).get("inject_zero_width", False),
        "mutate_image_hash": settings.get("anti_duplicate", {}).get("mutate_image_hash", True),
        "append_random_signature": settings.get("anti_duplicate", {}).get("append_random_signature", False),
        "simulate_typo_and_fix": settings.get("anti_duplicate", {}).get("simulate_typo_and_fix", False),
        "random_group_engagement": settings.get("anti_duplicate", {}).get("random_group_engagement", True),
        "fb_email": fb_email,
        "fb_password": "********" if has_password else ""
    })


@app.route("/api/campaign/start", methods=["POST"])
def api_start_campaign():
    with state_lock:
        if campaign_state["is_running"]:
            return jsonify({"ok": False, "message": "Chiến dịch đang chạy rồi!"}), 400

    t = threading.Thread(target=campaign_worker, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "Đã bắt đầu chạy chiến dịch tự động đăng bài!"})


@app.route("/api/campaign/stop", methods=["POST"])
def api_stop_campaign():
    with state_lock:
        if not campaign_state["is_running"]:
            return jsonify({"ok": False, "message": "Hiện không có chiến dịch nào đang chạy."})
        campaign_state["stop_requested"] = True
        campaign_state["status_text"] = "Đang dừng chiến dịch..."
    add_live_log("🛑 Đã nhận lệnh dừng từ giao diện Web, đang chờ tác vụ hiện tại kết thúc...", "warn")
    return jsonify({"ok": True, "message": "Đã gửi lệnh dừng chiến dịch!"})


@app.route("/api/browser/open", methods=["POST"])
def api_open_browser():
    def _open():
        try:
            settings = load_settings()
            profile_dir = settings.get("browser", {}).get("user_data_dir", "chrome_profile")
            mgr = DriverManager(profile_dir=profile_dir, headless=False)
            driver = mgr.get_driver()
            driver.get("https://www.facebook.com/")
            add_live_log("🌐 Đã mở cửa sổ Chrome kết nối cổng 9222!", "success")
        except Exception as e:
            add_live_log(f"❌ Lỗi khi mở Chrome: {e}", "error")

    threading.Thread(target=_open, daemon=True).start()
    return jsonify({"ok": True, "message": "Đang bật cửa sổ Chrome kết nối cổng 9222..."})


@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    history = HistoryManager()
    history._save_data([])
    add_live_log("🧹 Đã xóa lịch sử đăng bài (cho phép đăng lại tất cả nhóm).", "warn")
    return jsonify({"ok": True, "message": "Đã làm mới lịch sử đăng bài!"})


if __name__ == "__main__":
    port = 5000
    print("\n" + "=" * 65)
    print(f"🌐 GIAO DIỆN WEB QUẢN LÝ ĐĂNG BÀI ĐÃ SẴN SÀNG TẠI: http://127.0.0.1:{port}")
    print("=" * 65 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False)
