import json
import re
import unicodedata
from typing import Dict, List, Optional


# --- Keyword sets cho việc verify nội dung thẻ tín dụng ---
CORE_KEYWORDS = [
    "thẻ tín dụng",
    "credit card",
    "thẻ credit"
]

CONTEXT_KEYWORDS = [
    # hành vi
    "mở thẻ tín dụng", "làm thẻ tín dụng", "đăng ký thẻ tín dụng", "apply thẻ",
    "duyệt thẻ", "từ chối thẻ",
    # sử dụng
    "xài thẻ tín dụng", "dùng thẻ tín dụng", "quẹt thẻ", "cà thẻ",
    # tài chính
    "hạn mức", "limit thẻ", "dư nợ", "nợ thẻ",
    "phí thường niên", "lãi suất", "sao kê", "ngày sao kê",
    # tính năng
    "trả góp", "trả góp 0%",
    "cashback", "hoàn tiền", "tích điểm", "ưu đãi",
    # sự cố
    "bị trừ tiền", "bị charge", "fraud", "lộ thông tin thẻ",
    # online
    "add credit card", "thanh toán online"
]

NEGATIVE_KEYWORDS = [
    "thẻ atm",
    "thẻ sinh viên",
    "thẻ xe",
    "card đồ họa",
    "sim thẻ"
]

LABEL3_KEYWORDS = {
    "Financial Free": ["Financial Free"],
    "Rewards Unlimited": ["Rewards Unlimited"],
    "Cash Back": ["Cash Back"],
    "Travel Élite": ["Travel Élite", "Travel Elite"],
    "Family Link": ["Family Link"],
    "Online Plus 2in1": ["Online Plus 2in1"],
    "Premier Boundless": ["Premier Boundless"],
    "LazCard": ["LazCard", "Lazada Card", "thẻ Laz"],
    "Super Card (Thẻ trắng quyền lực)": [
        "Super Card",
        "Thẻ trắng quyền lực",
        "Thẻ trắng",
    ],
    "Thẻ thanh toán toàn cầu IDC": [
        "Thẻ thanh toán toàn cầu IDC",
        "IDC",
        "International Debit Card",
    ],
    "Thẻ nội địa Values (Thẻ ATM)": [
        "Thẻ nội địa Values",
        "Thẻ ATM",
        "thẻ nội địa",
    ],
    "iCard": ["iCard"],
    "Toss": ["Toss"],
    "TrueCard": ["TrueCard", "True card"],
    "Happy Drive": ["Happy Drive"],
    "Zero Interest": ["Zero Interest"],
    "Bill Pay": ["Bill Pay"],
    "Khác": [
        "Thẻ",
        "Thẻ tín dụng",
        "Thẻ thanh toán",
        "Thẻ VIB",
        "MasterCard",
        "Debit card",
    ],
}


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa text để so khớp:
    - lower
    - bỏ khoảng trắng thừa
    - chuẩn hóa unicode
    """
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", str(text)).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def contains_keyword(text: str, keyword: str) -> bool:
    """
    Kiểm tra keyword có xuất hiện trong text không.
    Match với word boundary để tránh false positive.
    """
    text_norm = normalize_text(text)
    kw_norm = normalize_text(keyword)

    # Regex với word boundary
    pattern = r'(?<!\w)' + re.escape(kw_norm) + r'(?!\w)'
    return re.search(pattern, text_norm) is not None


def is_credit_card_related(text: str) -> bool:
    """
    Kiểm tra xem text có liên quan đến thẻ tín dụng không.
    Sử dụng scoring system:
    - Core keywords: +2 điểm
    - Context keywords: +1 điểm
    - Negative keywords: loại trừ ngay
    - Cần tối thiểu 2 điểm để pass
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 1. Loại trừ negative keywords trước
    for neg in NEGATIVE_KEYWORDS:
        if neg in text_lower:
            return False
    
    score = 0
    
    # 2. Core keywords (quan trọng)
    for kw in CORE_KEYWORDS:
        if contains_keyword(text_lower, kw):
            score += 2
    
    # 3. Context keywords
    for kw in CONTEXT_KEYWORDS:
        if kw in text_lower:
            score += 1
    
    return score >= 2


def infer_label3(text: str, label3_keywords: Dict[str, List[str]] = None) -> Optional[str]:
    """
    Suy ra label3 từ text.
    Điều kiện:
    1. Text phải liên quan đến thẻ tín dụng/thẻ thanh toán
    2. Text phải chứa keyword của label3 cụ thể
    
    Ưu tiên:
    1. match các label cụ thể trước
    2. nếu không có thì rơi vào 'Khác' nếu có keyword generic
    """
    if label3_keywords is None:
        label3_keywords = LABEL3_KEYWORDS

    if not text:
        return None

    # Bước 1: Kiểm tra xem có liên quan đến thẻ tín dụng không
    if not is_credit_card_related(text):
        return None

    # Tách Khác ra xử lý sau cùng để tránh bắt quá rộng
    specific_items = [(k, v) for k, v in label3_keywords.items() if k != "Khác"]
    other_keywords = label3_keywords.get("Khác", [])

    # Match cụ thể trước
    for label3, keywords in specific_items:
        for kw in keywords:
            if contains_keyword(text, kw):
                return label3

    # Fallback về Khác
    for kw in other_keywords:
        if contains_keyword(text, kw):
            return "Khác"

    return None


def load_vib_label_tree(vib_json_path: str) -> List[Dict]:
    with open(vib_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_label_path_by_label3(label3: str, vib_labels: List[Dict]) -> Optional[Dict]:
    """
    Tìm node trong vib.json theo label3.
    Ưu tiên đúng nhánh:
    SẢN PHẨM/DỊCH VỤ CÁ NHÂN->THẺ TÍN DỤNG-><label3>
    """
    if not label3:
        return None

    target_suffix = f"->THẺ TÍN DỤNG->{label3}"

    # Ưu tiên đúng nhánh thẻ tín dụng
    for item in vib_labels:
        label_path = item.get("label_path", "")
        if label_path.endswith(target_suffix):
            return item

    # fallback: tìm path kết thúc bằng ->label3
    for item in vib_labels:
        label_path = item.get("label_path", "")
        if label_path.endswith(f"->{label3}"):
            return item

    return None


def parse_label_tree(label_path: str) -> Dict[str, Optional[str]]:
    """
    Parse label_path thành label1, label2, label3
    """
    if not label_path:
        return {
            "label1": None,
            "label2": None,
            "label3": None,
            "label_path_parts": [],
        }

    parts = [p.strip() for p in label_path.split("->")]

    return {
        "label1": parts[0] if len(parts) > 0 else None,
        "label2": parts[1] if len(parts) > 1 else None,
        "label3": parts[2] if len(parts) > 2 else None,
        "label_path_parts": parts,
    }


def map_text_to_vib_label_tree(
    text: str,
    vib_json_path: str = "special_data/vib.json",
    label3_keywords: Dict[str, List[str]] = None,
) -> Dict:
    """
    Hàm chính:
    - input: text
    - output: label3 suy ra + cây label từ vib
    """
    if label3_keywords is None:
        label3_keywords = LABEL3_KEYWORDS

    label3 = infer_label3(text, label3_keywords)
    vib_labels = load_vib_label_tree(vib_json_path)

    matched_item = find_label_path_by_label3(label3, vib_labels) if label3 else None

    if matched_item:
        parsed = parse_label_tree(matched_item.get("label_path", ""))
        return {
            "text": text,
            "matched_label3": label3,
            "label1": parsed["label1"],
            "label2": parsed["label2"],
            "label3": parsed["label3"],
            "label_path": matched_item.get("label_path"),
            "label_path_id": matched_item.get("label_path_id"),
            "matched": True,
        }

    return {
        "text": text,
        "matched_label3": label3,
        "label1": None,
        "label2": None,
        "label3": label3,
        "label_path": None,
        "label_path_id": None,
        "matched": False,
    }


if __name__ == "__main__":
    samples = [
        "Mình đang dùng Lazada Card của VIB thấy hoàn tiền ổn",
        "Ai review thẻ trắng quyền lực với?",
        "Mở thẻ VIB Travel Elite có lounge không?",
        "Thẻ VIB nào tốt nhỉ?",
        "Tôi muốn hỏi về International Debit Card của VIB",
    ]

    for s in samples:
        print("=" * 100)
        print(map_text_to_vib_label_tree(s))