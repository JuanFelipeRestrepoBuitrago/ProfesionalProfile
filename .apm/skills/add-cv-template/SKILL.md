---
name: add-cv-template
description: Turn a styled .docx the user drops into cv_formats/ into a reusable, generator-ready CV template. Tokenizes the document's text while preserving every font, color, border, image, and style, wires it into the generate-cv-document generator, and verifies it round-trips. Use whenever the user adds a new CV design (a new .docx in cv_formats/) and wants it available as a format the CV generator can fill from cv.md / cv_es.md.
---

# Add a CV template from a .docx

The user designs a CV layout in Word and drops the `.docx` into `cv_formats/`.
This skill converts that styled document into a **tokenized template** that the
`generate-cv-document` generator (`scripts/generate_cv.py`) can fill from the
canonical sources — preserving the design's exact fonts, colors, borders,
images, and spacing. The result is a new `<format>` the generate skill can use
for any language.

This is the authoring counterpart to `generate-cv-document`: this skill *creates*
a template; that skill *fills* it.

## Inputs

1. **source .docx** — a file in `cv_formats/` (e.g. `cv_formats/modern.docx`).
   The format name is the file stem (`modern`).
2. **confirm the design is final** — tokenizing bakes in the structure, so the
   user should be happy with the layout first.

If the file is not in `cv_formats/`, ask the user to place it there (per the
project structure rules, `cv_formats/` holds format definitions).

## Key principle

Content comes from `cv.md` / `cv_es.md` at generation time. The source `.docx`
is a **layout reference only** — its text is replaced with tokens. Never treat
the sample's words as canonical; only its styling matters.

## The target template contract

The generator expects these tokens and repeat sentinels (same vocabulary as the
existing `ats` / `general` templates). Reproduce whichever the design contains:

Static tokens (one occurrence each): `{{FULL_NAME}}`, `{{HEADLINE}}`,
`{{CONTACT_EMAIL_PHONE}}`, `{{CONTACT_LOCATION_LINKS}}`, `{{SUMMARY}}`,
`{{COMPETENCIES}}`, `{{ADDITIONAL_ACTIVITIES}}`, and the section-heading tokens
`{{SECTION_SUMMARY}}`, `{{SECTION_EXPERIENCE}}`, `{{SECTION_EDUCATION}}`,
`{{SECTION_SKILLS}}`, `{{SECTION_COMPETENCIES}}`, `{{SECTION_ACHIEVEMENTS}}`,
`{{SECTION_ADDITIONAL}}`.

Repeatable blocks, each wrapped in XML comment sentinels and containing exactly
**one** styled example in the source:
- `<!--REPEAT:EXPERIENCE-->` … `<!--END:EXPERIENCE-->` with `{{EXP_TITLE}}`,
  `{{EXP_COMPANY}}`, `{{EXP_DATES}}`, and a nested
  `<!--REPEAT:EXP_BULLET-->` … `<!--END:EXP_BULLET-->` holding `{{EXP_BULLET}}`.
- `<!--REPEAT:EDUCATION-->` … `<!--END:EDUCATION-->` with `{{EDU_DEGREE}}`,
  `{{EDU_DETAIL}}`.
- `<!--REPEAT:SKILL-->` … `<!--END:SKILL-->` with `{{SKILL_LABEL}}`,
  `{{SKILL_VALUE}}`.
- `<!--REPEAT:ACHIEVEMENT-->` … `<!--END:ACHIEVEMENT-->` with `{{ACHIEVEMENT}}`.

Rules that keep it fillable:
- Each token must sit inside a single `<w:r>`/`<w:t>` run so its styling is
  self-contained. Keep `{{EXP_TITLE}}` and `{{EXP_COMPANY}}` as separate runs if
  they have different colors.
- A REPEAT block must contain exactly one example item in the template; the
  generator clones it per entry in the CV.
- The XML comment sentinels go *between* `<w:p>` paragraphs (or between the
  title/date paragraphs and the bullet paragraphs), never inside a run.

## Steps

1. **Confirm inputs**: the source filename in `cv_formats/` and the format name
   (file stem). Refuse names that collide with an existing template unless the
   user wants to replace it.

2. **Study the design**: extract the document with the `document-loader` MCP
   (`read_document`, `file_type:"docx"`) to see section order and content. Then
   extract the raw XML to see the exact styling:
   ```bash
   mkdir -p /tmp/tpl_<format> && \
   unzip -o cv_formats/<format>.docx -d /tmp/tpl_<format> >/dev/null && \
   cat /tmp/tpl_<format>/word/document.xml
   ```
   Read `word/document.xml`. Identify the header block, each section heading,
   and one representative experience entry (title paragraph, date paragraph,
   bullet paragraph) to use as the repeat example.

3. **Author the tokenized XML**: create
   `.kiro/skills/generate-cv-document/templates/<format>/document.xml` as a copy
   of the source `document.xml` with:
   - header/summary/competencies/additional text replaced by the static tokens;
   - section heading text replaced by `{{SECTION_*}}` tokens;
   - the repeatable regions reduced to ONE example each, wrapped in the REPEAT
     sentinels, with inner text replaced by the item tokens;
   - everything else (styles, borders, tables, drawings/images, `sectPr`,
     `rFonts`, `color`, `sz`, spacing) left byte-for-byte intact.
   Preserve the exact `w:rPr`/`w:pPr` of each run/paragraph; only change `<w:t>`
   text and insert the comment sentinels.

4. **Package the template** by copying the ORIGINAL `.docx` entry-by-entry and
   swapping only `word/document.xml` — this keeps `styles.xml`, the footer,
   `customXml/*`, and any `media/` image. Do NOT rebuild from a subset of zip
   entries (that drops referenced parts and corrupts the file):
   ```python
   import zipfile
   from pathlib import Path
   fmt = "<format>"
   src = Path(f"cv_formats/{fmt}.docx")
   doc = Path(f".kiro/skills/generate-cv-document/templates/{fmt}/document.xml").read_text("utf-8")
   out = Path(f".kiro/skills/generate-cv-document/templates/{fmt}.template.docx")
   with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
       for info in zin.infolist():
           data = zin.read(info.filename)
           if info.filename == "word/document.xml":
               data = doc.encode("utf-8")
           zout.writestr(info, data)
   ```

5. **Extend the parser only if needed**: if the design introduces a section the
   generator doesn't know, add its heading text (English and Spanish) to
   `SECTION_ALIASES` and handle it in `scripts/generate_cv.py`, and add matching
   tokens to the template. For standard CV sections, no code change is needed.

6. **Register the format**: add the new format name to the `generate-cv-document`
   SKILL.md format list so users know it exists.

## Verification (always)

- Run the generator against the new template for BOTH languages:
  ```bash
  python3 .kiro/skills/generate-cv-document/scripts/generate_cv.py \
    --cv cv.md    --template .kiro/skills/generate-cv-document/templates/<format>.template.docx --out /tmp/<format>_en.docx
  python3 .kiro/skills/generate-cv-document/scripts/generate_cv.py \
    --cv cv_es.md --template .kiro/skills/generate-cv-document/templates/<format>.template.docx --out /tmp/<format>_es.docx
  ```
  A non-zero exit means a leftover `{{TOKEN}}` or unexpanded REPEAT/END sentinel
  — fix the tokenized XML until it exits 0 and prints sensible counts
  (experiences, bullets, skills, etc.).
- Inspect a generated `.docx` with the `office-mcp` tools:
  - `word_get_info` — confirm it opens and the table/image counts match the
    design's intent (e.g. a photo design should report `images: 1`).
  - `word_list_paragraphs` — confirm the design's run styling (fonts, colors,
    sizes) survived on the filled content, and that job/bullet counts match the
    source.
- Only after a clean round-trip, tell the user the format is ready and can be
  used with the generate-cv-document skill (`word` by default, `pdf` on request).

## Rules

- Never modify the canonical `cv.md` / `cv_es.md`. This skill only reads them
  for verification.
- Never alter the user's original `cv_formats/<format>.docx`; it stays the
  untouched design reference. The tokenized copy lives under
  `.kiro/skills/generate-cv-document/templates/`.
- Preserve the design's styling exactly; change only text and insert sentinels.
- If the design can't be expressed with the existing token/sentinel vocabulary,
  explain the gap and propose the minimal parser/token extension before
  proceeding.
