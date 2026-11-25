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

sys.dont_write_bytecode = True

from prose_lint import InputReadError, read_text


REFERENCE_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:(?:[一二三四五六七八九十]+|\d+)[、.．]\s*)?"
    r"(?:(?:主要)?参考文献(?:\s*[（(][^）)\n]{0,20}[）)])?(?:列表)?|references|bibliography)"
    r"\s*[:：]?\s*$",
    re.IGNORECASE,
)
NUMERIC_CITATION = re.compile(
    # Scan a numeric-shaped bracket once; validate its tokens separately.
    # Nested repetitions of optional separators can backtrack exponentially.
    r"\[(\d[\d\s,，;；–—-]*)\](?!\()"
)
NUMERIC_REFERENCE = re.compile(r"^\s*\[(\d+)\]\s*(.+?)\s*$")
EN_SURNAME_PARTICLES = r"(?:(?:van|von|de|del|della|der|la|le|di|da|st\.?)\s+)*"
EN_AUTHOR = rf"{EN_SURNAME_PARTICLES}[A-Z][A-Za-z'’.-]*"
CN_AUTHOR = r"[\u4e00-\u9fff]{2,16}(?:等)?"
AUTHOR_TOKEN = (
    rf"(?:{EN_AUTHOR}(?:\s+(?:&|and)\s+{EN_AUTHOR}|\s+et\s+al\.?)?"
    rf"|{CN_AUTHOR}(?:\s*[、与和]\s*{CN_AUTHOR})*)"
)
YEAR_TOKEN = r"(?:19|20)\d{2}[a-z]?"
YEAR_LIST = rf"{YEAR_TOKEN}(?:\s*[,，、]\s*{YEAR_TOKEN})*"
PARENTHETICAL_AUTHOR_YEAR = re.compile(
    rf"[（(]{AUTHOR_TOKEN}\s*[,，]\s*{YEAR_LIST}"
    rf"(?:\s*[;；]\s*{AUTHOR_TOKEN}\s*[,，]\s*{YEAR_LIST})*[）)]"
)
NARRATIVE_AUTHOR_YEAR = re.compile(
    rf"(?P<author>{AUTHOR_TOKEN})[（(](?P<years>{YEAR_LIST})[）)]"
)
GENERIC_NARRATIVE_AUTHORS = {
    "本研究",
    "该研究",
    "已有研究",
    "相关研究",
    "国内研究",
    "国外研究",
    "研究结果",
    "调查结果",
    "项目报告",
    "本项目",
    "该项目",
    "本课题",
    "该课题",
    "调查阶段",
}
GENERIC_NARRATIVE_AUTHOR = re.compile(
    r"^(?:(?:本|该|此)?(?:研究|项目|课题|调查|报告)(?:阶段|期间|期内)?|"
    r"(?:本|该|此)?(?:阶段|期间|期内|年度|年份|学期))$"
)
GENERIC_NARRATIVE_PERIOD_SUFFIXES = ("阶段", "期间", "期内", "年度", "年份", "学期")
LATEX_CITATION = re.compile(r"\\cite\w*\{[^{}\n]+\}")
DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
SENTENCE = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?", re.MULTILINE)
OWN_STUDY = re.compile(r"^\s*(?:本研究|本文|本项目|笔者|我们)(?:的|在|通过|采用|发现|结果|认为|提出|分析|考察|讨论)")
EXTERNAL_ATTRIBUTION = re.compile(
    r"(?:已有|既有|相关|国内外)?(?:研究|文献|学者|报告|调查|标准|规范|政策|指南|统计)(?:表明|显示|指出|认为|发现|证实|规定|要求|提出|认为)|"
    r"(?:根据|依据|按照)[^。！？!?；;]{0,24}(?:研究|报告|调查|标准|规范|政策|指南|统计)"
)
HIGH_RISK = re.compile(
    r"(?:(?<!\d)\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|人|项|篇|年|个月|天)|"
    r"导致|造成|促使|促进|提高|提升|降低|减少|优于|高于|低于|显著|相关性|因果|"
    r"首次|填补[^。！？!?；;]{0,12}空白|尚无研究|缺乏研究|普遍认为|一致认为)"
)
GENERAL_CLAIM = re.compile(
    r"(?:表明|显示|说明|证实|发现|指出|认为|提出|通常|往往|普遍|主要|核心|关键|有助于|影响|"
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


def parse_numeric_group(group: str) -> tuple[list[int], list[str]]:
    result: list[int] = []
    unparsed: list[str] = []
    parts = re.split(r"[,，;；]", group)
    for index, part in enumerate(parts):
        token = part.strip()
        if not token:
            if index != len(parts) - 1:
                unparsed.append("存在空编号项")
            continue
        range_match = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", token)
        if range_match:
            try:
                start, end = (int(value) for value in range_match.groups())
            except ValueError:
                unparsed.append(f"{token[:60]} 的数值无法转换")
                continue
            if start > end:
                unparsed.append(f"{token[:60]} 的范围起点大于终点")
            elif end - start > 200:
                # This is an expansion budget, not a maximum reference ID.
                unparsed.append(f"{token[:60]} 超出单个范围的展开预算")
            else:
                result.extend(range(start, end + 1))
            continue
        if token.isdigit():
            try:
                result.append(int(token))
            except ValueError:
                unparsed.append(f"{token[:60]} 的数值无法转换")
        else:
            unparsed.append(f"{token[:60]} 不是可解析的编号或范围")
    return result, unparsed


def expand_numeric_group(group: str) -> list[int]:
    return parse_numeric_group(group)[0]


def numeric_citations(text: str) -> list[int]:
    return audit_numeric_citations(text)[0]


def audit_numeric_citations(text: str) -> tuple[list[int], list[Finding]]:
    values: list[int] = []
    findings: list[Finding] = []
    line_no = 1
    previous_end = 0
    for match in NUMERIC_CITATION.finditer(text):
        line_no += text.count("\n", previous_end, match.start())
        parsed, unparsed = parse_numeric_group(match.group(1))
        values.extend(parsed)
        if unparsed:
            findings.append(Finding(line_no, "high", "citation-structure", "unparsed-numeric-citation", "编号引文未能完整解析：" + "；".join(unparsed), match.group(0)[:100]))
        line_no += text.count("\n", match.start(), match.end())
        previous_end = match.end()
    return values, findings


def narrative_author_year_matches(text: str) -> list[re.Match[str]]:
    return [
        match
        for match in NARRATIVE_AUTHOR_YEAR.finditer(text)
        if not is_generic_narrative_author(match.group("author"))
    ]


def is_generic_narrative_author(author: str) -> bool:
    return (
        author in GENERIC_NARRATIVE_AUTHORS
        or bool(GENERIC_NARRATIVE_AUTHOR.fullmatch(author))
        or author.endswith(GENERIC_NARRATIVE_PERIOD_SUFFIXES)
    )


def has_author_year_citation(text: str) -> bool:
    return bool(PARENTHETICAL_AUTHOR_YEAR.search(text) or narrative_author_year_matches(text))


AUTHOR_YEAR_SINGLE = re.compile(
    rf"^\s*(?P<author>{AUTHOR_TOKEN})\s*[,，]\s*(?P<years>{YEAR_LIST})\s*$"
)
AUTHOR_YEAR_YEAR_CAPTURE = re.compile(rf"({YEAR_TOKEN})")
REFERENCE_AUTHOR_THEN_PAREN_YEAR = re.compile(
    r"^(?P<authors>(?:(?![.。]\s*[\u4e00-\u9fffA-Za-z]{2,})[^（(\n]){1,100}?)\s*"
    rf"[（(]\s*(?P<year>{YEAR_TOKEN})\s*[）)]\s*[.。]?"
)
REFERENCE_AUTHOR_THEN_PLAIN_YEAR = re.compile(
    r"^(?P<authors>(?:(?![.。]\s*[\u4e00-\u9fffA-Za-z]{2,})[^(\n]){1,100}?)"
    rf"[,，.]\s*(?P<year>{YEAR_TOKEN})\s*[.,，:：]"
)
REFERENCE_POST_TITLE_YEAR = re.compile(
    rf"[.。]\s*(?P<year>{YEAR_TOKEN})\s*[.,，:：]"
)
REFERENCE_LEADING_AUTHORS = re.compile(
    rf"^(?P<authors>{EN_AUTHOR}(?:\s*,\s*(?:[A-Z]\.(?:\s*[A-Z]\.)*|{EN_AUTHOR}))*(?:\s*(?:[,，]|&|and)\s*{EN_AUTHOR}(?:\s*,\s*[A-Z]\.(?:\s*[A-Z]\.)*)?)*(?:\s+et\s+al\.?)?"
    rf"|[\u4e00-\u9fff]{{2,20}}(?:\s*[,，、与和]\s*[\u4e00-\u9fff]{{2,20}})*(?:\s*等)?)"
)


def normalize_author_key(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.split(r"\s+(?:&|and)\s+|[,，、与和]", cleaned, maxsplit=1)[0].strip()
    cleaned = re.sub(r"(?:等|et\s+al\.?)$", "", cleaned, flags=re.IGNORECASE).strip()
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        return cleaned
    return re.sub(r"\s+", " ", cleaned).lower()


def normalize_author_signature(raw: str) -> tuple[str, ...]:
    cleaned = re.sub(r"(?:等|et\s+al\.?)$", "", raw.strip(), flags=re.IGNORECASE).strip()
    parts = re.split(r"\s+(?:&|and)\s+|[,，、与和]", cleaned)
    tokens: list[str] = []
    for part in parts:
        token = part.strip()
        if not token:
            continue
        if re.fullmatch(r"(?:[A-Z]\.\s*)+", token):
            continue
        if re.search(r"[\u4e00-\u9fff]", token):
            tokens.append(token)
        else:
            tokens.append(re.sub(r"\s+", " ", token).lower())
    return tuple(tokens)


CN_NARRATIVE_PREFIX = re.compile(
    r"^(?:此外|另外|同时|以及|还有|其中|而且|但是|然而|不过|并且|可见|表明|指出|认为|显示|"
    r"根据|依据|按照|参照|参考|基于|结合|正如|至于|关于|对于|针对|由|据|从|在|向|对|和|与|及)+"
)


def strip_cn_narrative_prefix(author: str, *, after_close_paren: bool = False) -> str:
    cleaned = author.strip()
    if after_close_paren:
        cleaned = re.sub(r"^(?:和|与|及|以及|还有|、)+", "", cleaned).strip()
    candidate = CN_NARRATIVE_PREFIX.sub("", cleaned).strip()
    if len(candidate) >= 2:
        return candidate
    return cleaned


def extract_author_year_citations(text: str) -> list[tuple[int, str, str, str]]:
    citations: list[tuple[int, str, str, str]] = []
    for match in PARENTHETICAL_AUTHOR_YEAR.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        inner = match.group(0)[1:-1]
        for part in re.split(r"[;；]", inner):
            single = AUTHOR_YEAR_SINGLE.match(part)
            if not single:
                continue
            author_key = normalize_author_key(single.group("author"))
            if not author_key:
                continue
            for y_match in AUTHOR_YEAR_YEAR_CAPTURE.finditer(single.group("years")):
                citations.append((line_no, author_key, y_match.group(1).lower(), part.strip()))
    for match in narrative_author_year_matches(text):
        line_no = text.count("\n", 0, match.start()) + 1
        raw_author = match.group("author")
        after_close = match.start() > 0 and text[match.start() - 1] in "）)"
        author_key = normalize_author_key(strip_cn_narrative_prefix(raw_author, after_close_paren=after_close))
        if not author_key:
            continue
        for y_match in AUTHOR_YEAR_YEAR_CAPTURE.finditer(match.group("years")):
            citations.append((line_no, author_key, y_match.group(1).lower(), match.group(0).strip()))
    return citations


def _check_duplicate_dois(entries: list[tuple[str, int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    doi_rows: dict[str, list[tuple[str, int]]] = {}
    for label, line_no, content in entries:
        for match in DOI.finditer(content):
            doi = match.group(0).rstrip(".,;:，。；：)]}>").lower()
            doi_rows.setdefault(doi, []).append((label, line_no))
    for doi, rows in doi_rows.items():
        if len(rows) > 1:
            identifiers = ", ".join(label for label, _ in rows)
            findings.append(
                Finding(
                    rows[0][1],
                    "high",
                    "reference-structure",
                    "duplicate-doi",
                    f"DOI {doi} 出现在 {identifiers}",
                    doi,
                )
            )
    return findings


def author_year_reference_entries(
    text: str, heading_line: int | None
) -> tuple[dict[tuple[str, str], list[tuple[int, str]]], list[Finding], list[tuple[str, int, str]]]:
    entries: dict[tuple[str, str], list[tuple[int, str]]] = {}
    signatures: dict[tuple[str, str], list[tuple[str, ...]]] = {}
    findings: list[Finding] = []
    offset = heading_line or 0
    doi_candidates: list[tuple[str, int, str]] = []
    for index, line in enumerate(text.splitlines(), start=offset + 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or NUMERIC_REFERENCE.match(stripped):
            continue
        author_raw = ""
        year = ""
        m_paren = REFERENCE_AUTHOR_THEN_PAREN_YEAR.match(stripped)
        m_plain = REFERENCE_AUTHOR_THEN_PLAIN_YEAR.match(stripped)
        if m_paren:
            author_raw = m_paren.group("authors")
            year = m_paren.group("year").lower()
        elif m_plain:
            author_raw = m_plain.group("authors")
            year = m_plain.group("year").lower()
        else:
            lead = REFERENCE_LEADING_AUTHORS.match(stripped)
            post_year = REFERENCE_POST_TITLE_YEAR.search(stripped[lead.end() :] if lead else stripped)
            if lead and post_year:
                author_raw = lead.group("authors")
                year = post_year.group("year").lower()
        if not author_raw or not year:
            continue
        author_key = normalize_author_key(author_raw)
        if not author_key:
            continue
        sig = normalize_author_signature(author_raw)
        key = (author_key, year)
        existing_sigs = signatures.setdefault(key, [])
        if sig in existing_sigs:
            findings.append(
                Finding(
                    index,
                    "high",
                    "reference-structure",
                    "duplicate-author-year-reference",
                    f"著者—出版年条目 ({author_key}, {year}) 重复",
                    stripped[:100],
                )
            )
            continue
        if existing_sigs:
            findings.append(
                Finding(
                    index,
                    "medium",
                    "reference-structure",
                    "ambiguous-author-year-reference",
                    f"著者—出版年条目 ({author_key}, {year}) 存在同姓同年不同合著者，请核对正文区分",
                    stripped[:100],
                )
            )
        existing_sigs.append(sig)
        entries.setdefault(key, []).append((index, stripped))
        doi_candidates.append((f"{author_key} ({year})", index, stripped))
    return entries, findings, doi_candidates


def strip_author_year_citations(text: str) -> str:
    stripped = PARENTHETICAL_AUTHOR_YEAR.sub("", text)

    def keep_author(match: re.Match[str]) -> str:
        if not is_generic_narrative_author(match.group("author")):
            return match.group("author")
        return match.group(0)

    return NARRATIVE_AUTHOR_YEAR.sub(keep_author, stripped)


def has_citation_marker(text: str) -> bool:
    return bool(NUMERIC_CITATION.search(text) or has_author_year_citation(text) or LATEX_CITATION.search(text))


def citation_schemes(text: str) -> set[str]:
    schemes: set[str] = set()
    if NUMERIC_CITATION.search(text):
        schemes.add("numeric")
    if has_author_year_citation(text):
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
        boundaries = list(line)
        for pattern in (NUMERIC_CITATION, PARENTHETICAL_AUTHOR_YEAR, LATEX_CITATION):
            for citation in pattern.finditer(line):
                boundaries[citation.start() : citation.end()] = "x" * len(citation.group(0))
        for match in SENTENCE.finditer("".join(boundaries)):
            sentence = line[match.start() : match.end()].strip()
            if len(re.sub(r"\s+", "", sentence)) >= 8:
                rows.append((line_no, sentence))
    return rows


def is_claim_candidate(sentence: str, mode: str) -> bool:
    visible = NUMERIC_CITATION.sub("", LATEX_CITATION.sub("", sentence))
    visible = strip_author_year_citations(visible).strip()
    if OWN_STUDY.match(visible) and not EXTERNAL_ATTRIBUTION.search(visible):
        return False
    if EXTERNAL_ATTRIBUTION.search(visible) or HIGH_RISK.search(visible):
        return True
    if mode == "literature-review" and GENERAL_CLAIM.search(visible):
        return True
    return bool(has_citation_marker(sentence) and GENERAL_CLAIM.search(visible))


def analyze(text: str, *, mode: str = "general", minimum_marker_coverage: float | None = None) -> dict:
    body, references, heading_line = split_document(text)
    used, numeric_findings = audit_numeric_citations(body)
    entries, findings = reference_entries(references, heading_line)
    findings.extend(numeric_findings)
    schemes = citation_schemes(body)

    for identifier in sorted(set(used) - set(entries)):
        findings.append(Finding(1, "high", "citation-mapping", "missing-reference-entry", f"正文使用 [{identifier}]，文后未找到对应编号条目", f"[{identifier}]"))
    for identifier in sorted(set(entries) - set(used)):
        line_no, content = entries[identifier]
        findings.append(Finding(line_no, "low", "citation-mapping", "unused-reference-entry", f"文后条目 [{identifier}] 未在正文编号引文中使用", content[:100]))

    ay_entries: dict[tuple[str, str], list[tuple[int, str]]] = {}
    ay_utilization: float | None = None
    ay_doi_candidates: list[tuple[str, int, str]] = []
    if references.strip():
        ay_entries, ay_findings, ay_doi_candidates = author_year_reference_entries(references, heading_line)
        findings.extend(ay_findings)
        ay_citations = extract_author_year_citations(body)
        if ay_entries or (not entries and ay_citations):
            cited_keys: dict[tuple[str, str], tuple[int, str]] = {}
            for line_no, author_key, year, raw_display in ay_citations:
                resolved_key = (author_key, year)
                if resolved_key not in ay_entries and re.search(r"[\u4e00-\u9fff]", author_key):
                    suffix_matches = [
                        ek for ek in ay_entries
                        if ek[1] == year and author_key.endswith(ek[0]) and len(ek[0]) >= 2
                    ]
                    if len(suffix_matches) == 1:
                        resolved_key = suffix_matches[0]
                cited_keys.setdefault(resolved_key, (line_no, raw_display))
            for key, (line_no, raw_display) in cited_keys.items():
                if key not in ay_entries:
                    findings.append(
                        Finding(
                            line_no,
                            "high",
                            "citation-mapping",
                            "missing-author-year-reference",
                            f"正文使用 ({key[0]}, {key[1]})，文后未找到对应著者—出版年条目",
                            raw_display[:100],
                        )
                    )
            for key in sorted(set(ay_entries) - set(cited_keys)):
                for line_no, content in ay_entries[key]:
                    findings.append(
                        Finding(
                            line_no,
                            "low",
                            "citation-mapping",
                            "unused-author-year-reference",
                            f"文后条目 ({key[0]}, {key[1]}) 未在正文著者—出版年引文中使用",
                            content[:100],
                        )
                    )
            if ay_entries:
                ay_utilization = len(set(cited_keys) & set(ay_entries)) / len(ay_entries)
    if ay_doi_candidates:
        numeric_dois = [(f"[{identifier}]", line_no, content) for identifier, (line_no, content) in entries.items()]
        findings.extend(_check_duplicate_dois([*numeric_dois, *ay_doi_candidates]))
        # Deduplicate duplicate-doi findings if numeric reference_entries already emitted the exact same DOI line
        dedup_findings: list[Finding] = []
        seen_finding_keys: set[tuple[int, str, str]] = set()
        for item in findings:
            fkey = (item.line, item.code, item.excerpt)
            if item.code == "duplicate-doi" and fkey in seen_finding_keys:
                continue
            seen_finding_keys.add(fkey)
            dedup_findings.append(item)
        findings = dedup_findings

    candidates: list[tuple[int, str, bool]] = []
    for line_no, sentence in sentence_rows(body):
        if not is_claim_candidate(sentence, mode):
            continue
        marker_present = has_citation_marker(sentence)
        candidates.append((line_no, sentence, marker_present))
        if not marker_present:
            findings.append(Finding(line_no, "medium", "claim-coverage", "uncited-claim-candidate", "该论断可能需要来源支持，请结合研究语境人工判断", sentence[:100]))

    marker_covered_candidates = sum(1 for _, _, marker_present in candidates if marker_present)
    marker_coverage = marker_covered_candidates / len(candidates) if candidates else None
    if minimum_marker_coverage is not None and marker_coverage is not None and marker_coverage < minimum_marker_coverage:
        findings.append(Finding(1, "high", "citation-marker-coverage", "below-explicit-marker-minimum", f"候选论断的引用标记覆盖率 {marker_coverage:.1%} 低于明确结构口径 {minimum_marker_coverage:.1%}", "该值只表示引用标记存在；有效支持仍须核对原文和证据账本"))

    counts = Counter(used)
    top_share = max(counts.values()) / sum(counts.values()) if counts else None
    utilization = len(set(used) & set(entries)) / len(entries) if entries else None
    return {
        "summary": {
            "mode": mode,
            "schemes": sorted(schemes),
            "claim_candidates": len(candidates),
            "marker_covered_claim_candidates": marker_covered_candidates,
            "citation_marker_coverage": marker_coverage,
            "citation_occurrences": len(used),
            "unique_numeric_citations": len(set(used)),
            "listed_numeric_references": len(entries),
            "numeric_reference_utilization": utilization,
            "listed_author_year_references": len(ay_entries),
            "author_year_reference_utilization": ay_utilization,
            "top_numeric_reference_share": top_share,
            "explicit_minimum_marker_coverage": minimum_marker_coverage,
        },
        "findings": [asdict(item) for item in findings],
    }


def print_text_report(report: dict) -> None:
    summary = report["summary"]
    coverage = summary["citation_marker_coverage"]
    print(f"CITATION_MARKER_COVERAGE={'n/a' if coverage is None else f'{coverage:.1%}'} ({summary['marker_covered_claim_candidates']}/{summary['claim_candidates']})")
    print("NOTE=Marker coverage is structural only; it does not prove that a source supports the claim.")
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
    parser.add_argument("--minimum-marker-coverage", type=float, help="Explicit structural marker threshold from 0 to 1; no default is assumed and semantic support is not inferred.")
    parser.add_argument("--encoding", help="Encoding for plain-text inputs.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return 1 for high structural findings or an explicit threshold failure; never rewrites.")
    args = parser.parse_args(argv)
    if args.minimum_marker_coverage is not None and not 0 <= args.minimum_marker_coverage <= 1:
        parser.error("--minimum-marker-coverage must be between 0 and 1")

    reports: list[dict] = []
    read_error = False
    for file_arg in args.files:
        try:
            path_label, content = read_text(file_arg, args.encoding)
        except InputReadError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            read_error = True
            continue
        report = analyze(content, mode=args.mode, minimum_marker_coverage=args.minimum_marker_coverage)
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
