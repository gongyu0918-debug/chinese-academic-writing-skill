#!/usr/bin/env python3
"""Read-only citation coverage and numeric-reference structure audit.

The scanner reports candidates. It never inserts, replaces, or rewrites a
citation. Semantic support, source authority, and institutional requirements
remain human/model review tasks after reading the cited source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass

from prose_lint import InputReadError, read_text


REFERENCE_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:参考文献|主要参考文献|references|bibliography)\s*[:：]?\s*$",
    re.IGNORECASE,
)
NUMERIC_CITATION = re.compile(
    r"\[((?:\d+\s*(?:[-–—]\s*\d+)?\s*[,，;；]?\s*)+)\](?!\()"
)
NUMERIC_REFERENCE = re.compile(r"^\s*\[(\d+)\]\s*(.+?)\s*$")
AUTHOR_YEAR = re.compile(
    r"[（(](?=[^()（）\n]{0,70}(?:19|20)\d{2}[a-z]?)[^()（）\n]{1,90}[）)]"
)
LATEX_CITATION = re.compile(r"\\cite\w*\{[^{}\n]+\}")
DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
SENTENCE = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?", re.MULTILINE)
OWN_STUDY = re.compile(r"^\s*(?:本研究|本文|本项目|笔者|我们)(?:的|在|通过|采用|发现|结果|认为|提出|分析|考察|讨论)")
EXTERNAL_ATTRIBUTION = re.compile(
    r"(?:已有|既有|相关|国内外)?(?:研究|文献|学者|报告|调查|标准|规范|政策|指南|统计)(?:表明|显示|指出|认为|发现|证实|规定|要求|提出|认为)|"
    r"(?:根据|依据|按照)[^。！？!?；;]{0,24}(?:研究|报告|调查|标准|规范|政策|指南|统计)"
)
HIGH_RISK = re.compile(
    r"(?:\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|人|项|篇|年|个月|天)|"
    r"导致|造成|促使|促进|提高|提升|降低|减少|优于|高于|低于|显著|相关性|因果|"
    r"首次|填补[^。！？!?；;]{0,12}空白|尚无研究|缺乏研究|普遍认为|一致认为)"
)
GENERAL_CLAIM = re.compile(
    r"(?:表明|显示|说明|证实|发现|通常|往往|普遍|主要|核心|关键|有助于|影响|"
    r"可分为|是指|定义为|包括|集中于|呈现|形成|构成)"
)


@dataclass(frozen=True)
class Finding:
    line: int
    severity: str
    category: str
    code: str
    detail: str
    excerpt: str


def split_document(text: str) -> tuple[str, str, int | None]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for index, line in enumerate(lines):
        if REFERENCE_HEADING.match(line):
            return "\n".join(lines[:index]), "\n".join(lines[index + 1 :]), index + 1
    return "\n".join(lines), "", None


def expand_numeric_group(group: str) -> list[int]:
    result: list[int] = []
    for part in re.split(r"[,，;；]", group):
        token = part.strip()
        if not token:
            continue
        range_match = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", token)
        if range_match:
            start, end = (int(value) for value in range_match.groups())
            if start <= end and end - start <= 200:
                result.extend(range(start, end + 1))
            continue
        if token.isdigit():
            result.append(int(token))
    return result


def numeric_citations(text: str) -> list[int]:
    values: list[int] = []
    for match in NUMERIC_CITATION.finditer(text):
        values.extend(expand_numeric_group(match.group(1)))
    return values


def citation_schemes(text: str) -> set[str]:
    schemes: set[str] = set()
    if NUMERIC_CITATION.search(text):
        schemes.add("numeric")
    if AUTHOR_YEAR.search(text):
        schemes.add("author-year")
    if LATEX_CITATION.search(text):
        schemes.add("latex")
    return schemes


def reference_entries(text: str, heading_line: int | None) -> tuple[dict[int, tuple[int, str]], list[Finding]]:
    entries: dict[int, tuple[int, str]] = {}
    findings: list[Finding] = []
    offset = heading_line or 0
    for index, line in enumerate(text.splitlines(), start=offset + 1):
        match = NUMERIC_REFERENCE.match(line)
        if not match:
            continue
        identifier = int(match.group(1))
        if identifier in entries:
            findings.append(Finding(index, "high", "reference-structure", "duplicate-reference-id", f"参考文献编号 [{identifier}] 重复", line.strip()[:100]))
            continue
        entries[identifier] = (index, match.group(2))

    doi_rows: dict[str, list[tuple[int, int]]] = {}
    for identifier, (line_no, content) in entries.items():
        for match in DOI.finditer(content):
            doi = match.group(0).rstrip(".,;:，。；：)]}>").lower()
            doi_rows.setdefault(doi, []).append((identifier, line_no))
    for doi, rows in doi_rows.items():
        if len(rows) > 1:
            identifiers = ", ".join(f"[{identifier}]" for identifier, _ in rows)
            findings.append(Finding(rows[0][1], "high", "reference-structure", "duplicate-doi", f"DOI {doi} 出现在 {identifiers}", doi))
    return entries, findings


def sentence_rows(body: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        for match in SENTENCE.finditer(line):
            sentence = match.group(0).strip()
            if len(re.sub(r"\s+", "", sentence)) >= 8:
                rows.append((line_no, sentence))
    return rows


def is_claim_candidate(sentence: str, mode: str) -> bool:
    visible = NUMERIC_CITATION.sub("", LATEX_CITATION.sub("", sentence))
    visible = AUTHOR_YEAR.sub("", visible).strip()
    if OWN_STUDY.match(visible) and not EXTERNAL_ATTRIBUTION.search(visible):
        return False
    if EXTERNAL_ATTRIBUTION.search(visible) or HIGH_RISK.search(visible):
        return True
    if mode == "literature-review" and GENERAL_CLAIM.search(visible):
        return True
    return bool((NUMERIC_CITATION.search(sentence) or AUTHOR_YEAR.search(sentence) or LATEX_CITATION.search(sentence)) and GENERAL_CLAIM.search(visible))


def analyze(text: str, *, mode: str = "general", minimum_coverage: float | None = None) -> dict:
    body, references, heading_line = split_document(text)
    used = numeric_citations(body)
    entries, findings = reference_entries(references, heading_line)
    schemes = citation_schemes(body)

    for identifier in sorted(set(used) - set(entries)):
        findings.append(Finding(1, "high", "citation-mapping", "missing-reference-entry", f"正文使用 [{identifier}]，文后未找到对应编号条目", f"[{identifier}]"))
    for identifier in sorted(set(entries) - set(used)):
        line_no, content = entries[identifier]
        findings.append(Finding(line_no, "low", "citation-mapping", "unused-reference-entry", f"文后条目 [{identifier}] 未在正文编号引文中使用", content[:100]))

    candidates: list[tuple[int, str, bool]] = []
    for line_no, sentence in sentence_rows(body):
        if not is_claim_candidate(sentence, mode):
            continue
        cited = bool(NUMERIC_CITATION.search(sentence) or AUTHOR_YEAR.search(sentence) or LATEX_CITATION.search(sentence))
        candidates.append((line_no, sentence, cited))
        if not cited:
            findings.append(Finding(line_no, "medium", "claim-coverage", "uncited-claim-candidate", "该论断可能需要来源支持，请结合研究语境人工判断", sentence[:100]))

    cited_candidates = sum(1 for _, _, cited in candidates if cited)
    coverage = cited_candidates / len(candidates) if candidates else None
    if minimum_coverage is not None and coverage is not None and coverage < minimum_coverage:
        findings.append(Finding(1, "high", "claim-coverage", "below-explicit-minimum", f"候选论断覆盖率 {coverage:.1%} 低于明确口径 {minimum_coverage:.1%}", "仅在用户、学校或期刊明确给出口径时使用"))

    counts = Counter(used)
    top_share = max(counts.values()) / sum(counts.values()) if counts else None
    utilization = len(set(used) & set(entries)) / len(entries) if entries else None
    return {
        "summary": {
            "mode": mode,
            "schemes": sorted(schemes),
            "claim_candidates": len(candidates),
            "cited_claim_candidates": cited_candidates,
            "claim_coverage": coverage,
            "citation_occurrences": len(used),
            "unique_numeric_citations": len(set(used)),
            "listed_numeric_references": len(entries),
            "numeric_reference_utilization": utilization,
            "top_numeric_reference_share": top_share,
            "explicit_minimum_coverage": minimum_coverage,
        },
        "findings": [asdict(item) for item in findings],
    }


def print_text_report(report: dict) -> None:
    summary = report["summary"]
    coverage = summary["claim_coverage"]
    print(f"CLAIM_COVERAGE={'n/a' if coverage is None else f'{coverage:.1%}'} ({summary['cited_claim_candidates']}/{summary['claim_candidates']})")
    print(f"CITATIONS={summary['citation_occurrences']} UNIQUE={summary['unique_numeric_citations']} LISTED={summary['listed_numeric_references']}")
    for finding in report["findings"]:
        print(f"line {finding['line']}: {finding['severity']}: {finding['code']}: {finding['detail']}")
        if finding["excerpt"]:
            print(f"  {finding['excerpt']}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Read-only citation coverage and numeric-reference audit; never rewrites files.")
    parser.add_argument("files", nargs="+", help="Text/Markdown/DOCX files, or '-' for stdin.")
    parser.add_argument("--mode", choices=("general", "literature-review", "proposal"), default="general")
    parser.add_argument("--minimum-coverage", type=float, help="Explicit user/institution threshold from 0 to 1; no default is assumed.")
    parser.add_argument("--encoding", help="Encoding for plain-text inputs.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return 1 for high structural findings or an explicit threshold failure; never rewrites.")
    args = parser.parse_args(argv)
    if args.minimum_coverage is not None and not 0 <= args.minimum_coverage <= 1:
        parser.error("--minimum-coverage must be between 0 and 1")

    reports: list[dict] = []
    read_error = False
    for file_arg in args.files:
        try:
            path_label, content = read_text(file_arg, args.encoding)
        except InputReadError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            read_error = True
            continue
        report = analyze(content, mode=args.mode, minimum_coverage=args.minimum_coverage)
        report["path"] = path_label
        reports.append(report)

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"FILE={report['path']}")
            print_text_report(report)
    if read_error:
        return 2
    if args.strict and any(item["severity"] == "high" for report in reports for item in report["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
