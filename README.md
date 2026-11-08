# 🚀 Facebook Group Auto Poster (Hệ Thống Tự Động Đăng Bài Group Facebook)

Hệ thống tự động hóa quy trình đăng bài và hình ảnh lên danh sách hàng chục nhóm Facebook sử dụng **Python + Selenium**, tối ưu chống checkpoint, chống spam và hỗ trợ điều khiển trực tiếp trên trình duyệt Google Chrome thật.

---

## 🌟 Tính Năng Nổi Bật

1. **Kết Nối Trình Duyệt Thật (Chrome Remote Debugging):**
   - Hoạt động trực tiếp trên phiên bản Google Chrome chính chủ, giữ nguyên vân tay trình duyệt (Canvas, WebGL, AudioContext), cookies và lịch sử duyệt web.
   - Không bị các thuật toán phát hiện bot tự động như Puppeteer/Selenium thông thường chặn lại.
2. **Cơ Chế Đăng Bài Chuẩn Xác (Modal Dialog Lexical Composer):**
   - Tự động nhận diện và tương tác chuẩn xác vào hộp thoại tạo bài viết của Facebook.
   - Bộ lọc an toàn tuyệt đối: Không bao giờ gõ nhầm vào ô bình luận của các bài viết khác trong nhóm.
   - Tự động chuyển tab thảo luận nếu là nhóm Mua Bán (Buy & Sell).
   - Tự động phát hiện nhóm đã bị xóa hoặc tài khoản chưa tham gia để gửi yêu cầu tham gia.
3. **Bộ Công Cụ Chống Khóa & Chống Trùng Lặp (Anti-Ban Pro):**
   - **Đổi pHash ảnh (Image Mutation):** Tự động xóa EXIF, micro-crop viền 1-3px, thêm micro-noise và lưu tên file ngẫu nhiên như ảnh chụp từ camera điện thoại (`IMG_YYYYMMDD_HHMMSS.jpg`).
   - **Giãn cách tự nhiên:** Thiết lập thời gian chờ ngẫu nhiên giữa các nhóm (mặc định 45s – 85s).
   - **Nghỉ giải lao & Nuôi Trust:** Cứ sau 6 nhóm sẽ tự động về Newsfeed lướt dạo 3 – 5 phút để hạ nhiệt tài khoản.
   - **Tùy chọn Spintax & Zero-Width:** Tùy biến nội dung hoặc giữ nguyên văn 100% theo nhu cầu.

---

## 📁 Cấu Trúc Dự Án

```text
ai_company/
├── config/
│   ├── settings.yaml         # File cấu hình thời gian giãn cách, số lượng nhóm, tính năng chống spam
│   └── groups.txt            # Danh sách URL các nhóm Facebook cần đăng (mỗi dòng 1 link)
├── posts/
│   └── sample_post/
│       ├── content.txt       # Nội dung văn bản bài viết
│       └── images/           # Thư mục chứa các hình ảnh đính kèm bài viết
├── src/
│   ├── driver_manager.py     # Quản lý kết nối cổng Debug 9222 và Chrome profile
│   ├── fb_poster.py          # Logic đăng bài, upload ảnh, click nút Đăng và xử lý lỗi nhóm
│   ├── humanizer.py          # Mô phỏng gõ phím, cuộn trang, di chuột, lướt Newsfeed
│   ├── image_mutator.py      # Thay đổi mã băm ảnh (pHash) và xóa EXIF
│   ├── spintax.py            # Trộn nội dung và chèn ký tự vô hình
│   └── history_manager.py    # Ghi nhận lịch sử và xuất file logs/posting.log
├── .env.example              # Mẫu cấu hình tài khoản (copy thành .env)
├── .gitignore                # Danh sách loại trừ bảo mật (KHÔNG ĐƯỢC ĐẨY TÀI KHOẢN / COOKIE LÊN GIT)
├── requirements.txt          # Danh sách thư viện Python cần cài đặt
├── run.py                    # Menu điều khiển bằng dòng lệnh (CLI tương tác)
├── auto_pilot.py             # Script chạy tự động hoàn toàn chỉ với 1 lệnh
├── CHAY_DANG_BAI.bat         # File kích hoạt nhanh 1-Click trên Windows
└── README.md                 # Tài liệu hướng dẫn sử dụng chi tiết
```

---

## 🛠️ Yêu Cầu Môi Trường

- **Hệ điều hành:** Windows 10 / 11 (hoặc Linux / macOS có cài đặt Google Chrome).
- **Python:** Phiên bản `3.10` trở lên.
- **Trình duyệt:** Google Chrome bản mới nhất.

---

## 📥 Hướng Dẫn Cài Đặt Từng Bước Cho Người Mới

### Bước 1: Tải mã nguồn về máy
Mở Terminal / PowerShell và chạy lệnh:
```bash
git clone https://github.com/vuhuy2901/autopostfb.git
cd autopostfb
```

### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```bash
# Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# Kích hoạt môi trường ảo:
# Trên Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Hoặc trên Windows Command Prompt (CMD):
.\venv\Scripts\activate.bat

# Cài đặt toàn bộ thư viện phụ thuộc:
pip install -r requirements.txt
```

### Bước 3: Cấu hình tài khoản an toàn (.env)
1. Tạo file `.env` bằng cách sao chép từ `.env.example`:
   ```bash
   cp .env.example .env
   ```
   *(Trên Windows CMD dùng `copy .env.example .env`)*
2. Mở file `.env` và nhập tài khoản Facebook:
   ```env
   FB_EMAIL=email_hoac_sdt_cua_ban@gmail.com
   FB_PASSWORD=mat_khau_cua_ban
   ```
> ⚠️ **LƯU Ý BẢO MẬT QUAN TRỌNG:**
> File `.env` và thư mục `chrome_profile/` đã được cấu hình trong `.gitignore`. **TUYỆT ĐỐI KHÔNG xóa `.gitignore` hoặc đẩy tài khoản cá nhân lên Git public!**

---

## ⚙️ Thiết Lập Bài Đăng & Danh Sách Nhóm

### 1. Chuẩn bị nội dung bài viết
- Chỉnh sửa nội dung trong file: `posts/sample_post/content.txt`.
- Copy các hình ảnh bạn muốn đính kèm vào thư mục: `posts/sample_post/images/` (hỗ trợ JPG, PNG, WEBP).

### 2. Danh sách nhóm Facebook cần đăng
- Mở file `config/groups.txt` và dán danh sách URL nhóm Facebook vào (mỗi link 1 dòng), ví dụ:
  ```text
  https://www.facebook.com/groups/137432553631895/
  https://www.facebook.com/groups/1016236275156493/
  https://www.facebook.com/groups/3112215695755075/
  ```

### 3. Tùy chỉnh thông số chạy (`config/settings.yaml`)
Bạn có thể điều chỉnh thời gian nghỉ và cơ chế đăng trong file `config/settings.yaml`:
```yaml
# Số nhóm tối đa đăng trong 1 đợt chạy:
max_posts_per_run: 30

# Giãn cách nghỉ giữa 2 nhóm liên tiếp:
delay_between_groups:
  min_seconds: 45      # Tối thiểu 45s
  max_seconds: 85      # Tối đa 85s

# Giải lao nuôi Trust:
break_after_posts:
  count: 6             # Cứ sau 6 nhóm
  duration_min_seconds: 180  # Nghỉ 3 phút và tự động lướt Newsfeed
  duration_max_seconds: 300  # Tối đa 5 phút
```

---

## 🚀 Hướng Dẫn Vận Hành

### Cách 1: Giao Diện Web Trực Quan (Khuyên dùng)
Chỉ cần chạy lệnh:
```bash
python web_app.py
```
Hoặc trên Windows, click đúp vào file **`MO_GIAO_DIEN_WEB.bat`**.
- Trình duyệt sẽ tự động mở bảng điều khiển tại địa chỉ: `http://127.0.0.1:5000`
- Trên giao diện Web, bạn có thể:
  - Bấm **🚀 BẮT ĐẦU CHẠY AUTO** hoặc **🛑 DỪNG CHIẾN DỊCH** bất kỳ lúc nào.
  - Xem nhật ký hoạt động thời gian thực (Live Console), tiến độ phần trăm và thống kê Thành công / Thất bại.
  - Chỉnh sửa nội dung bài viết, tải lên hoặc xóa ảnh đính kèm.
  - Quản lý danh sách link nhóm Facebook và cấu hình thời gian nghỉ, tài khoản `.env` ngay trên Web.

### Cách 2: Chạy tự động 1-Click bằng Script
Chỉ cần chạy lệnh:
```bash
python auto_pilot.py
```
Hoặc trên máy tính Windows, bạn chỉ cần click đúp vào file **`CHAY_DANG_BAI.bat`**.

Hệ thống sẽ:
1. Tự động kiểm tra hoặc khởi chạy Chrome với cổng Debug `9222`.
2. Tự động đăng nhập tài khoản Facebook (hoặc sử dụng phiên đăng nhập đã có sẵn trong `chrome_profile`).
3. Kiểm tra danh sách nhóm, tự động đăng lần lượt từng nhóm, đính kèm ảnh và ghi nhật ký.

### Cách 3: Sử dụng giao diện Menu dòng lệnh
Nếu bạn muốn xem menu tương tác trực quan trên Terminal:
```bash
python run.py
```
Menu sẽ cung cấp các tùy chọn:
- `1. Bắt đầu chiến dịch tự động đăng bài`
- `2. Xem bài viết và ảnh mẫu`
- `3. Xem nhật ký & lịch sử đăng bài gần đây`
- `4. Kiểm tra trạng thái đăng nhập Facebook`
- `0. Thoát chương trình`

---

## 📊 Xem Lịch Sử & Nhật Ký Hoạt Động

- Mọi lượt đăng bài (thành công hay thất bại, nguyên nhân chi tiết) đều được ghi nhận trực tiếp vào file:
  `logs/posting.log`
- Lịch sử chống đăng trùng nhóm được lưu trữ tại `data/history.json`.

---

## ❓ Câu Hỏi Thường Gặp & Xử Lý Sự Cố

**1. Nếu tài khoản Facebook bật bảo mật 2 lớp (2FA)?**
- Lần đầu tiên chạy, trình duyệt Chrome sẽ mở lên. Nếu Facebook yêu cầu xác thực 2FA (gửi mã qua SMS/Authenticator hoặc bấm số phê duyệt trên điện thoại), bạn chỉ cần thao tác phê duyệt trên điện thoại hoặc nhập mã vào trình duyệt một lần duy nhất. Trình duyệt sẽ lưu lại session trong `chrome_profile/` cho các lần chạy sau.

**2. Gặp lỗi không kết nối được cổng Debug 9222?**
- Hãy đóng tất cả các cửa sổ Chrome đang chạy nền trước khi bật công cụ, hoặc chạy file `CHAY_DANG_BAI.bat` để script tự động khởi động phiên làm việc chuẩn.

**3. Tại sao một số nhóm báo thất bại?**
- File `logs/posting.log` sẽ ghi rõ nguyên nhân:
  - `Nhóm không tồn tại hoặc đã bị Facebook xóa`: Link nhóm bị chết hoặc nhóm riêng tư đã giải tán.
  - `Tài khoản chưa tham gia nhóm`: Công cụ đã tự động bấm gửi yêu cầu tham gia (Join request), cần chờ Admin nhóm duyệt thành viên mới có thể đăng bài.
