from __future__ import annotations

import json
import re
from pathlib import Path


SOURCE_PATH = Path(r"C:\Users\Smart Laptop\Desktop\prac\dp900-questions.js")
OUTPUT_PATH = Path(r"C:\Users\Smart Laptop\Desktop\prac\dp900-questions.json")


def load_source() -> list[dict]:
    text = SOURCE_PATH.read_text(encoding="utf-8")
    payload = text.split("=", 1)[1].rsplit(";", 1)[0]
    return json.loads(payload)


def clean_text(text: str) -> str:
    replacements = [
        (r"\bSQ1\b", "SQL"),
        (r"\bstem data\b", "store data"),
        (r"\btor internet-connected\b", "for internet-connected"),
        (r"\bRSAC\b", "RBAC"),
    ]
    cleaned = text.strip()
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("Azure What", "Azure. What")
    cleaned = cleaned.replace("statement. select", "statement, select")
    cleaned = cleaned.replace("statement, select yes if he statement is true", "statement, select Yes if the statement is true")
    return cleaned.strip()


def normalize_answer_values(question: dict) -> list[str]:
    answer = str(question.get("answer", "")).strip()
    if not answer:
        return []
    if "||" in answer:
        values = [value.strip() for value in answer.split("||") if value.strip()]
    else:
        values = [answer]
    return values


def canonical_answer(question: dict) -> list[str]:
    number = question["number"]
    if number == 7:
        return ["A"]
    if number == 11:
        return ["A"]
    if number == 12:
        return ["D"]
    return normalize_answer_values(question)


def build_explanation(question: dict, status: str) -> str:
    number = question["number"]
    if status == "Incomplete":
        if question["type"] == "match":
            return "Incomplete: OCR removed the drag-and-drop prompt or exhibit details from the source PDF."
        if question["type"] == "yesno":
            return "Incomplete: OCR removed the statement rows from the source PDF."
        return "Incomplete: OCR removed part of the sentence, options, or exhibit from the source PDF."

    if number == 7:
        return (
            "Corrected to A. Microsoft Learn says read-only replicas are used to offload read workloads "
            "such as analytics and reporting from the write replica: "
            "https://learn.microsoft.com/en-us/azure/azure-sql/database/read-scale-out?view=azuresql"
        )
    if number == 11:
        return (
            "Corrected to A. Microsoft Learn documents that Azure SQL Database firewall rules control access "
            "by client IP address, so a changed external IP must be added to the allow list: "
            "https://learn.microsoft.com/en-us/azure/azure-sql/database/firewall-configure?view=azuresql"
        )
    if number == 12:
        return (
            "Corrected to D. Microsoft Learn's big data guidance treats internet-connected temperature sensor "
            "trend analysis as a time-series scenario: "
            "https://learn.microsoft.com/en-us/azure/architecture/databases/guide/big-data-architectures"
        )
    return "Answer extracted from the provided PDF."


def build_question(question: dict) -> dict:
    number = question["number"]
    qtype = question["type"]
    question_text = clean_text(question.get("questionText", ""))

    if number == 7:
        question_text = "You have a transactional application that stores data in an Azure SQL managed instance. When should you implement a read-only database replica?"
    elif number == 11:
        question_text = (
            "You have an Azure SQL database that you access directly from the internet. You recently changed your external IP address. "
            "After changing the IP address, you can no longer access the database. You can connect to other resources in Azure. "
            "What is a possible cause of the issue?"
        )
    elif number == 12:
        question_text = (
            "Your company is designing a data store for internet-connected temperature sensors. The collected data will be used to analyze temperature trends. "
            "Which type of data store should you use?"
        )

    incomplete = qtype != "mcq"

    options: list[str]
    if qtype == "yesno":
        options = ["Yes", "No"]
    elif qtype == "mcq":
        options = [clean_text(option) for option in question.get("options", [])]
    else:
        options = []

    answer_values = canonical_answer(question)

    if number == 11 and len(options) == 4:
        options = [options[0], options[1].replace("(RSAC)", "(RBAC)"), options[2], options[3]]

    if number == 7:
        answer_values = ["A"]
    elif number == 11:
        answer_values = ["A"]
    elif number == 12:
        answer_values = ["D"]

    return {
        "id": number,
        "question": question_text,
        "type": qtype,
        "options": options,
        "answer": answer_values,
        "explanation": build_explanation(question, "Incomplete" if incomplete else "Complete"),
        "status": "Incomplete" if incomplete else "Complete",
        "pageNumbers": question.get("pageNumbers", []),
    }


def main() -> None:
    source = load_source()
    output: list[dict] = []

    for question in source:
        built = build_question(question)
        output.append(built)

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    incomplete_count = sum(1 for item in output if item["status"] == "Incomplete")
    print(f"Wrote {len(output)} questions to {OUTPUT_PATH}")
    print(f"Incomplete questions: {incomplete_count}")


if __name__ == "__main__":
    main()