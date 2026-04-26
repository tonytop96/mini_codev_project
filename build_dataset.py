import os
import json
import re
from bs4 import BeautifulSoup

# ==============================
# 경로 설정 (수정 필요)
# ==============================
BASE_DIR = r"C:\CODEV202303\help"

TARGET_FOLDERS = [
    "macroplus",
    "lens_system",
    "diagnostic",
    "geometric",
    "diffraction",
    "optimization",
    "tolerancing",
    "specbuilder",
    "sysanalysis",
    "setup",
]

OUTPUT_FILE = "commands.json"

# ==============================
# 필터 조건
# ==============================
SKIP_PREFIX = ("HIDD", "HIDC", "IDX", "TOC")

MIN_TEXT_LENGTH = 100

# ==============================
# 텍스트 정리
# ==============================
def clean_text(text):
    text = re.sub(r"\xa0", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ==============================
# command 이름 추출
# ==============================
def extract_command_name(filename):
    return filename.replace(".html", "").upper()

# ==============================
# HTML 내용 추출
# ==============================
def extract_content(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        content_div = soup.find(id="page_content")

        if not content_div:
            return None

        text = clean_text(content_div.get_text(" ", strip=True))

        if len(text) < MIN_TEXT_LENGTH:
            return None

        return text

    except Exception as e:
        return None

# ==============================
# example 추출
# ==============================
def extract_example(text, command):
    cmd_lower = command.lower()

    # 1. "in COMMAND arg ..." — command 이름이 반드시 포함되어야 함
    m = re.search(
        rf"(in\s+{re.escape(cmd_lower)}(?:\s+[\w\[\]'\.\/\-]+){{1,8}})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # 2. "$COMMAND arg ..." 단축 별칭
    m = re.search(
        rf"(\${re.escape(cmd_lower)}(?:\s+[\w\[\]'\.\/\-]+){{1,8}})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # 3. "Example:" / "e.g." 다음 텍스트
    m = re.search(r"(?:example|e\.g\.)[:\s]+([^\n\.]{10,100})", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return ""

# ==============================
# main process
# ==============================
def process():
    results = []
    seen = set()

    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)

        if not os.path.exists(folder_path):
            continue

        for file in os.listdir(folder_path):
            if not file.endswith(".html"):
                continue

            # 🔥 노이즈 제거
            if file.startswith(SKIP_PREFIX):
                continue

            command = extract_command_name(file)

            # 🔥 command 형식 필터
            if not re.match(r"^[A-Z0-9_]{3,12}$", command):
                continue

            # 🔥 중복 제거
            if command in seen:
                continue
            seen.add(command)

            filepath = os.path.join(folder_path, file)

            text = extract_content(filepath)
            if not text:
                continue

            example = extract_example(text, command)

            results.append({
                "command": command,
                "description": text[:1000],  # 너무 길면 자름
                "example": example,
                "source": file
            })

    print(f"Extracted {len(results)} clean commands")

    # 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

# ==============================
# 실행
# ==============================
if __name__ == "__main__":
    process()