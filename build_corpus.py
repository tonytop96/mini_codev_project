from bs4 import BeautifulSoup
import json
import os
import re

BASE_DIR = r"C:\CODEV202303\help"

TARGET_FOLDERS = [
    "macroplus", "lens_system", "diagnostic", "geometric",
    "diffraction", "optimization", "tolerancing", "specbuilder",
    "sysanalysis", "setup", "api", "beam", "fab", "lens_data",
    "multilayer", "troubleshooting",
]

SKIP_PREFIX = ("HIDD", "HIDC", "IDX", "TOC")
MIN_CHARS = 100
MAX_CHARS = 2000
OUTPUT_FILE = r"d:\05_Claude Project\mini_codev_project\corpus.json"


def clean_text(text):
    text = re.sub(r"\xa0", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_paragraphs(text, max_chars=MAX_CHARS):
    if len(text) <= max_chars:
        return [text]

    # 1차: 문장 경계로 분할
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    chunks, buf = [], ""
    for part in parts:
        if len(buf) + len(part) + 1 > max_chars and buf:
            chunks.append(buf.strip())
            buf = part
        else:
            buf = (buf + " " + part).strip() if buf else part
    if buf:
        chunks.append(buf.strip())

    # 2차: 여전히 초과하는 청크는 하드 컷
    final = []
    for chunk in (chunks if chunks else [text]):
        while len(chunk) > max_chars:
            final.append(chunk[:max_chars])
            chunk = chunk[max_chars:]
        if chunk:
            final.append(chunk)
    return final


def extract_page(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except Exception:
        return None, None

    title = soup.title.get_text(strip=True) if soup.title else ""
    title = clean_text(title)

    div = soup.find(id="page_content")
    if not div:
        return title, None

    text = clean_text(div.get_text(separator=" ", strip=True))
    if len(text) < MIN_CHARS:
        return title, None

    return title, text


def build():
    chunks = []
    chunk_id = 0
    skipped = 0

    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)
        if not os.path.exists(folder_path):
            print(f"  [SKIP] folder not found: {folder}")
            continue

        files = sorted(f for f in os.listdir(folder_path) if f.endswith(".html"))
        folder_chunks = 0

        for fname in files:
            if fname.startswith(SKIP_PREFIX):
                skipped += 1
                continue

            title, text = extract_page(os.path.join(folder_path, fname))
            if not text:
                skipped += 1
                continue

            parts = split_paragraphs(text)
            for i, part in enumerate(parts):
                chunk_title = title if len(parts) == 1 else f"{title} ({i+1})"
                chunks.append({
                    "id": chunk_id,
                    "folder": folder,
                    "filename": fname,
                    "title": chunk_title,
                    "text": part,
                    "char_count": len(part),
                })
                chunk_id += 1
                folder_chunks += 1

        print(f"  {folder:20} : {folder_chunks:4} chunks")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\nTotal chunks : {len(chunks)}")
    print(f"Skipped files: {skipped}")
    print(f"Saved to     : {OUTPUT_FILE}")

    # 검증: THC 시나리오 페이지 포함 확인
    thc_found = any("Opt_2_VariablesCC" in c["filename"] for c in chunks)
    max_chars = max(c["char_count"] for c in chunks)
    print(f"\nValidation:")
    print(f"  Opt_2_VariablesCC page found : {thc_found}")
    print(f"  Max chunk size               : {max_chars} chars (limit: {MAX_CHARS})")


if __name__ == "__main__":
    print("Building corpus...\n")
    build()
