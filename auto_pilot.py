"""
FILE CHẠY TỰ ĐỘNG HOÀN TOÀN (1-CLICK AUTO-PILOT)
Chỉ cần chạy lệnh: python auto_pilot.py
Hệ thống sẽ tự động đăng 30 nhóm theo đúng lịch trình nhanh & an toàn, không cần bấm xác nhận.
"""
from run import load_settings, menu_start_posting

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 KÍCH HOẠT CHẾ ĐỘ TỰ ĐỘNG CHẠY HOÀN TOÀN (AUTO-PILOT)")
    print("="*60)
    settings = load_settings()
    menu_start_posting(settings, auto_confirm=True)
