import re
import random
import string

class SpintaxEngine:
    """
    Xử lý trộn nội dung văn bản theo cú pháp Spintax: {tùy chọn 1|tùy chọn 2|tùy chọn 3}
    Kết hợp kỹ thuật chèn ký tự vô hình (Zero-Width) và biến đổi vi mô để phá bộ lọc SimHash của Facebook.
    """

    # Các ký tự khoảng trắng vô hình (mắt thường không thấy nhưng làm thay đổi hoàn toàn mã Hash văn bản)
    ZERO_WIDTH_CHARS = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\ufeff",  # Zero-width no-break space
    ]

    @staticmethod
    def spin(text: str) -> str:
        """Giải mã cú pháp spintax {A|B|C} (hỗ trợ cả lồng nhau)"""
        pattern = re.compile(r'\{([^{}]+)\}')
        while True:
            match = pattern.search(text)
            if not match:
                break
            options = match.group(1).split('|')
            chosen = random.choice(options)
            text = text[:match.start()] + chosen + text[match.end():]
        return text

    @classmethod
    def inject_invisible_salt(cls, text: str) -> str:
        """
        Chèn ngẫu nhiên các ký tự vô hình (Zero-Width) vào giữa một số khoảng trắng trong bài.
        Mắt người đọc hoàn toàn bình thường, nhưng thuật toán chống Spam của Facebook sẽ thấy
        mỗi bài viết có cấu trúc chuỗi byte khác nhau 100%.
        """
        words = text.split(" ")
        if len(words) < 4:
            return text

        salted_words = []
        for word in words:
            salted_words.append(word)
            # Cứ khoảng 25% từ sẽ được gắn thêm 1 ký tự vô hình ở cuối
            if random.random() < 0.25:
                salted_words[-1] += random.choice(cls.ZERO_WIDTH_CHARS)

        return " ".join(salted_words)

    @staticmethod
    def generate_random_signature() -> str:
        """Tạo mã định danh ngẫu nhiên ngắn hoặc cụm icon tự nhiên ở cuối bài"""
        icons = ["🌿", "⭐", "✨", "📌", "💎", "🍀", "🌸", "☕", "🔥", "🚀", "🎯", "💡", "🌈", "🌻"]
        random_icons = "".join(random.sample(icons, random.randint(2, 3)))
        random_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        templates = [
            f"\n\n{random_icons} [Mã: #{random_code}]",
            f"\n\n{random_icons} (Ref: {random_code})",
            f"\n\n{random_icons} #{random_code}",
        ]
        return random.choice(templates)

    @classmethod
    def process_content(
        cls,
        raw_text: str,
        use_spintax: bool = True,
        append_signature: bool = True,
        inject_zero_width: bool = True
    ) -> str:
        """Xử lý toàn bộ nội dung bài viết để đạt độ độc nhất 100%"""
        text = raw_text
        if use_spintax:
            text = cls.spin(text)
        if inject_zero_width:
            text = cls.inject_invisible_salt(text)
        if append_signature:
            text += cls.generate_random_signature()
        return text.strip()


if __name__ == "__main__":
    sample = "{Chào bạn|Xin chào cả nhà|Hello anh em}! {Hôm nay đẹp trời|Chúc một ngày tốt lành}."
    for i in range(3):
        print(f"Lần {i+1}:", SpintaxEngine.process_content(sample, True, True, True))
