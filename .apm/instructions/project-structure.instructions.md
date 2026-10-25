---
applyTo: '**'
---

# Project structure

This repository is the long-term workspace for the user's career documents.

## Layout

- `cv.md`, `cv_es.md` (root) — canonical CV source files (English / Spanish).
  See the canonical CV steering for their rules.
- `formats/` — format definitions and templates for each CV variant to be
  generated (layout, styling, structure conventions for the output documents).
- `results/` — generated and tailored CV outputs. Each tailored CV produced for
  a specific job description is stored here, kept separate from the canonical
  source so the source of truth stays clean.

## Conventions

- Generate derived outputs (PDF, DOCX, tailored versions) from the canonical
  source files; do not hand-edit multiple independent copies.
- Store job-description-tailored CVs under `results/`, never overwriting the
  canonical root files.
- Preserve existing conventions and avoid creating unnecessary duplicate files.
- Create `formats/` and `results/` on first use if they do not yet exist.
