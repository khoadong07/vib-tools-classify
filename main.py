import json
import re
import unicodedata
from typing import Dict, List, Optional

# JSON mapping data
CARD_MAPPING = [
    {"label_vi": "Financial Free", "label_en": "Financial Free", "keywords": ["financial free"]},
    {"label_vi": "Rewards Unlimited", "label_en": "Rewards Unlimited", "keywords": ["rewards unlimited"]},
    {"label_vi": "Cash Back", "label_en": "Cash Back", "keywords": ["cash back", "cashback", "hoàn tiền"]},
    {"label_vi": "Travel Élite", "label_en": "Travel Elite", "keywords": ["travel élite", "travel elite"]},
    {"label_vi": "Family Link", "label_en": "Family Link", "keywords": ["family link"]},
    {"label_vi": "Online Plus 2in1", "label_en": "Online Plus 2in1", "keywords": ["online plus 2in1"]},
    {"label_vi": "Premier Boundless", "label_en": "Premier Boundless", "keywords": ["premier boundless"]},
    {"label_vi": "LazCard", "label_en": "LazCard", "keywords": ["lazcard", "lazada card", "thẻ laz"]},
    {"label_vi": "Super Card", "label_en": "Super Card", "keywords": ["super card", "thẻ trắng quyền lực", "thẻ trắng"]},
    {"label_vi": "Thẻ thanh toán toàn cầu IDC", "label_en": "International Debit Card", "keywords": ["thẻ thanh toán toàn cầu idc", "idc", "international debit card"]},
    {"label_vi": "Thẻ nội địa Values", "label_en": "Domestic Debit Card", "keywords": ["thẻ nội địa values", "thẻ atm", "thẻ nội địa"]},
    {"label_vi": "iCard", "label_en": "iCard", "keywords": ["icard"]},
    {"label_vi": "Toss", "label_en": "Toss", "keywords": ["toss"]},
    {"label_vi": "TrueCard", "label_en": "TrueCard", "keywords": ["truecard", "true card"]},
    {"label_vi": "Happy Drive", "label_en": "Happy Drive", "keywords": ["happy drive"]},
    {"label_vi": "Zero Interest", "label_en": "Zero Interest", "keywords": ["zero interest", "0% interest", "trả góp 0%", "lãi suất 0%"]},
    {"label_vi": "Bill Pay", "label_en": "Bill Pay", "keywords": ["bill pay", "thanh toán hóa đơn", "pay bill"]},
    {"label_vi": "Khác", "label_en": "Others", "keywords": ["thẻ", "thẻ tín dụng", "thẻ thanh toán", "thẻ vib", "mastercard", "debit card"]}
]

# Keywords để phát hiện mention về thẻ tín dụng
CREDIT_CARD_KEYWORDS = [
    "thẻ", "thẻ tín dụng", "thẻ thanh toán", "thẻ atm", "thẻ vib",
    "credit card", "debit card", "mastercard", "visa",
    "card", "lazcard", "icard", "truecard"
]


def is_credit_card_mention(text: str) -> bool:
    """
    Kiểm tra xem text có đang mention đến thẻ tín dụng không
    """
    text_lower = text.lower()
    
    for keyword in CREDIT_CARD_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    return False


def classify_card(text: str) -> dict:
    """
    Phân loại thẻ dựa trên keywords
    Trả về label và confidence score
    """
    text_lower = text.lower()
    matches = []
    
    # Tìm tất cả các matches
    for card in CARD_MAPPING:
        for keyword in card["keywords"]:
            if keyword.lower() in text_lower:
                matches.append({
                    "label_vi": card["label_vi"],
                    "label_en": card["label_en"],
                    "matched_keyword": keyword,
                    "keyword_length": len(keyword)
                })
                break  # Chỉ cần match 1 keyword là đủ
    
    if not matches:
        return None
    
    # Ưu tiên keyword dài hơn (cụ thể hơn)
    best_match = max(matches, key=lambda x: x["keyword_length"])
    
    return {
        "label_vi": best_match["label_vi"],
        "label_en": best_match["label_en"],
        "matched_keyword": best_match["matched_keyword"]
    }


def process_text(text: str) -> dict:
    """
    Xử lý text: kiểm tra mention thẻ tín dụng và phân loại
    """
    result = {
        "input_text": text,
        "is_credit_card_mention": False,
        "classification": None
    }
    
    # Bước 1: Kiểm tra có mention thẻ tín dụng không
    if is_credit_card_mention(text):
        result["is_credit_card_mention"] = True
        
        # Bước 2: Phân loại thẻ
        classification = classify_card(text)
        result["classification"] = classification
    
    return result


def load_class_labels(json_path: str = "class.json") -> list:
    """
    Load class labels từ file JSON
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_label1_label2(text: str, class_labels: list) -> dict:
    """
    Tìm label1 (cấp 3) và label2 (cấp 4) từ text dựa vào keywords trong class.json
    Trả về label1, label2 và matched keywords
    """
    text_lower = text.lower()
    matches = []
    
    for item in class_labels:
        keywords = item.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append({
                    "label1": item["label1"],
                    "label2": item["label2"],
                    "matched_keyword": keyword,
                    "keyword_length": len(keyword),
                    "definition": item.get("definition", "")
                })
                break  # Chỉ cần match 1 keyword trong mỗi item
    
    if not matches:
        return None
    
    # Ưu tiên keyword dài hơn (cụ thể hơn)
    best_match = max(matches, key=lambda x: x["keyword_length"])
    
    return {
        "label1": best_match["label1"],
        "label2": best_match["label2"],
        "matched_keyword": best_match["matched_keyword"],
        "definition": best_match["definition"]
    }


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


def process_text_full(text: str, class_labels: list, vib_json_path: str = "vib.json") -> dict:
    """
    Xử lý text đầy đủ:
    - Kiểm tra mention thẻ tín dụng
    - Phân loại loại thẻ từ vib.json
    - Tìm label1, label2 từ class.json
    
    Trả về cấu trúc:
    Labels1: THẺ TÍN DỤNG
    Labels2: Loại thẻ (từ vib.json)
    Labels3: Chủ đề (từ class.json - label1)
    Labels4: Chi tiết (từ class.json - label2)
    """
    result = {
        "input_text": text,
        "is_credit_card_mention": False,
        "Labels1": None,
        "Labels2": None,
        "Labels3": None,
        "Labels4": None,
        "matched_keywords": []
    }
    
    # Bước 1: Kiểm tra có mention thẻ tín dụng không
    if is_credit_card_mention(text):
        result["is_credit_card_mention"] = True
        result["Labels1"] = "THẺ TÍN DỤNG"
        
        # Bước 2: Phân loại loại thẻ từ vib.json
        card_classification = classify_card(text)
        if card_classification:
            result["matched_keywords"].append(card_classification["matched_keyword"])
            
            # Tìm label2 từ vib.json nếu file tồn tại
            try:
                import os
                if os.path.exists(vib_json_path):
                    with open(vib_json_path, "r", encoding="utf-8") as f:
                        vib_labels = json.load(f)
                    
                    matched_item = find_label_path_by_label3(card_classification["label_vi"], vib_labels)
                    if matched_item:
                        parsed = parse_label_tree(matched_item.get("label_path", ""))
                        result["Labels2"] = parsed["label2"]  # Loại thẻ cụ thể
                    else:
                        result["Labels2"] = card_classification["label_vi"]
                else:
                    result["Labels2"] = card_classification["label_vi"]
            except:
                result["Labels2"] = card_classification["label_vi"]
        
        # Bước 3: Tìm label1, label2 từ class.json (Labels3, Labels4)
        label_classification = find_label1_label2(text, class_labels)
        if label_classification:
            result["Labels3"] = label_classification["label1"]
            result["Labels4"] = label_classification["label2"]
            result["matched_keywords"].append(label_classification["matched_keyword"])
    
    return result


if __name__ == "__main__":
    # Load class labels
    class_labels = load_class_labels("class.json")
    
    # Test cases
    test_texts = [
        "Tôi muốn đăng ký thẻ Financial Free nhưng phí thường niên cao quá",
        "Làm sao để mở thẻ Cash Back? Điều kiện có khó không?",
        "Thẻ LazCard có ưu đãi gì không? Lãi suất thế nào?",
        "Tôi muốn mua điện thoại",  # Không mention thẻ
        "Thẻ tín dụng VIB có những loại nào?",
        "Hoàn tiền bao nhiêu khi dùng thẻ?",
        "Mở thẻ bị từ chối, không đủ điều kiện",
        "Bị spam sau khi đăng ký thẻ",
        "Thẻ thanh toán toàn cầu IDC có phí thường niên không?"
    ]
    
    print("=" * 120)
    print("CREDIT CARD FULL CLASSIFICATION SYSTEM - 4 LABELS")
    print("=" * 120)
    
    for text in test_texts:
        result = process_text_full(text, class_labels)
        print(f"\n📝 Input: {result['input_text']}")
        
        if result['is_credit_card_mention']:
            print(f"✅ Labels1: {result['Labels1']}")
            if result['Labels2']:
                print(f"✅ Labels2: {result['Labels2']}")
            if result['Labels3']:
                print(f"✅ Labels3: {result['Labels3']}")
            if result['Labels4']:
                print(f"✅ Labels4: {result['Labels4']}")
            if result['matched_keywords']:
                print(f"🔑 Matched Keywords: {', '.join(result['matched_keywords'])}")
        else:
            print("❌ Không mention thẻ tín dụng")
        
        print("-" * 120)
