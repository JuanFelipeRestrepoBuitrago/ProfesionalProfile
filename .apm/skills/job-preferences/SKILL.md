---
name: job-preferences
description: Interview the user about their job-search preferences (work type, location, seniority, job type, salary, keywords, and deal-breakers), grounding the questions in their canonical CV and the LinkedIn job-search filters the find-matching-jobs skill relies on. Produces or updates job_preferences.md (at the project root) as the single source of truth for job searches. Use whenever the user wants to define, review, or change what kind of jobs they are looking for, before searching for jobs.
---

# Capture job-search preferences

Ask the user a focused set of questions about what they are looking for in their
next role, informed by their canonical CV, and persist the answers to
`job_preferences.md` at the project root. This file is the input the
`find-matching-jobs` skill reads to search and rank jobs, so every question maps
to a real LinkedIn job-search filter or a ranking signal.

## Sources of truth

- `cv.md` (English) and `cv_es.md` (Spanish) — the authoritative professional
  record. Read them first to tailor the questions (seniority, stack, current
  location, languages) instead of asking what the CV already answers.
- `job_preferences.md` (project root) — the output of this skill. If it already
  exists, treat it as the current state to review and update, not to overwrite
  blindly.

## Filters to cover (map to LinkedIn `search_jobs`)

Ask about each of these. Infer a sensible default from the CV where possible and
offer it, so the user can confirm instead of starting from blank:

- **Keywords / roles** — target titles and specializations (e.g. "backend
  engineer", "software architect"). Suggest options from the CV summary and
  skills.
- **Work type** — `remote`, `hybrid`, `on_site` (one or more).
- **Location** — city/region/country, or "Remote". Default the user's current
  location from the CV when relevant.
- **Job type** — `full_time`, `part_time`, `contract`, `temporary`,
  `internship`, `other`.
- **Experience level** — `internship`, `entry`, `associate`, `mid_senior`,
  `director`, `executive`. Recommend a range consistent with the CV; do not
  inflate seniority.
- **Date posted** — how fresh postings must be (`past_hour`, `past_24_hours`,
  `past_week`, `past_month`) or no constraint.
- **Easy Apply only** — whether to restrict to LinkedIn Easy Apply.

## Ranking / soft preferences (beyond LinkedIn filters)

Also ask about preferences that shape ranking and filtering of results even
though they are not direct search filters:

- **Salary / compensation** expectations or minimum (and currency).
- **Must-have technologies** and **nice-to-have technologies**.
- **Deal-breakers** — things that disqualify a job (e.g. no remote, specific
  domains to avoid, required relocation, on-call, etc.).
- **Language-of-work** requirements (e.g. English, Spanish, Portuguese) and the
  user's proficiency per the CV.
- **Company preferences** — size, industry, or specific companies to prioritize
  or avoid.
- **Priorities** — the 2–3 factors that matter most, used to break ties when
  ranking jobs.

## Steps

1. **Read the CV.** Read `cv.md` (and `cv_es.md` if Spanish context helps) to
   derive defaults and avoid asking what is already known.
2. **Read existing preferences** if `job_preferences.md` (project root) exists,
   and present current values so the user edits rather than re-enters everything.
3. **Interview the user.** Ask the questions grouped as above. Batch related
   questions; propose CV-derived defaults and let the user confirm or change
   them. Keep it concise — do not interrogate one field at a time when several
   can be confirmed together.
4. **Confirm ambiguous or market-sensitive choices** (seniority, salary,
   relocation) before writing. Never invent a preference the user did not state.
5. **Write `job_preferences.md` at the project root.** Structure it so
   `find-matching-jobs` can consume it directly:
    - A **LinkedIn filters** section listing each `search_jobs` parameter with its
      chosen value (keywords, work_type, location, job_type, experience_level,
      date_posted, easy_apply).
    - A **Ranking preferences** section (salary, must-have / nice-to-have tech,
      deal-breakers, language-of-work, company preferences, top priorities).
    - A short **Notes** section for anything that needs future revisiting.

## Validation

- Confirm `job_preferences.md` (project root) was written and opens correctly.
- Verify every LinkedIn-filter value uses a valid option from the lists above
  (so searches do not fail).
- Confirm no preference was invented: each value is either stated by the user or
  a CV-derived default the user confirmed.
- Report: the chosen filters, the ranking preferences captured, and any item
  left pending for the user to decide later.
