import shutil
import random
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageEnhance

class ImageMutator:
    """
    Hệ thống chống quét trùng lặp ảnh chuyên sâu (Anti-Perceptual Hash / Anti-PhotoDNA):
    1. Xóa sạch toàn bộ siêu dữ liệu EXIF/Metadata cũ.
    2. Cắt viền vi mô (Micro-Crop 1-3px) để dịch chuyển lưới khối JPEG DCT (phá pHash/dHash).
    3. Biến thiên nhẹ độ sáng, độ tương phản và độ bão hòa màu (±1%).
    4. Rải hạt vi mô ngẫu nhiên (Micro-Noise) mắt thường không thể nhận ra.
    5. Đổi tên file tải lên giống hệt ảnh chụp từ iPhone/Samsung thực tế (IMG_YYYYMMDD_HHMMSS.jpg).
    """

    def __init__(self, temp_dir: str = ".temp_mutated_images"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def clean_temp(self):
        """Dọn dẹp thư mục ảnh tạm"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_realistic_filename() -> str:
        """Tạo tên file giống ảnh chụp từ điện thoại hoặc máy ảnh thật"""
        now_str = datetime.now().strftime("%Y%m%d")
        rand_time = f"{random.randint(8, 22):02d}{random.randint(0, 59):02d}{random.randint(0, 59):02d}"
        rand_num = random.randint(1000, 9999)
        patterns = [
            f"IMG_{now_str}_{rand_time}.jpg",
            f"IMG_{rand_num}.jpg",
            f"PXL_{now_str}_{rand_time}000.jpg",
            f"DSC_{rand_num}.jpg",
            f"{now_str}_{rand_time}.jpg"
        ]
        return random.choice(patterns)

    def mutate_image(self, image_path: str) -> str:
        """Tạo bản sao ảnh độc nhất 100% cả về MD5 lẫn Perceptual Hash"""
        img_path = Path(image_path)
        if not img_path.exists():
            return image_path

        try:
            with Image.open(img_path) as img:
                # Chuyển sang RGB thuần (loại bỏ kênh Alpha và toàn bộ EXIF gốc)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                else:
                    img = img.copy()

                width, height = img.size

                # 1. Micro-Crop (Cắt nhẹ 1-3 pixel ở các cạnh để đổi kích thước & dịch lưới điểm ảnh)
                if width > 50 and height > 50:
                    left = random.randint(1, 3)
                    top = random.randint(1, 3)
                    right = width - random.randint(1, 3)
                    bottom = height - random.randint(1, 3)
                    img = img.crop((left, top, right, bottom))
                    width, height = img.size

                # 2. Biến thiên nhẹ Độ sáng + Độ tương phản + Màu sắc (Mắt thường không phân biệt được)
                img = ImageEnhance.Brightness(img).enhance(random.uniform(0.988, 1.012))
                img = ImageEnhance.Contrast(img).enhance(random.uniform(0.990, 1.010))
                img = ImageEnhance.Color(img).enhance(random.uniform(0.990, 1.010))

                # 3. Rải 20-35 điểm nhiễu vi mô (Micro-Noise) ngẫu nhiên khắp ảnh
                if width > 10 and height > 10:
                    num_pixels = random.randint(20, 35)
                    for _ in range(num_pixels):
                        px = random.randint(0, width - 1)
                        py = random.randint(0, height - 1)
                        r, g, b = img.getpixel((px, py))[:3]
                        nr = min(255, max(0, r + random.choice([-2, -1, 1, 2])))
                        ng = min(255, max(0, g + random.choice([-2, -1, 1, 2])))
                        nb = min(255, max(0, b + random.choice([-2, -1, 1, 2])))
                        img.putpixel((px, py), (nr, ng, nb))

                # 4. Lưu với tên file tự nhiên như chụp từ điện thoại
                dest_filename = self._generate_realistic_filename()
                dest_path = self.temp_dir / dest_filename
                # Đảm bảo không trùng tên nếu có nhiều ảnh trong cùng 1 bài
                while dest_path.exists():
                    dest_filename = self._generate_realistic_filename()
                    dest_path = self.temp_dir / dest_filename

                quality = random.randint(92, 97)
                img.save(dest_path, format="JPEG", quality=quality, optimize=True)
                return str(dest_path.resolve())

        except Exception as e:
            print(f"[Cảnh báo] Không thể biến đổi ảnh {img_path.name}: {e}. Dùng ảnh gốc.")
            return str(img_path.resolve())

    def prepare_images(self, image_paths: list[str], mutate: bool = True) -> list[str]:
        """Chuẩn bị danh sách ảnh sẵn sàng để đăng"""
        if not mutate:
            return [str(Path(p).resolve()) for p in image_paths if Path(p).exists()]

        processed = []
        for path in image_paths:
            processed.append(self.mutate_image(path))
        return processed
