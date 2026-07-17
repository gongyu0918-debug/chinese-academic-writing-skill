#!/usr/bin/env python3
"""Read-only whole-manuscript consistency candidate audit.

The scanner never rewrites inputs. Duplicate prose, term variants, and
abbreviation findings require contextual review; only broken LaTeX label/ref
structure is treated as a high-severity structural finding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass

sys.dont_write_bytecode = True

from prose_lint import InputReadError, read_text


LATEX_LABEL = re.compile(r"\\label\{([^{}\n]+)\}")
LATEX_REF = re.compile(r"\\(?:ref|pageref|nameref|autoref|eqref|cref|Cref|vref|Vref)\{([^{}\n]+)\}")
HEADING = re.compile(r"^\s*#{1,6}\s+")
TABLE_ROW = re.compile(r"^\s*\|")
LATEX_CONTROL_LINE = re.compile(r"^\s*\\(?:label|ref|pageref|nameref|autoref|eqref|cref|Cref|vref|Vref)\{[^{}\n]+\}\s*$")
FENCED_CODE = re.compile(r"(?ms)^\s*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^\s*(?P=fence)\s*$")
LATEX_CODE_ENV = re.compile(r"(?s)\\begin\{(?:verbatim|Verbatim|lstlisting|minted|comment)\}.*?\\end\{(?:verbatim|Verbatim|lstlisting|minted|comment)\}")
INLINE_CODE = re.compile(r"`+[^`\n]*`+")
LATEX_COMMENT = re.compile(r"(?m)(?<!\\)%[^\n]*$")


@dataclass(frozen=True)
class Location:
    path: str
    line: int


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    category: str
    code: str
    detail: str
    excerpt: str


def normalize_prose(text: str) -> str:
    return re.sub(r"\s+", "", text).strip()


def paragraphs(text: str) -> list[tuple[int, str]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    rows: list[tuple[int, str]] = []
    start_line = 1
    buffer: list[str] = []
    for line_no, line in enumerate(normalized.split("\n"), start=1):
        if HEADING.match(line) or TABLE_ROW.match(line) or LATEX_CONTROL_LINE.match(line):
            if buffer:
                rows.append((start_line, "\n".join(buffer).strip()))
                buffer = []
            start_line = line_no + 1
            continue
        if not line.strip():
            if buffer:
                rows.append((start_line, "\n".join(buffer).strip()))
                buffer = []
            start_line = line_no + 1
            continue
        if not buffer:
            start_line = line_no
        buffer.append(line)
    if buffer:
        rows.append((start_line, "\n".join(buffer).strip()))
    return rows


def locations(
    pattern: re.Pattern[str],
    path: str,
    text: str,
    *,
    split_commas: bool = False,
) -> dict[str, list[Location]]:
    result: dict[str, list[Location]] = defaultdict(list)
    for match in pattern.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        values = match.group(1).split(",") if split_commas else (match.group(1),)
        for value in values:
            cleaned = value.strip()
            if cleaned:
                result[cleaned].append(Location(path, line))
    return result


def mask_preserving_newlines(text: str, pattern: re.Pattern[str]) -> str:
    return pattern.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def latex_scan_text(text: str) -> str:
    masked = text
    for pattern in (FENCED_CODE, LATEX_CODE_ENV, INLINE_CODE, LATEX_COMMENT):
        masked = mask_preserving_newlines(masked, pattern)
    return masked


def parse_term_group(value: str) -> tuple[str, ...]:
    terms = tuple(dict.fromkeys(part.strip() for part in value.split("|") if part.strip()))
    if len(terms) < 2:
        raise argparse.ArgumentTypeError("--term-group needs at least two terms separated by |")
    return terms


def find_term_group_locations(
    documents: list[tuple[str, str]], group: tuple[str, ...]
) -> dict[str, list[Location]]:
    result: dict[str, list[Location]] = defaultdict(list)
    for path, text in documents:
        candidates: list[tuple[int, int, str]] = []
        for term in group:
            candidates.extend(
                (match.start(), match.end(), term)
                for match in re.finditer(re.escape(term), text)
            )
        chosen: list[tuple[int, int]] = []
        for start, end, term in sorted(candidates, key=lambda item: (item[0], -(item[1] - item[0]))):
            if any(start < used_end and end > used_start for used_start, used_end in chosen):
                continue
            chosen.append((start, end))
            result[term].append(Location(path, text.count("\n", 0, start) + 1))
    return result


def analyze(
    documents: list[tuple[str, str]],
    *,
    term_groups: list[tuple[str, ...]] | None = None,
    abbreviations: list[str] | None = None,
    minimum_duplicate_chars: int = 80,
) -> dict:
    findings: list[Finding] = []
    duplicate_index: dict[str, tuple[Location, str]] = {}
    labels: dict[str, list[Location]] = defaultdict(list)
    refs: dict[str, list[Location]] = defaultdict(list)

    for path, text in documents:
        for line_no, paragraph in paragraphs(text):
            key = normalize_prose(paragraph)
            if len(key) < minimum_duplicate_chars:
                continue
            first = duplicate_index.get(key)
            if first is None:
                duplicate_index[key] = (Location(path, line_no), paragraph)
                continue
            first_location, _ = first
            findings.append(
                Finding(
                    path,
                    line_no,
                    "medium",
                    "cross-file-prose",
                    "duplicate-paragraph-candidate",
                    f"与 {first_location.path}:{first_location.line} 的长段完全重复，请核对是否为必要复现",
                    paragraph.replace("\n", " ")[:120],
                )
            )
        scan_text = latex_scan_text(text)
        for label, rows in locations(LATEX_LABEL, path, scan_text).items():
            labels[label].extend(rows)
        for label, rows in locations(LATEX_REF, path, scan_text, split_commas=True).items():
            refs[label].extend(rows)

    for label, rows in labels.items():
        if len(rows) > 1:
            for row in rows[1:]:
                findings.append(
                    Finding(
                        row.path,
                        row.line,
                        "high",
                        "cross-reference",
                        "duplicate-latex-label",
                        f"LaTeX 标签 {label!r} 重复；首次位于 {rows[0].path}:{rows[0].line}",
                        label,
                    )
                )
    for label, rows in refs.items():
        if label not in labels:
            for row in rows:
                findings.append(
                    Finding(
                        row.path,
                        row.line,
                        "high",
                        "cross-reference",
                        "missing-latex-label",
                        f"引用的 LaTeX 标签 {label!r} 在已扫描文件中不存在",
                        label,
                    )
                )

    for group in term_groups or []:
        seen = find_term_group_locations(documents, group)
        if len(seen) > 1:
            canonical = group[0]
            summary = "，".join(f"{term}({len(rows)})" for term, rows in seen.items())
            first_term = next(term for term in group if term in seen)
            first = seen[first_term][0]
            findings.append(
                Finding(
                    first.path,
                    first.line,
                    "medium",
                    "terminology",
                    "term-variant-group",
                    f"同组术语同时出现：{summary}；请结合状态包确认规范形式 {canonical!r} 及允许变体",
                    " | ".join(group),
                )
            )

    for abbreviation in dict.fromkeys(abbreviations or []):
        token = re.compile(rf"(?<![A-Za-z0-9]){re.escape(abbreviation)}(?![A-Za-z0-9])")
        definition = re.compile(rf"[（(]\s*{re.escape(abbreviation)}\s*[）)]")
        occurrences: list[tuple[int, int, Location]] = []
        definitions: list[tuple[int, int, Location]] = []
        for document_index, (path, text) in enumerate(documents):
            for match in token.finditer(text):
                occurrences.append((document_index, match.start(), Location(path, text.count("\n", 0, match.start()) + 1)))
            for match in definition.finditer(text):
                definitions.append((document_index, match.start(), Location(path, text.count("\n", 0, match.start()) + 1)))
        if not occurrences:
            continue
        if not definitions:
            first = min(occurrences, key=lambda row: (row[0], row[1]))[2]
            findings.append(
                Finding(first.path, first.line, "medium", "abbreviation", "undefined-abbreviation-candidate", f"指定缩写 {abbreviation!r} 已使用，但已扫描文本中未找到括号定义", abbreviation)
            )
            continue
        first_use_row = min(occurrences, key=lambda row: (row[0], row[1]))
        first_definition_row = min(definitions, key=lambda row: (row[0], row[1]))
        if first_use_row[:2] < first_definition_row[:2]:
            first_use = first_use_row[2]
            first_definition = first_definition_row[2]
            findings.append(
                Finding(first_use.path, first_use.line, "medium", "abbreviation", "abbreviation-before-definition-candidate", f"指定缩写 {abbreviation!r} 在 {first_definition.path}:{first_definition.line} 定义前已经使用", abbreviation)
            )

    return {
        "summary": {
            "documents": len(documents),
            "term_groups": len(term_groups or []),
            "abbreviations": len(abbreviations or []),
            "findings": len(findings),
        },
        "findings": [asdict(item) for item in findings],
    }


def print_text_report(report: dict) -> None:
    summary = report["summary"]
    print(f"DOCUMENTS={summary['documents']} FINDINGS={summary['findings']}")
    print("NOTE=All prose, terminology, and abbreviation findings are review candidates; files are never rewritten.")
    for finding in report["findings"]:
        print(f"{finding['path']}:{finding['line']}: {finding['severity']}: {finding['code']}: {finding['detail']}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Read-only multi-file manuscript consistency candidate audit; never rewrites files.")
    parser.add_argument("files", nargs="+", help="Text/Markdown/LaTeX/DOCX files, or '-' for stdin.")
    parser.add_argument("--term-group", action="append", type=parse_term_group, default=[], help="Terms separated by |; first term is the expected canonical form from the project state.")
    parser.add_argument("--abbreviation", action="append", default=[], help="Explicit abbreviation to check for definition order; repeat as needed.")
    parser.add_argument("--minimum-duplicate-chars", type=int, default=80)
    parser.add_argument("--encoding", help="Encoding for plain-text inputs.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return 1 only for high LaTeX cross-reference structure findings; never rewrites.")
    args = parser.parse_args(argv)
    if args.minimum_duplicate_chars < 20:
        parser.error("--minimum-duplicate-chars must be at least 20")

    documents: list[tuple[str, str]] = []
    read_error = False
    for file_arg in args.files:
        try:
            path_label, content = read_text(file_arg, args.encoding)
        except InputReadError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            read_error = True
            continue
        documents.append((path_label, content))

    report = analyze(
        documents,
        term_groups=args.term_group,
        abbreviations=args.abbreviation,
        minimum_duplicate_chars=args.minimum_duplicate_chars,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    if read_error:
        return 2
    if args.strict and any(item["severity"] == "high" for item in report["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
