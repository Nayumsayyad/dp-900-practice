from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path(r"C:\Users\Smart Laptop\Desktop\prac\DP-900.pdf")
OUTPUT_PATH = Path(r"C:\Users\Smart Laptop\Desktop\prac\dp900-questions.js")


def classify_question(block: str) -> str:
    lower = block.lower()
    if "select yes if the statement is true" in lower:
        return "yesno"
    if "match the" in lower or "drag the appropriate" in lower:
        return "match"
    if re.search(r"\n\s*[A-F]\. ", block):
        return "mcq"
    return "dropdown"


def parse_question_block(number: int, block: str) -> dict:
    block = block.replace("\r", "")
    block = re.sub(
        r"Dumps Q&A Microsoft - DP-900\s*Success Guaranteed, 100% Valid\s*\d+ of 76",
        "",
        block,
        flags=re.S,
    )
    block = re.sub(r"\n{3,}", "\n\n", block).strip()
    qtype = classify_question(block)

    raw_lines = [line.strip() for line in block.splitlines() if line.strip()]
    question_lines: list[str] = []
    options: list[str] = []
    current_option: str | None = None
    in_options = False
    answer = ""

    for index, line in enumerate(raw_lines):
        if line.lower().startswith("answer:"):
            answer = line.split(":", 1)[1].strip()
            if not answer and index + 1 < len(raw_lines):
                answer = raw_lines[index + 1].strip()
            break

        if qtype == "mcq" and re.match(r"^[A-F]\.\s*", line):
            in_options = True
            if current_option:
                options.append(current_option.strip())
            current_option = re.sub(r"^[A-F]\.\s*", "", line).strip()
            continue

        if qtype == "mcq" and in_options and current_option is not None:
            current_option += " " + line
            continue

        question_lines.append(line)

    if current_option:
        options.append(current_option.strip())

    question_text = " ".join(question_lines)
    question_text = re.sub(r"^Question #:\d+\s*", "", question_text)
    question_text = re.sub(r"\s+", " ", question_text).strip()

    page_numbers = sorted({int(value) for value in re.findall(r"(\d+) of 76", block)})

    normalized_answer = answer.strip()
    normalized_answer = re.sub(r"^Answer(?:\s*\([^)]*\))?\s*:\s*", "", normalized_answer, flags=re.I)
    normalized_answer = normalized_answer.strip()

    if qtype in {"dropdown", "mcq", "match", "yesno"} and "||" in normalized_answer:
        normalized_answer_values = [value.strip() for value in normalized_answer.split("||") if value.strip()]
    elif qtype == "mcq":
        normalized_answer_values = [value.strip() for value in re.split(r"\s+", normalized_answer) if value.strip()]
    else:
        normalized_answer_values = [normalized_answer] if normalized_answer else []

    return {
        "number": number,
        "type": qtype,
        "questionText": question_text,
        "options": options,
        "answer": normalized_answer,
        "answerValues": normalized_answer_values,
        "pageNumbers": page_numbers,
        "raw": block,
    }


def main() -> None:
    reader = PdfReader(str(PDF_PATH))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    matches = list(re.finditer(r"Question #:(\d+)", text))

    items = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        items.append(parse_question_block(number, text[start:end]))

    OUTPUT_PATH.write_text(
        "window.dp900Questions = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(items)} questions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()