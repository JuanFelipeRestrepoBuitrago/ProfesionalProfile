---
name: generate-cv-document
description: Generate a CV document from the canonical CV sources (cv.md / cv_es.md) in a chosen language, visual format, and output extension (Word or PDF). Fills a styled .docx template with a block-repetition generator so the exact fonts, colors, and layout of cv_formats/ are preserved, regardless of how many jobs, bullets, or skills the CV has. Use whenever the user asks to produce, export, or render a CV file — for example "make my English CV in the ATS format" or "export my Spanish CV as Word in the general format".
---

# Generate a CV document (language + format + extension)

Produce a polished CV from the canonical Markdown sources while preserving the
exact look of the chosen `cv_formats/` design (fonts, colors, borders, spacing,
photo). The skill fills a **tokenized `.docx` template** with a generator script
that clones one styled example per repeatable section, so the CV can grow to any
number of jobs/bullets/skills without editing the template.

Output is a `.docx` by default. PDF is produced only on request, by converting
the generated `.docx` with the `office-mcp` server (LibreOffice).

## Why this approach (do not regress to it)

The `office-mcp` Word _authoring_ tools (`word_create_document`,
`word_add_paragraph`, `word_add_heading`) can only emit paragraphs in the
default template styles — they cannot set run color/font/size, paragraph
borders, or hanging indents. Building a CV from scratch with them will **never**
match the hand-crafted `cv_formats/*.docx`. `word_find_replace` preserves run
formatting but cannot add or remove paragraphs, so it cannot handle a variable
number of jobs/bullets.

The working design is: a styled template whose repeatable blocks are marked with
XML comment sentinels, filled by `scripts/generate_cv.py`, which splices the
`word/document.xml` directly and preserves every style. `office-mcp` is used
only for the optional final PDF conversion and for verification.

## Inputs (resolve all three before generating)

1. **language** — which canonical source to use:
    - `en` / English → `cv.md`
    - `es` / Spanish → `cv_es.md`
2. **format** — the visual variant, matching `cv_formats/`:
    - `ats` → single column, parser-friendly, no tables/photo.
    - `general` → richer layout with a header table and photo (swappable, see
      "photo" below).
    - Any other format that has a packaged template under `templates/` (add new
      designs from a `.docx` with the `add-cv-template` skill).
    - For an unknown name, map it to the closest existing template or ask.
3. **extension** — the output file type:
    - `word` / `docx` → `.docx` (default).
    - `pdf` → convert the generated `.docx` to `.pdf`.
4. **photo** (only for formats that embed one, e.g. `general`) — the header
   picture, taken from the `resources/` folder:
    - Default: `resources/DEFAULT.jpg` when the user names no photo.
    - Otherwise use the file the user names inside `resources/` (e.g. "use
      `headshot.jpg`" → `resources/headshot.jpg`).
    - The generator stores the chosen image under the template's existing media
      name, so package relationships and content types stay valid; Word reads
      the real format from the bytes. A standard JPEG/PNG headshot works.
    - Formats without a photo (e.g. `ats`) ignore this input.

5. **source** (optional) — a derived CV Markdown to render instead of the
   canonical file, e.g. a job-tailored CV written by the `tailor-cv-for-job`
   skill under `results/applications/`. It must follow the canonical structure
   (see "How the canonical Markdown maps to fields"). When a source is given,
   its language comes from the caller, and the caller may also set the output
   path. Without a source, use the canonical file for the language.

If any input is missing or ambiguous, ask one concise question. Do not guess the
language. The photo input is not ambiguous: silently default to
`resources/DEFAULT.jpg` unless the user names another file.

## Files

- Canonical sources (content, verbatim): `cv.md`, `cv_es.md`.
- Format references (look & feel): `cv_formats/ats.docx`, `cv_formats/general.docx`.
- Tokenized templates (used by the generator):
  `<skill-dir>/templates/ats.template.docx`,
  `<skill-dir>/templates/general.template.docx`.
- Generator: `<skill-dir>/scripts/generate_cv.py`.
- Editable token source per format (for restyling the template):
  `<skill-dir>/templates/<format>/document.xml`.

`<skill-dir>` is this skill's own directory, wherever the agent harness
deployed it — `.kiro/skills/generate-cv-document/` under Kiro,
`.claude/skills/generate-cv-document/` under Claude Code,
`.agents/skills/generate-cv-document/` under Codex. Resolve it once from the
path of this `SKILL.md` and use it for every command below; never hardcode a
single harness's folder.

## Steps

1. Resolve language, format, extension, and (for photo formats) the photo file.
2. Run the generator with absolute paths:

    ```bash
    python3 <skill-dir>/scripts/generate_cv.py \
      --cv <cv.md|cv_es.md|derived source> \
      --template <skill-dir>/templates/<format>.template.docx \
      --out results/cv_<lang>_<format>.docx \
      --photo resources/<photo>      # photo formats only; omit for ats
    ```

    For a photo format, pass `--photo resources/DEFAULT.jpg` by default, or the
    file the user named. Omit `--photo` for formats without an embedded image
    (e.g. `ats`); if given there, the generator warns and ignores it.

    The script parses the canonical CV, expands every repeatable block from the
    real data, fills all tokens, swaps the header photo when `--photo` applies,
    and fails loudly (non-zero exit) if any token or repeat sentinel is left
    unresolved. It prints the parsed counts
    (experiences, bullets, education, skills, achievements) — sanity-check them
    against the source.

3. If the requested extension is `pdf`, convert the generated `.docx` with the
   `office-mcp` `word_export_pdf` tool (load it first). LibreOffice (`soffice`)
   must be available; if it is not, report that instead of claiming success.
   Keep the `.docx` as well.
4. Output path: `results/cv_<language>_<format>.<ext>` (e.g.
   `results/cv_en_ats.docx`, `results/cv_es_general.pdf`). For a derived source,
   use the output path the caller gives (default: next to the source, same
   stem, e.g. `results/applications/cv_en_ats_canals_junior-software-engineer.docx`).
   Create the folder if needed. Use absolute paths for `office-mcp` calls.

## Verification (always)

- The generator exits non-zero on any unreplaced `{{TOKEN}}` or leftover
  `REPEAT`/`END` sentinel — treat a non-zero exit as a hard failure.
- Confirm the output file exists in `results/` and is non-empty.
- Inspect the `.docx` with the `office-mcp` tools:
    - `word_get_info` — for `ats`, expect `tables: 0` and `images: 0`; for
      `general`, expect `tables: 1` and `images: 1` (header + photo). When a
      photo was swapped, confirm the embedded image matches the chosen file
      (e.g. compare byte sizes: the output's `word/media/image1.jpeg` should
      equal the `resources/` photo).
    - `word_list_paragraphs` — spot-check that styling survived: name in
      `Aptos Display` bold color `174B5B`; job titles bold `2B343F` + company
      `174B5B`; date lines italic `646F78`; bullet markers bold `174B5B`.
- Spot-check that all sections and every job/bullet from the source are present
  and that counts match the source.
- For PDF, confirm the `.pdf` was actually produced (not just that a tool
  returned). Optionally extract it with the `document-loader` MCP and compare.
- Report the final path(s), language, format, extension, and the counts. Never
  report success solely because a command returned.

## Updating a template's look (restyling)

The template's design lives in
`<skill-dir>/templates/<format>/document.xml` — the loose,
human-editable tokenized XML. To change colors, sizes, spacing, or the photo
size, edit that file, then repackage the `.docx` template by copying the
original `cv_formats/<format>.docx` and replacing only `word/document.xml`
(this preserves `styles.xml`, the footer, `customXml/*`, and media):

```python
import zipfile
from pathlib import Path
src = Path("cv_formats/<format>.docx")
doc = Path("<skill-dir>/templates/<format>/document.xml").read_text("utf-8")
out = Path("<skill-dir>/templates/<format>.template.docx")
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename == "word/document.xml":
            data = doc.encode("utf-8")
        zout.writestr(info, data)
```

Never build the template by selecting only some zip entries — that drops parts
the document references (e.g. `customXml/item1.xml`) and corrupts the package.

## Token & sentinel vocabulary (template authors)

Static tokens (single occurrence): `{{FULL_NAME}}`, `{{HEADLINE}}`,
`{{CONTACT_EMAIL_PHONE}}`, `{{CONTACT_LOCATION_LINKS}}`, `{{SUMMARY}}`,
`{{COMPETENCIES}}`, `{{ADDITIONAL_ACTIVITIES}}`, and section-heading tokens
`{{SECTION_SUMMARY}}`, `{{SECTION_EXPERIENCE}}`, `{{SECTION_EDUCATION}}`,
`{{SECTION_SKILLS}}`, `{{SECTION_COMPETENCIES}}`, `{{SECTION_ACHIEVEMENTS}}`,
`{{SECTION_ADDITIONAL}}` (heading text comes from the canonical CV, so Spanish
sources yield Spanish headings).

Repeatable blocks (`<!--REPEAT:X-->` … `<!--END:X-->`), cloned once per item:

- `EXPERIENCE` with inner tokens `{{EXP_TITLE}}`, `{{EXP_COMPANY}}`,
  `{{EXP_DATES}}`, and a nested `EXP_BULLET` block with `{{EXP_BULLET}}`.
- `EDUCATION` with `{{EDU_DEGREE}}`, `{{EDU_DETAIL}}`.
- `SKILL` with `{{SKILL_LABEL}}`, `{{SKILL_VALUE}}`.
- `ACHIEVEMENT` with `{{ACHIEVEMENT}}`.

Keep each token inside a single `<w:r>`/`<w:t>` run so its styling is
self-contained. Tokenize `{{EXP_TITLE}}` and `{{EXP_COMPANY}}` as separate runs
so each keeps its own color.

## How the canonical Markdown maps to fields

The generator expects the canonical CV structure already used by `cv.md` /
`cv_es.md`:

- `# Name` → `{{FULL_NAME}}`; the first non-empty header line → `{{HEADLINE}}`;
  the next header lines → contact tokens (Markdown links become `text: url`).
- `## <Section>` headings are matched by English **or** Spanish name.
- Under Experience, each `### Title | Company` starts a job; the first following
  non-bullet line is the date; `- ` lines are bullets.
- Skills `- **Label:** value` lines become `{{SKILL_LABEL}}` / `{{SKILL_VALUE}}`.
  If you add a new section or rename headings, update `SECTION_ALIASES` and the
  parser in `scripts/generate_cv.py`, and add matching tokens to the templates.

## Rules

- Content comes only from the canonical CV of the requested language, or from a
  derived source passed in explicitly (e.g. by `tailor-cv-for-job`), rendered
  as is. The format controls layout, never facts. Never translate; use the
  right language's file.
- Never overwrite the canonical `cv.md` / `cv_es.md` or the `cv_formats/`
  samples. Outputs go under `results/` only.
- The header photo for photo formats comes from `resources/`; default to
  `resources/DEFAULT.jpg` unless the user names another file there. Never embed
  a photo from outside `resources/`.
- Keep employers, titles, dates, credentials, and links factually intact and
  preserve the recruiter-grade phrasing already in the source.
- DOCX is the primary deliverable; produce PDF only when explicitly requested.
