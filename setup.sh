#!/bin/bash

echo "🚀 Cài đặt VIB Credit Card Classifier..."

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt"
    exit 1
fi

echo "✅ Python3 đã được cài đặt"

# Tạo virtual environment nếu chưa có
if [ ! -d ".venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv .venv
fi

# Kích hoạt virtual environment
echo "🔧 Kích hoạt virtual environment..."
source .venv/bin/activate

# Cài đặt dependencies
echo "📥 Cài đặt các thư viện cần thiết..."
pip install -r requirements.txt

echo "✅ Cài đặt hoàn tất!"
echo ""
echo "Để chạy ứng dụng:"
echo "  source .venv/bin/activate"
echo "  streamlit run app.py"
