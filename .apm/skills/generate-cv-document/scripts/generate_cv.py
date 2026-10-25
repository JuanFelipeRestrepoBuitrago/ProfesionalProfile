#!/usr/bin/env python3
"""Generate a styled CV .docx from a canonical CV markdown source.

The script fills a tokenized .docx template (one example per repeatable
section, marked with XML comment sentinels) with data parsed from the
canonical CV markdown. All run-level styling in the template is preserved
verbatim; only text content is substituted and repeatable blocks are cloned
once per item. The number of jobs, bullets, skills, achievements, and
education entries is therefore unbounded and driven entirely by the source.

Usage:
    generate_cv.py --cv <cv.md> --template <name.template.docx> --out <out.docx>
            [--photo <image>]

If the template embeds a header photo (the ``general`` format does), the
``--photo`` option replaces it with the given image file, defaulting to
``resources/DEFAULT.jpg``. The image is stored under the template's existing
media name so the package relationships and content types stay valid; Word
detects the real image format from the bytes.

The template .docx must contain a tokenized word/document.xml using:
  - Static tokens: {{FULL_NAME}}, {{HEADLINE}}, {{CONTACT_EMAIL_PHONE}},
    {{CONTACT_LOCATION_LINKS}}, {{SUMMARY}}, {{COMPETENCIES}},
    {{ADDITIONAL_ACTIVITIES}}, and section-heading tokens {{SECTION_*}}.
  - Repeatable blocks delimited by <!--REPEAT:X-->...<!--END:X--> with inner
    tokens; EXPERIENCE nests an <!--REPEAT:EXP_BULLET--> block.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field
from html import escape
from pathlib import Path


# --------------------------------------------------------------------------
# Markdown parsing
# --------------------------------------------------------------------------


@dataclass
class Experience:
    title: str
    company: str
    dates: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class CVData:
    full_name: str = ""
    headline: str = ""
    contact_email_phone: str = ""
    contact_location_links: str = ""
    section_titles: dict[str, str] = field(default_factory=dict)
    summary: str = ""
    experiences: list[Experience] = field(default_factory=list)
    education: list[tuple[str, str]] = field(default_factory=list)
    skills: list[tuple[str, str]] = field(default_factory=list)
    competencies: str = ""
    achievements: list[str] = field(default_factory=list)
    additional_activities: str = ""


# Canonical heading text -> internal section key. Supports English and Spanish.
SECTION_ALIASES = {
    "professional summary": "SUMMARY",
    "resumen profesional": "SUMMARY",
    "professional experience": "EXPERIENCE",
    "experiencia profesional": "EXPERIENCE",
    "education": "EDUCATION",
    "educacion": "EDUCATION",
    "educación": "EDUCATION",
    "technical skills": "SKILLS",
    "habilidades tecnicas": "SKILLS",
    "habilidades técnicas": "SKILLS",
    "core competencies": "COMPETENCIES",
    "competencias clave": "COMPETENCIES",
    "achievements & recognition": "ACHIEVEMENTS",
    "achievements and recognition": "ACHIEVEMENTS",
    "logros y reconocimientos": "ACHIEVEMENTS",
    "additional activities": "ADDITIONAL",
    "actividades adicionales": "ADDITIONAL",
}


def _strip_md(text: str) -> str:
    """Remove markdown emphasis and links, keeping link text."""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1: \2", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"\1", text)
    return text.strip()


def parse_cv(md_path: Path) -> CVData:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    cv = CVData()

    # --- Header block (before the first H2) ---
    i = 0
    n = len(lines)
    # H1 = name
    while i < n and not lines[i].startswith("# "):
        i += 1
    if i < n:
        cv.full_name = _strip_md(lines[i][2:])
        i += 1

    # Collect header lines until first "## "
    header: list[str] = []
    while i < n and not lines[i].startswith("## "):
        if lines[i].strip():
            header.append(lines[i].strip())
        i += 1

    header = [_strip_md(h) for h in header]
    if header:
        cv.headline = header[0]
    # Contact: find the line with an email/phone, and the location/links line.
    contact_lines = [h for h in header[1:]]
    if contact_lines:
        cv.contact_email_phone = contact_lines[0]
    if len(contact_lines) > 1:
        cv.contact_location_links = " ".join(contact_lines[1:])

    # --- Sections ---
    current_key: str | None = None
    buffer: list[str] = []
    sections: dict[str, list[str]] = {}
    section_title_text: dict[str, str] = {}

    def flush():
        if current_key is not None:
            sections.setdefault(current_key, []).extend(buffer)

    while i < n:
        line = lines[i]
        if line.startswith("## "):
            flush()
            buffer = []
            raw_title = _strip_md(line[3:])
            key = SECTION_ALIASES.get(raw_title.lower())
            current_key = key
            if key:
                section_title_text[key] = raw_title.upper()
        else:
            if current_key is not None:
                buffer.append(line)
        i += 1
    flush()

    cv.section_titles = section_title_text

    # Summary
    cv.summary = _join_paragraph(sections.get("SUMMARY", []))

    # Experience
    cv.experiences = _parse_experiences(sections.get("EXPERIENCE", []))

    # Education
    cv.education = _parse_education(sections.get("EDUCATION", []))

    # Skills
    cv.skills = _parse_skills(sections.get("SKILLS", []))

    # Competencies
    cv.competencies = _join_paragraph(sections.get("COMPETENCIES", []))

    # Achievements
    cv.achievements = _parse_bullets(sections.get("ACHIEVEMENTS", []))

    # Additional activities
    cv.additional_activities = _join_paragraph(sections.get("ADDITIONAL", []))

    return cv


def _join_paragraph(block: list[str]) -> str:
    text = " ".join(l.strip() for l in block if l.strip())
    return _strip_md(text)


def _parse_bullets(block: list[str]) -> list[str]:
    bullets = []
    for l in block:
        s = l.strip()
        if s.startswith("- ") or s.startswith("* "):
            bullets.append(_strip_md(s[2:]))
    return bullets


def _parse_experiences(block: list[str]) -> list[Experience]:
    exps: list[Experience] = []
    current: Experience | None = None
    pending_title = None
    for raw in block:
        s = raw.strip()
        if not s:
            continue
        if s.startswith("### "):
            if current is not None:
                exps.append(current)
            heading = _strip_md(s[4:])
            # "Title | Company" — split on the first pipe.
            if "|" in heading:
                title, company = heading.split("|", 1)
                current = Experience(
                    title=title.strip(), company=company.strip(), dates=""
                )
            else:
                current = Experience(title=heading, company="", dates="")
            pending_title = False
        elif s.startswith("- ") or s.startswith("* "):
            if current is not None:
                current.bullets.append(_strip_md(s[2:]))
        else:
            # First non-bullet, non-heading line after a title is the date line.
            if current is not None and not current.dates:
                current.dates = _strip_md(s)
    if current is not None:
        exps.append(current)
    return exps


def _parse_education(block: list[str]) -> list[tuple[str, str]]:
    edu: list[tuple[str, str]] = []
    for raw in block:
        s = raw.strip()
        if not s:
            continue
        s = _strip_md(s)
        if "|" in s:
            degree, detail = s.split("|", 1)
            edu.append((degree.strip(), detail.strip()))
        else:
            edu.append((s, ""))
    return edu


def _parse_skills(block: list[str]) -> list[tuple[str, str]]:
    skills: list[tuple[str, str]] = []
    for raw in block:
        s = raw.strip()
        if not (s.startswith("- ") or s.startswith("* ")):
            continue
        s = s[2:]
        # "**Label:** value" or "Label: value"
        s_clean = s.replace("**", "")
        if ":" in s_clean:
            label, value = s_clean.split(":", 1)
            skills.append((label.strip(), value.strip()))
        else:
            skills.append((s_clean.strip(), ""))
    return skills


# --------------------------------------------------------------------------
# Template expansion
# --------------------------------------------------------------------------


def _xml(text: str) -> str:
    """Escape text for inclusion inside a <w:t> element."""
    return escape(text, quote=False)


def _expand_block(xml: str, tag: str, items: list, render) -> str:
    """Replace a <!--REPEAT:tag-->...<!--END:tag--> block with rendered items."""
    pattern = re.compile(
        r"<!--REPEAT:" + re.escape(tag) + r"-->(.*?)<!--END:" + re.escape(tag) + r"-->",
        re.DOTALL,
    )
    m = pattern.search(xml)
    if not m:
        raise ValueError(f"Repeat block not found: {tag}")
    block_template = m.group(1)
    rendered = "".join(render(block_template, item) for item in items)
    return xml[: m.start()] + rendered + xml[m.end() :]


def fill_template(document_xml: str, cv: CVData) -> str:
    xml = document_xml

    # Expand EXPERIENCE (with nested EXP_BULLET) first.
    def render_experience(block: str, exp: Experience) -> str:
        inner = _expand_block(
            block,
            "EXP_BULLET",
            exp.bullets,
            lambda b, bullet: b.replace("{{EXP_BULLET}}", _xml(bullet)),
        )
        inner = inner.replace("{{EXP_TITLE}}", _xml(exp.title))
        inner = inner.replace("{{EXP_COMPANY}}", _xml(exp.company))
        inner = inner.replace("{{EXP_DATES}}", _xml(exp.dates))
        return inner

    xml = _expand_block(xml, "EXPERIENCE", cv.experiences, render_experience)

    xml = _expand_block(
        xml,
        "EDUCATION",
        cv.education,
        lambda b, e: b.replace("{{EDU_DEGREE}}", _xml(e[0])).replace(
            "{{EDU_DETAIL}}", _xml(e[1])
        ),
    )
    xml = _expand_block(
        xml,
        "SKILL",
        cv.skills,
        lambda b, s: b.replace("{{SKILL_LABEL}}", _xml(s[0])).replace(
            "{{SKILL_VALUE}}", _xml(s[1])
        ),
    )
    xml = _expand_block(
        xml,
        "ACHIEVEMENT",
        cv.achievements,
        lambda b, a: b.replace("{{ACHIEVEMENT}}", _xml(a)),
    )

    # Static tokens.
    replacements = {
        "{{FULL_NAME}}": cv.full_name,
        "{{HEADLINE}}": cv.headline,
        "{{CONTACT_EMAIL_PHONE}}": cv.contact_email_phone,
        "{{CONTACT_LOCATION_LINKS}}": cv.contact_location_links,
        "{{SUMMARY}}": cv.summary,
        "{{COMPETENCIES}}": cv.competencies,
        "{{ADDITIONAL_ACTIVITIES}}": cv.additional_activities,
        "{{SECTION_SUMMARY}}": cv.section_titles.get("SUMMARY", "PROFESSIONAL SUMMARY"),
        "{{SECTION_EXPERIENCE}}": cv.section_titles.get(
            "EXPERIENCE", "PROFESSIONAL EXPERIENCE"
        ),
        "{{SECTION_EDUCATION}}": cv.section_titles.get("EDUCATION", "EDUCATION"),
        "{{SECTION_SKILLS}}": cv.section_titles.get("SKILLS", "TECHNICAL SKILLS"),
        "{{SECTION_COMPETENCIES}}": cv.section_titles.get(
            "COMPETENCIES", "CORE COMPETENCIES"
        ),
        "{{SECTION_ACHIEVEMENTS}}": cv.section_titles.get(
            "ACHIEVEMENTS", "ACHIEVEMENTS & RECOGNITION"
        ),
        "{{SECTION_ADDITIONAL}}": cv.section_titles.get(
            "ADDITIONAL", "ADDITIONAL ACTIVITIES"
        ),
    }
    for token, value in replacements.items():
        xml = xml.replace(token, _xml(value))

    return xml


# --------------------------------------------------------------------------
# Packaging
# --------------------------------------------------------------------------


def _find_media_part(names: list[str]) -> str | None:
    """Return the single embedded image part in a template, if any."""
    media = [n for n in names if n.startswith("word/media/")]
    if not media:
        return None
    return media[0]


def write_docx(
    template_docx: Path,
    filled_document_xml: str,
    out_path: Path,
    photo: Path | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(template_docx, "r") as zin:
        names = zin.namelist()
        media_part = _find_media_part(names) if photo is not None else None
        photo_bytes = photo.read_bytes() if (photo is not None and media_part) else None
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in names:
                data = zin.read(item)
                if item == "word/document.xml":
                    data = filled_document_xml.encode("utf-8")
                elif item == media_part and photo_bytes is not None:
                    # Reuse the template's media name so rels and content types
                    # stay valid; Word reads the real format from the bytes.
                    data = photo_bytes
                zout.writestr(item, data)


def verify(filled_xml: str) -> list[str]:
    problems = []
    leftover_tokens = re.findall(r"\{\{[A-Z_]+\}\}", filled_xml)
    if leftover_tokens:
        problems.append(f"Unreplaced tokens: {sorted(set(leftover_tokens))}")
    leftover_sentinels = re.findall(r"<!--(REPEAT|END):[A-Z_]+-->", filled_xml)
    if leftover_sentinels:
        problems.append(f"Unexpanded sentinels remain: {len(leftover_sentinels)}")
    return problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Generate a styled CV .docx from canonical markdown."
    )
    ap.add_argument(
        "--cv",
        required=True,
        type=Path,
        help="Path to the canonical CV markdown (cv.md / cv_es.md).",
    )
    ap.add_argument(
        "--template",
        required=True,
        type=Path,
        help="Path to the tokenized .template.docx.",
    )
    ap.add_argument("--out", required=True, type=Path, help="Output .docx path.")
    ap.add_argument(
        "--photo",
        type=Path,
        default=None,
        help="Header photo to embed (templates that carry one, e.g. 'general'). "
        "Ignored for templates without an embedded image.",
    )
    args = ap.parse_args(argv)

    if not args.cv.is_file():
        print(f"ERROR: CV source not found: {args.cv}", file=sys.stderr)
        return 2
    if not args.template.is_file():
        print(f"ERROR: template not found: {args.template}", file=sys.stderr)
        return 2
    if args.photo is not None and not args.photo.is_file():
        print(f"ERROR: photo not found: {args.photo}", file=sys.stderr)
        return 2

    cv = parse_cv(args.cv)

    with zipfile.ZipFile(args.template, "r") as z:
        document_xml = z.read("word/document.xml").decode("utf-8")

    filled = fill_template(document_xml, cv)

    problems = verify(filled)
    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        return 3

    # Report whether the chosen photo will actually be embedded.
    photo_note = ""
    if args.photo is not None:
        with zipfile.ZipFile(args.template, "r") as z:
            media_part = _find_media_part(z.namelist())
        if media_part:
            photo_note = f"\n  photo: {args.photo} -> {media_part}"
        else:
            print(
                f"WARNING: --photo given but template has no embedded image; "
                f"ignoring {args.photo}",
                file=sys.stderr,
            )

    write_docx(args.template, filled, args.out, photo=args.photo)

    print(
        "OK: generated {out}\n"
        "  name: {name}\n"
        "  experiences: {exp} (bullets: {bul})\n"
        "  education: {edu} | skills: {sk} | achievements: {ach}{photo}".format(
            out=args.out,
            name=cv.full_name,
            exp=len(cv.experiences),
            bul=sum(len(e.bullets) for e in cv.experiences),
            edu=len(cv.education),
            sk=len(cv.skills),
            ach=len(cv.achievements),
            photo=photo_note,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
