---
name: update-canonical-cv
description: Update the canonical CV source files (cv.md in English and cv_es.md in Spanish) with new details the user provides. Use whenever the user adds, changes, or corrects professional information (new role, project, skill, certification, education, contact detail) that belongs in the CV. Always updates BOTH language files.
---

# Update the canonical CV (both languages)

Apply user-provided professional details to the two canonical CV source files,
keeping them synchronized and each in its correct language.

## Canonical files

- `cv.md` — English.
- `cv_es.md` — Spanish.

## Core rule

Every verified detail the user provides must be applied to BOTH files:

- `cv.md` in English.
- `cv_es.md` in Spanish (equivalent content, naturally translated — never a
  mechanical word-for-word translation that distorts meaning).

Keep structure, section order, and headings consistent across both files.

## Steps

1. Read both `cv.md` and `cv_es.md` to understand current content and structure.
   If a file does not exist yet, create it following the structure of its pair
   (or a standard CV structure if neither exists).
2. Identify exactly what the user is adding, changing, or correcting, and which
   section(s) it belongs in. Treat the input as verified facts; do not invent
   surrounding details, metrics, or embellishments.
3. Preserve the distinction between current and previous roles, and keep
   employers, titles, dates, and credentials factually intact.
4. Apply the change to `cv.md` in English and the equivalent change to
   `cv_es.md` in Spanish. Make the smallest complete edit; do not reflow or
   rewrite unrelated sections.
5. If a detail is ambiguous or the language choice materially affects wording,
   ask a concise clarifying question before writing.

## Validation

- Confirm both files were updated with equivalent content.
- Verify section order and headings still match between the two files.
- Report what changed in each file and flag any item that needs user
  confirmation.
