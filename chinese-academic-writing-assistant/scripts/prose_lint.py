#!/usr/bin/env python3
"""Report candidate prose risks in Chinese academic drafts without rewriting.

The read-only scanner is academically adapted from the user-owned
``chinese-official-writing/scripts/prose_lint.py`` framework.  It preserves the
Finding model, standard-library DOCX reading, protected spans, and text/JSON
reporting while replacing official-document rules with academic-writing checks.

Matches and frequencies are review candidates, not proof that text is wrong or
AI-generated.  Semantic decisions and any local rewrite belong to the model or
author after reading the evidence and surrounding argument.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    severity: str
    category: str
    pattern_id: str
    match: str
    count: int
    excerpt: str
    advice: str


class InputReadError(Exception):
    """Raised when an input cannot be read as usable text."""


Pattern = tuple[str, str, str, str, str]

SEMANTIC_PATTERNS: tuple[Pattern, ...] = (
    (
        "low",
        "semantic-review",
        "not-but",
        r"不是[^。！？；;\n]{0,80}而是",
        "回读前文与材料，判断被否定对象是否真实存在、两项是否构成对照。",
    ),
    (
        "low",
        "semantic-review",
        "not-rather-but",
        r"并非[^。！？；;\n]{0,80}而是",
        "核对是否为必要概念辨析或真实反驳；单次命中不直接改写。",
    ),
    (
        "low",
        "semantic-review",
        "rather-than",
        r"而不是",
        "核对前文是否提出替代项，避免无依据的先否定后肯定。",
    ),
    (
        "low",
        "semantic-review",
        "not-only",
        r"不仅[^。！？；;\n]{0,80}(?:还|而且|更)",
        "核对两项是否存在真实递进关系以及证据是否同时支持。",
    ),
    (
        "low",
        "semantic-review",
        "not-only-also",
        r"不但[^。！？；;\n]{0,80}而且",
        "核对两项是否存在真实递进关系以及证据是否同时支持。",
    ),
    (
        "low",
        "semantic-review",
        "both-and",
        r"既[^。！？；;\n]{0,80}又",
        "核对并列项是否各有材料落点；真实并列应保留。",
    ),
    (
        "low",
        "semantic-review",
        "two-sides",
        r"一方面[^。！？；;\n]{0,120}另一方面",
        "核对是否为真实的两个分析面向，而非机械制造平衡。",
    ),
    (
        "medium",
        "evidence-review",
        "vague-attribution",
        r"(?:有研究|相关研究|已有研究|学界普遍|有学者)(?:表明|显示|指出|认为)",
        "核对相邻引用与来源层级；无可回查来源时不要保留模糊背书。",
    ),
    (
        "low",
        "claim-strength-review",
        "obviousness-claim",
        r"(?:毋庸置疑|不言而喻|显而易见)",
        "核对该强判断是否由证据支持，不能用提示语替代论证。",
    ),
    (
        "low",
        "claim-strength-review",
        "inflated-significance",
        r"(?:这|这一(?:发现|结果|现象))[^。！？\n]{0,24}(?:充分)?(?:说明|表明)[^。！？\n]{0,36}(?:重要意义|重要价值|深远影响)",
        "核对结论强度和实际作用对象，避免从有限材料直接拔高意义。",
    ),
)

DELIVERY_PATTERNS: tuple[Pattern, ...] = (
    (
        "high",
        "production-residue",
        "model-identity",
        r"作为(?:一个)?\s*AI|我是(?:一个)?\s*AI|(?:本文|本稿|本报告|以上内容|以下内容|该文稿)[^。\n]{0,12}由\s*AI\s*(?:起草|生成|辅助生成)|as an ai(?: language)? model",
        "删除模型身份或生成来源旁白；诚信披露应服从用户和机构要求另行处理。",
    ),
    (
        "high",
        "production-residue",
        "thought-process",
        r"我的(?:思路|推理|分析)|(?:思考|推理)过程(?:如下|是|：|:)|内部推理|接下来我会|我将根据(?:用户|你的)要求",
        "删除思考过程和起草动作说明，只保留学术文本。",
    ),
    (
        "high",
        "production-residue",
        "delivery-preface",
        r"(?:以下|下面)(?:为|是)(?:按[^。\n]{0,16}要求)?(?:修改后|修订后|调整后|最终)?(?:的)?(?:正文|稿件|文稿|内容)",
        "删除交付前言，直接输出正文。",
    ),
    (
        "high",
        "production-residue",
        "version-audience-label",
        r"给领导看的|不用于\s*AIGC\s*检测|(?:以下|本稿|本版|当前(?:稿件|文本)?|交付(?:稿|文本)?)[^。\n]{0,16}(?:脱敏版|修改版|修订版)",
        "核对是否为用户明确要求显示的正式标识；否则移出成品正文。",
    ),
    (
        "medium",
        "production-residue",
        "version-label-candidate",
        r"脱敏版|修改版|修订版",
        "该词可能是研究材料的正式版本名，也可能是制作标签；结合对象和用户要求判断。",
    ),
    (
        "high",
        "production-residue",
        "internal-gate",
        r"(?:已|已经|现已)?通过(?:内容|质量|交付|发布)门禁|内部(?:校验|审校)(?:结果|通过|完成)|(?:路由|加载)(?:结果|过程|文件)|(?:writer|verifier)(?:[_\s-]?(?:输出|结果|模型|编号|上下文))|(?:测试样本|测试用例)(?:编号|输出|用于验证(?:本\s*Skill|提示词)|通过(?:门禁|校验))|提示词(?:检查|规则|内容)",
        "删除内部门禁、路由、测试或模型编排信息。",
    ),
    (
        "medium",
        "production-residue",
        "self-certification",
        r"不新增原文外事实|不超出(?:已给|现有)?事实|不改变(?:事实|引用|术语|论断强度)",
        "核对是否在复述写作规则；必要的研究范围限制应改成学术表述并就近放置。",
    ),
    (
        "medium",
        "tail-note",
        "small-print-tail",
        r"(?:以上|上述)(?:内容|说明)[^。\n]{0,32}(?:不作为(?:结论|依据)|仅供参考)|(?:小字说明|免责声明|边界说明)[：:][^\n]{0,100}",
        "核对是否为重复兜底或制作型小字说明；真实研究限制应融入对应论断。",
    ),
)

FORMAT_PATTERNS: tuple[Pattern, ...] = (
    (
        "medium",
        "punctuation",
        "repeated-punctuation",
        r"([，。；：！？、])\1+",
        "检查重复标点；引用、公式或原样材料中的符号可保留。",
    ),
    (
        "medium",
        "punctuation",
        "conflicting-punctuation",
        r"[，；：。][。；，]|[！？][，；：。]",
        "检查相邻标点是否误叠。",
    ),
    (
        "low",
        "punctuation",
        "halfwidth-cn-punctuation",
        r"[\u4e00-\u9fff][,;:!?][\u4e00-\u9fff]",
        "中文句内通常使用全角标点；英文题名、公式和引用格式除外。",
    ),
    (
        "low",
        "punctuation",
        "space-before-punctuation",
        r"[ \t\u3000]+[，。；：！？]",
        "检查中文标点前是否误留空格。",
    ),
    (
        "medium",
        "format",
        "emoji",
        r"[\U0001F300-\U0001FAFF]",
        "论文正文通常不使用 Emoji；研究对象原文或编码材料除外。",
    ),
)

# Thresholds locate concentrated language only.  They are not quotas or errors.
FREQUENCY_TERMS: dict[str, tuple[int, str]] = {
    "此外": (3, "discourse-marker"),
    "同时": (4, "discourse-marker"),
    "因此": (3, "discourse-marker"),
    "进一步": (3, "discourse-marker"),
    "综上所述": (2, "discourse-marker"),
    "需要指出的是": (2, "metadiscourse"),
    "值得注意的是": (2, "metadiscourse"),
    "本文将": (3, "metadiscourse"),
    "本研究": (6, "metadiscourse"),
    "不应": (3, "negation"),
    "不宜": (3, "negation"),
    "不能": (4, "negation"),
    "并非": (3, "negation"),
    "赋能": (2, "abstract-term"),
    "协同": (5, "abstract-term"),
    "路径": (7, "academic-term"),
    "框架": (7, "academic-term"),
    "范式": (5, "academic-term"),
    "系统性": (5, "abstract-term"),
}

DELIVERY_MODES = ("generic", "body-only", "body-with-suggestions", "review-only")
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
REFERENCE_HEADING = re.compile(r"^\s*(?:#{1,6}\s*)?参考文献\s*$")
POST_REFERENCE_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:附录(?:\s*[A-Za-zＡ-Ｚａ-ｚ0-9一二三四五六七八九十]+)?|"
    r"致谢|后记|作者简介|攻读(?:学位|硕士|博士)期间[^\n]{0,30})\s*$"
)
SUGGESTION_HEADING = re.compile(r"^\s*(?:#{1,6}\s*)?补充与修改建议\s*$")
LIST_OR_HEADING = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)、]\s+|[一二三四五六七八九十]+、)")
PROTECTED_INLINE = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"`[^`\n]+`",
        r"\$[^$\n]+\$",
        r"\\\([^\n]*?\\\)",
        r"\\\[[^\n]*?\\\]",
        r"\\(?:cite|ref|eqref|label|url)\{[^{}\n]+\}",
        r"https?://[^\s<>，。；：！？、“”‘’（）【】]+",
        r"\b(?:doi:\s*)?10\.\d{4,9}/[-._;()/:A-Z0-9]+",
        r"\b[\w.+-]+@[\w.-]+\.[A-Z]{2,}\b",
        r"\[(?:\d+\s*[-–—,，]?\s*)+\]",
        r"[（(][^()（）\n]{0,36}(?:19|20)\d{2}[a-z]?[^()（）\n]{0,16}[）)]",
        r"[A-Za-z]:\\[^\s，。；：！？<>]+|(?<![\w\u4e00-\u9fff])/(?:[^/\s，。；：！？<>]+/)+[^/\s，。；：！？<>]+",
    )
)


def read_docx(path: Path) -> str:
    """Read only the main DOCX body, excluding headers, comments, and review notes."""
    try:
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                raise InputReadError(f"DOCX 缺少正文 XML: {path}")
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except FileNotFoundError as exc:
        raise InputReadError(f"文件不存在: {path}") from exc
    except zipfile.BadZipFile as exc:
        raise InputReadError(f"文件损坏或不是有效 DOCX: {path}") from exc
    except ElementTree.ParseError as exc:
        raise InputReadError(f"DOCX 正文 XML 无法解析: {path}") from exc
    except OSError as exc:
        raise InputReadError(f"无法读取 DOCX: {path}: {exc}") from exc

    paragraphs: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.rsplit("}", 1)[-1] != "p":
            continue
        pieces: list[str] = []
        for element in paragraph.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag == "t" and element.text:
                pieces.append(element.text)
            elif tag == "br":
                pieces.append("\n")
            elif tag == "tab":
                pieces.append("\t")
        paragraphs.append("".join(pieces))
    return "\n".join(paragraphs)


def read_text(path_arg: str, encoding: str | None) -> tuple[str, str]:
    if path_arg == "-":
        return "<stdin>", sys.stdin.read()

    path = Path(path_arg)
    if path.suffix.lower() == ".docx":
        return str(path), read_docx(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise InputReadError(f"文件不存在: {path}") from exc
    except PermissionError as exc:
        raise InputReadError(f"无权限读取文件: {path}") from exc
    except OSError as exc:
        raise InputReadError(f"无法读取文件: {path}: {exc}") from exc

    encodings = [encoding] if encoding else ["utf-8-sig", "utf-8", "gb18030"]
    for candidate in encodings:
        if not candidate:
            continue
        try:
            return str(path), raw.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    raise InputReadError(f"无法按指定或常用中文编码解码文件: {path}")


def mark(mask: list[bool], start: int, end: int) -> None:
    for index in range(max(0, start), min(len(mask), end)):
        mask[index] = True


def protected_masks(lines: list[str]) -> list[list[bool]]:
    """Mark code, quotations, references, citations, formulas, URLs, and paths."""
    masks = [[False] * len(line) for line in lines]

    in_fence = False
    in_display_math = False
    in_latex_environment = False
    in_references = False
    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if in_references and POST_REFERENCE_HEADING.match(stripped):
            in_references = False
        if REFERENCE_HEADING.match(stripped):
            in_references = True
        if in_references:
            mark(masks[line_index], 0, len(line))
            continue

        if stripped.startswith(("```", "~~~")):
            mark(masks[line_index], 0, len(line))
            in_fence = not in_fence
            continue
        if in_fence:
            mark(masks[line_index], 0, len(line))
            continue

        if "\\begin{" in line:
            in_latex_environment = True
        if in_latex_environment:
            mark(masks[line_index], 0, len(line))
            if "\\end{" in line:
                in_latex_environment = False
            continue

        if in_display_math:
            mark(masks[line_index], 0, len(line))
            if "$$" in line:
                in_display_math = False
            continue
        if line.count("$$") % 2 == 1:
            first = line.find("$$")
            mark(masks[line_index], first, len(line))
            in_display_math = True
        elif "$$" in line:
            position = 0
            while True:
                left = line.find("$$", position)
                if left == -1:
                    break
                right = line.find("$$", left + 2)
                if right == -1:
                    break
                mark(masks[line_index], left, right + 2)
                position = right + 2

    quote_pairs = {"“": "”", "‘": "’", '"': '"', "「": "」", "『": "』", "《": "》"}
    active_close: str | None = None
    for line_index, line in enumerate(lines):
        if masks[line_index] and all(masks[line_index]):
            continue
        index = 0
        while index < len(line):
            if active_close is not None:
                right = line.find(active_close, index)
                if right == -1:
                    mark(masks[line_index], index, len(line))
                    break
                mark(masks[line_index], index, right + 1)
                index = right + 1
                active_close = None
                continue

            openings = [(line.find(symbol, index), symbol) for symbol in quote_pairs]
            openings = [(position, symbol) for position, symbol in openings if position != -1]
            if not openings:
                break
            left, symbol = min(openings)
            close = quote_pairs[symbol]
            right = line.find(close, left + 1)
            if right != -1:
                mark(masks[line_index], left, right + 1)
                index = right + 1
                continue
            future_close = any(
                close in future
                for future in lines[line_index + 1 : line_index + 9]
                if future.strip()
            )
            if future_close:
                mark(masks[line_index], left, len(line))
                active_close = close
                break
            index = left + 1

    for line_index, line in enumerate(lines):
        for pattern in PROTECTED_INLINE:
            for match in pattern.finditer(line):
                mark(masks[line_index], match.start(), match.end())
    return masks


def visible_line(line: str, mask: list[bool]) -> str:
    # A one-character newline sentinel preserves columns while stopping patterns
    # that explicitly exclude line breaks from crossing protected material.
    return "".join("\n" if protected else character for character, protected in zip(line, mask))


def excerpt(line: str, start: int, end: int) -> str:
    left = max(0, start - 28)
    right = min(len(line), end + 28)
    return re.sub(r"\s+", " ", line[left:right].strip())


def body_limit(lines: list[str], delivery_mode: str) -> int:
    if delivery_mode != "body-with-suggestions":
        return len(lines)
    for index, line in enumerate(lines):
        if SUGGESTION_HEADING.match(line.strip()):
            return index
    return len(lines)


def add_pattern_findings(
    findings: list[Finding],
    path_label: str,
    lines: list[str],
    visible: list[str],
    patterns: tuple[Pattern, ...],
    line_limit: int,
) -> None:
    compiled = [(severity, category, pattern_id, re.compile(regex, re.IGNORECASE), advice)
                for severity, category, pattern_id, regex, advice in patterns]
    for line_index, candidate in enumerate(visible[:line_limit]):
        for severity, category, pattern_id, regex, advice in compiled:
            for match in regex.finditer(candidate):
                findings.append(
                    Finding(
                        path=path_label,
                        line=line_index + 1,
                        column=match.start() + 1,
                        severity=severity,
                        category=category,
                        pattern_id=pattern_id,
                        match=lines[line_index][match.start() : match.end()],
                        count=1,
                        excerpt=excerpt(lines[line_index], match.start(), match.end()),
                        advice=advice,
                    )
                )


def frequency_findings(
    path_label: str,
    lines: list[str],
    visible: list[str],
    line_limit: int,
) -> list[Finding]:
    findings: list[Finding] = []
    for term, (threshold, kind) in FREQUENCY_TERMS.items():
        positions: list[tuple[int, int]] = []
        for line_index, line in enumerate(visible[:line_limit]):
            start = 0
            while True:
                column = line.find(term, start)
                if column == -1:
                    break
                positions.append((line_index, column))
                start = column + len(term)
        if len(positions) < threshold:
            continue
        line_index, column = positions[0]
        findings.append(
            Finding(
                path=path_label,
                line=line_index + 1,
                column=column + 1,
                severity="low",
                category="frequency-review",
                pattern_id=f"term-{kind}",
                match=term,
                count=len(positions),
                excerpt=excerpt(lines[line_index], column, column + len(term)),
                advice=(
                    f"全文可见区出现 {len(positions)} 次；结合章节功能判断是否为必要术语、"
                    "真实衔接或机械复现，不按阈值自动换词。"
                ),
            )
        )
    return findings


def paragraph_blocks(visible: list[str], line_limit: int) -> list[tuple[int, str, int]]:
    blocks: list[tuple[int, str, int]] = []
    current: list[str] = []
    start_line = 1
    section = 0

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append((start_line, "".join(current), section))
            current = []

    for line_index, line in enumerate(visible[:line_limit], start=1):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if LIST_OR_HEADING.match(stripped) or stripped.startswith("|"):
            flush()
            section += 1
            continue
        if not current:
            start_line = line_index
        current.append(stripped)
    flush()
    return blocks


def content_tokens(text: str) -> set[str]:
    compact = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)
    if len(compact) < 24:
        return set()
    return {
        compact[index : index + width]
        for width in (2, 3)
        for index in range(len(compact) - width + 1)
    }


def structure_findings(
    path_label: str,
    lines: list[str],
    visible: list[str],
    line_limit: int,
) -> list[Finding]:
    findings: list[Finding] = []
    blocks = paragraph_blocks(visible, line_limit)

    starts: dict[str, list[int]] = {}
    for line_no, text, _ in blocks:
        compact = re.sub(r"^[^\u4e00-\u9fffA-Za-z0-9]+", "", text)
        compact = re.sub(r"\s+", "", compact)
        if len(compact) >= 6:
            starts.setdefault(compact[:6], []).append(line_no)
    for start, line_numbers in starts.items():
        if len(line_numbers) < 3:
            continue
        line_no = line_numbers[0]
        findings.append(
            Finding(
                path=path_label,
                line=line_no,
                column=1,
                severity="low",
                category="structure-review",
                pattern_id="repeated-paragraph-start",
                match=start,
                count=len(line_numbers),
                excerpt=lines[line_no - 1].strip()[:56],
                advice=f"有 {len(line_numbers)} 段使用相同开头；结合段落主导任务判断是否机械复现。",
            )
        )

    for index in range(1, len(blocks)):
        previous_line, previous_text, previous_section = blocks[index - 1]
        line_no, text, section = blocks[index]
        if section != previous_section or min(len(previous_text), len(text)) < 60:
            continue
        previous_tokens = content_tokens(previous_text)
        tokens = content_tokens(text)
        if not previous_tokens or not tokens:
            continue
        shared = previous_tokens & tokens
        ratio = len(shared) / len(previous_tokens | tokens)
        if len(shared) >= 18 and ratio >= 0.42:
            findings.append(
                Finding(
                    path=path_label,
                    line=line_no,
                    column=1,
                    severity="medium",
                    category="structure-review",
                    pattern_id="adjacent-paragraph-overlap",
                    match=";".join(sorted(shared)[:6]),
                    count=1,
                    excerpt=lines[line_no - 1].strip()[:56],
                    advice=f"与约第 {previous_line} 行的上一段重合较高；核对是否重复解释同一论点或限制。",
                )
            )

    sentences: list[tuple[int, int]] = []
    for line_no, text, _ in blocks:
        for sentence in re.split(r"[。！？；]+", text):
            length = len(re.sub(r"\s+", "", sentence))
            if 12 <= length <= 120:
                sentences.append((line_no, length))
    for start in range(0, max(0, len(sentences) - 5)):
        window = sentences[start : start + 6]
        lengths = [length for _, length in window]
        mean = sum(lengths) / len(lengths)
        variance = sum((length - mean) ** 2 for length in lengths) / len(lengths)
        coefficient = math.sqrt(variance) / mean if mean else 1.0
        if 20 <= mean <= 80 and coefficient <= 0.08:
            line_no = window[0][0]
            findings.append(
                Finding(
                    path=path_label,
                    line=line_no,
                    column=1,
                    severity="low",
                    category="structure-review",
                    pattern_id="uniform-sentence-rhythm",
                    match=",".join(str(length) for length in lengths),
                    count=6,
                    excerpt=lines[line_no - 1].strip()[:56],
                    advice="连续六句长度高度接近；只在句法和段落任务也机械重复时调整节奏。",
                )
            )
            break
    return findings


def unbalanced_findings(
    path_label: str,
    lines: list[str],
    visible: list[str],
    line_limit: int,
) -> list[Finding]:
    findings: list[Finding] = []
    text = "\n".join(visible[:line_limit])
    pairs = (("“", "”"), ("‘", "’"), ("「", "」"), ("『", "』"), ("《", "》"), ("（", "）"), ("【", "】"), ("[", "]"))
    for opening, closing in pairs:
        opening_count = text.count(opening)
        closing_count = text.count(closing)
        if opening_count == closing_count:
            continue
        target = opening if opening_count > closing_count else closing
        line_index = next((index for index, line in enumerate(visible[:line_limit]) if target in line), 0)
        column = visible[line_index].find(target) if visible else 0
        findings.append(
            Finding(
                path=path_label,
                line=line_index + 1,
                column=max(0, column) + 1,
                severity="medium",
                category="punctuation",
                pattern_id="unbalanced-pair",
                match=f"{opening}{closing}",
                count=abs(opening_count - closing_count),
                excerpt=lines[line_index].strip()[:56] if lines else "",
                advice="检查成对符号是否缺失；引用、公式和模板中的特殊用法需人工确认。",
            )
        )
    return findings


def scan(
    path_label: str,
    text: str,
    *,
    include_format: bool = False,
    include_structure: bool = False,
    delivery_mode: str = "generic",
) -> list[Finding]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    masks = protected_masks(lines)
    visible = [visible_line(line, mask) for line, mask in zip(lines, masks)]
    line_limit = body_limit(lines, delivery_mode)
    findings: list[Finding] = []

    if delivery_mode != "review-only":
        add_pattern_findings(findings, path_label, lines, visible, SEMANTIC_PATTERNS, line_limit)
        findings.extend(frequency_findings(path_label, lines, visible, line_limit))
    add_pattern_findings(findings, path_label, lines, visible, DELIVERY_PATTERNS, len(lines))

    if include_format:
        add_pattern_findings(findings, path_label, lines, visible, FORMAT_PATTERNS, len(lines))
        findings.extend(unbalanced_findings(path_label, lines, visible, len(lines)))
    if include_structure and delivery_mode != "review-only":
        findings.extend(structure_findings(path_label, lines, visible, line_limit))

    unique: list[Finding] = []
    seen: set[tuple[str, int, int, str, str]] = set()
    for finding in findings:
        key = (finding.path, finding.line, finding.column, finding.category, finding.match)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def print_text(findings: Iterable[Finding]) -> None:
    for finding in findings:
        print(
            f"{finding.path}:{finding.line}:{finding.column}: "
            f"{finding.severity}: {finding.pattern_id}: {finding.match}"
        )
        print(f"  {finding.excerpt} | {finding.advice}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Report candidate language and residue risks in Chinese academic drafts."
    )
    parser.add_argument("files", nargs="+", help="Text/Markdown/DOCX files, or '-' for stdin.")
    parser.add_argument("--encoding", help="Encoding for plain-text inputs.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON array of findings.")
    parser.add_argument("--format", action="store_true", help="Also report punctuation and format candidates.")
    parser.add_argument("--structure", action="store_true", help="Also report repeated starts, overlap, and uniform rhythm.")
    parser.add_argument(
        "--delivery-mode",
        choices=DELIVERY_MODES,
        default="generic",
        help="Select final-body, body-with-suggestions, or review-output handling.",
    )
    parser.add_argument("--strict", action="store_true", help="Return 1 when findings meet --fail-on; never rewrites.")
    parser.add_argument(
        "--fail-on",
        choices=("low", "medium", "high"),
        default="high",
        help="Severity threshold used only with --strict (default: high).",
    )
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    had_read_error = False
    for file_arg in args.files:
        try:
            path_label, text = read_text(file_arg, args.encoding)
        except InputReadError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            had_read_error = True
            continue
        findings.extend(
            scan(
                path_label,
                text,
                include_format=args.format,
                include_structure=args.structure,
                delivery_mode=args.delivery_mode,
            )
        )

    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], ensure_ascii=False, indent=2))
    elif findings:
        print_text(findings)
    elif not had_read_error:
        print("No candidate prose risks found.")

    if had_read_error:
        return 2
    if args.strict:
        threshold = SEVERITY_RANK[args.fail_on]
        return 1 if any(SEVERITY_RANK[finding.severity] >= threshold for finding in findings) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
