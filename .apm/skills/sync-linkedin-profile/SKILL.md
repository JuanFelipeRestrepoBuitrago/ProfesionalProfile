---
name: sync-linkedin-profile
description: Query the full LinkedIn profile via the read-only linkedin MCP and produce an updated, professionally written LinkedIn version derived from the canonical CVs. Because the linkedin MCP has NO editing tools, the deliverable is a Markdown file under results/ that the user applies to LinkedIn manually. Use whenever the user wants to review, refresh, or align their LinkedIn profile with their CV.
---

# Sync LinkedIn profile from the canonical CVs

Read the user's current LinkedIn profile, compare it against the canonical CV
source files, and generate professionally written replacement content for every
LinkedIn section. The output is a Markdown handoff file the user copies into
LinkedIn by hand.

## Hard constraint: LinkedIn is read-only

The `@linkedin` MCP exposes query tools only — it has NO write, edit, or publish
capability. Never claim to have changed LinkedIn. The only artifact this skill
produces is a Markdown file in `results/`. Tell the user explicitly that they
must apply the changes themselves.

## Sources of truth

- `cv.md` (English) and `cv_es.md` (Spanish) are the authoritative professional
  record. All generated LinkedIn content derives from them.
- The LinkedIn profile is the current external state to query and compare.
- Never invent employment, achievements, metrics, degrees, certifications, or
  skills. Only use verified facts present in the canonical CVs or explicitly
  provided by the user.

## Steps

1. **Confirm output language.** LinkedIn is usually a single-language profile.
   Ask which language the deliverable should be in (default: English from
   `cv.md`) unless the user already stated it.
2. **Read the canonical CVs.** Read `cv.md` and `cv_es.md` to load the verified
   facts, roles, dates, and credentials. Use the file matching the chosen output
   language as the content base.
3. **Query the current LinkedIn profile.** Use the `@linkedin` MCP read tools
   (e.g. `get_my_profile`, and `get_person_profile` if a specific profile is
   needed). Inspect the available tools before calling them. Capture every
   section the MCP returns: headline, about/summary, experience entries,
   education, skills, certifications, location, and contact detail.
   - If the MCP cannot authenticate or returns nothing, report that and ask how
     to proceed instead of fabricating current profile content.
4. **Compare and diagnose.** For each section, note what is missing, outdated,
   weaker than the CV, or inconsistent with the canonical facts. Keep verified
   employers, titles, and dates intact.
5. **Write professional replacement content.** Produce improved, recruiter-grade
   content for each section, grounded in the CV:
   - Headline — concise, keyword-aware, role + specialization.
   - About / summary — first-person, achievement-oriented, no fabricated metrics.
   - Experience — per role, aligned titles/dates, strong accurate bullets.
   - Skills, certifications, education — matched to the canonical CV.
   LinkedIn tone may differ from the CV (more narrative, more keywords) but every
   fact must trace back to the canonical source.
6. **Write the deliverable** to `results/linkedin.md` (or
   `results/linkedin_es.md` for a Spanish profile). Create `results/` if it does
   not exist. Structure it as an editing handoff:
   - One section per LinkedIn field, with a clear heading.
   - For each section show the **Current** value (from the query) and the
     **Proposed** value, so the user sees exactly what to change.
   - A short "Pending / needs user decision" list for anything ambiguous.
   - A note at the top stating LinkedIn must be updated manually because the MCP
     is read-only.

## Validation

- Confirm the `results/linkedin*.md` file was written and opens correctly.
- Verify every proposed value traces to a verified fact in the canonical CVs.
- Confirm no fabricated roles, metrics, or credentials were introduced.
- Report: sections changed, items needing user decision, and the explicit
  reminder that the user applies the changes on LinkedIn themselves.
