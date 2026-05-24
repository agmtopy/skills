#!/usr/bin/env python3
"""PDF 转 TXT — 提取 PDF 全文为纯文本。

用法:
    python pdf2txt.py <input.pdf> <output.txt>
"""

import sys
import fitz  # PyMuPDF


def pdf_to_text(pdf_path: str, txt_path: str):
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text.strip())
    doc.close()

    content = "\n\n".join(pages)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"提取 {len(pages)} 页，共 {len(content)} 字")
    print(f"保存到: {txt_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pdf2txt.py <input.pdf> [output.txt]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    txt_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.rsplit(".", 1)[0] + ".txt"
    pdf_to_text(pdf_path, txt_path)
