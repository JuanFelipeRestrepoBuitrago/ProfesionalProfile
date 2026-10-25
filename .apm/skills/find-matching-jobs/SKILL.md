---
name: find-matching-jobs
description: Search LinkedIn for jobs compatible with the user's canonical CV and their captured job preferences, then rank the matches and write them to results/jobs.md. Uses the read-only linkedin MCP (search_jobs, get_job_details, get_job_apply_url). Use whenever the user wants to find, look for, or discover jobs that fit their profile. Always checks for job_preferences.md (project root) first; if it is missing, invokes the job-preferences skill to generate it before searching.
---

# Find jobs matching the CV and preferences

Query LinkedIn for current openings that fit the user's professional profile and
stated preferences, score each against the CV, and produce a ranked shortlist in
`results/jobs.md`. The linkedin MCP is read-only: this skill never applies to a
job, it only finds and reports them.

## Hard constraint: LinkedIn is read-only

The `@linkedin` MCP exposes query tools only (`search_jobs`, `get_job_details`,
`get_job_apply_url`, `get_saved_jobs`). Never claim to have applied to or saved a
job. The only artifact this skill produces is `results/jobs.md`. Application is
always a manual step the user performs via the apply URL.

## Sources of truth

- `cv.md` (English) / `cv_es.md` (Spanish) — the authoritative professional
  record used to form search keywords and to score compatibility. Never invent
  skills or experience the CV does not contain.
- `job_preferences.md` (project root) — the search filters and ranking
  preferences. It must exist before searching: if it is missing, invoke the
  `job-preferences` skill to generate it first (see step 1).

## Steps

1. **Ensure preferences exist, then load inputs.** Before anything else, check
   for `job_preferences.md` at the project root. If it is missing, invoke the
   `job-preferences` skill to generate it, then continue once it exists. Read the
   CV and `job_preferences.md`, and extract the LinkedIn filters and the ranking
   preferences.
2. **Inspect the MCP tools** before calling them, then **search**. Call
   `search_jobs` with the preference-derived parameters:
   `keywords`, `location`, `work_type` (remote/hybrid/on_site), `job_type`,
   `experience_level`, `date_posted`, `easy_apply`, and `sort_by`. Run multiple
   searches when the user has several target roles or keyword sets; de-duplicate
   by `job_id`.
    - If the MCP cannot authenticate or returns nothing, report that and ask how
      to proceed instead of fabricating listings.
3. **Fetch details.** For the most relevant candidates, call `get_job_details`
   (and `get_job_apply_url` for the application link and apply method). Do not
   fabricate any field the MCP did not return.
4. **Score compatibility against the CV.** For each job, assess fit using:
    - Overlap between required/preferred skills and the CV skills and experience.
    - Seniority alignment (do not treat tech exposure as professional expertise;
      do not inflate the user's level).
    - Work type, location, and job type versus the user's preferences.
    - Must-have vs nice-to-have technologies and any deal-breakers from the
      preferences (a deal-breaker match disqualifies or heavily downranks a job).
    - Language-of-work versus the user's stated proficiency.
      Assign each job a match level (e.g. Strong / Moderate / Weak) with a one-line
      rationale grounded in the CV and preferences. Break ties using the user's top
      priorities.
5. **Write `results/jobs.md`.** Create `results/` if needed. Overwrite the file
   on each run (it is a derived shortlist, not canonical). Structure it as:
    - A header with the run date, the search filters used, and how many jobs were
      found vs reported.
    - A ranked list (strongest match first). For each job include: title, company,
      location, work type, job type, match level + rationale, key matching skills,
      any notable gaps or deal-breaker flags, the LinkedIn posting link, and the
      apply URL / apply method from `get_job_apply_url`.
    - A short **Excluded / deal-breaker** section listing jobs filtered out and
      why, so the user sees what was dropped.
    - A closing reminder that applications are manual (read-only MCP).

## Validation

- Confirm `results/jobs.md` was written and opens correctly.
- Verify every listed job traces to a real `search_jobs` / `get_job_details`
  result — no fabricated postings, companies, or links.
- Confirm match rationales reference actual CV facts and stated preferences, and
  that no deal-breaker job is ranked as a strong match.
- Report: number of jobs found and reported, the filters applied, the top
  matches, and the reminder that the user applies manually.
