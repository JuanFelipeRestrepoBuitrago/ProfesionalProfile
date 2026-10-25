---
name: document-to-markdown
description: Convert a PDF or Word (DOCX/DOC) CV into a structured Markdown document using the document-loader MCP. Use when the user provides a PDF or Word CV that needs to become a Markdown source file, or asks to extract a document into Markdown.
---

# Convert PDF/DOCX CV to Markdown

Transform a PDF or Word CV into a clean, structured Markdown document suitable
for version control, using the `document-loader` MCP for extraction.

## When to use

- The user provides a `.pdf`, `.docx`, or `.doc` CV and wants it as Markdown.
- You need to turn an existing binary CV into a canonical `cv.md` / `cv_es.md`
  source, or into any Markdown record.

## Steps

1. Confirm the source file path and its type (`pdf`, `docx`, or `doc`).
2. Extract the content with the `document-loader` MCP `read_document` tool,
   passing `file_path` and the matching `file_type`. Do not use shell tools
   (`cat`, `pdftotext`) for this.
   - For a scanned/image-only PDF, `read_document` may return little or no text.
     If so, tell the user and ask how to proceed instead of guessing content.
3. Structure the extracted text into Markdown, preserving faithfully:
   - Section hierarchy and headings.
   - Bullet points and lists.
   - Employers, job titles, and employment dates.
   - Links, certifications, and education details.
4. This is a format-only conversion. Do not rewrite, embellish, or invent facts.
   Keep extracted content faithful. If you also propose editorial improvements,
   present them separately and clearly marked, not mixed into the extraction.
5. Confirm the target Markdown path with the user before writing. If it will
   become a canonical file (`cv.md` / `cv_es.md`), follow the canonical CV
   steering and keep the language correct for the target file.

## Validation

- Verify the Markdown file was written and opens correctly.
- Spot-check that key sections (experience, education, skills, dates, links)
  are present and match the source.
- Report anything that could not be extracted cleanly (e.g., tables, columns,
  scanned regions) rather than silently dropping it.
