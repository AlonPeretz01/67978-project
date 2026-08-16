# Clustering / AUDIT.md discrepancy — verification report

## Bottom line

**AUDIT.md is correct about the file it describes. The clustering output that quotes "43.4% feel somewhat connected" etc. did not run against that same file.** The master CSV on disk (`data/processed/harmonized_stack_overflow_2011_2025.csv`) is a **stale, gitignored build artifact** that predates the current version of `src/cleaning/data_harmonization.py`. The current harmonization code, run fresh, produces non-null 2025 values for `Part_of_community`, `Participates_in_questions`, and `Visits_SO_freq` — but the CSV sitting on disk was generated before that mapping existed (or before it was last regenerated) and was never rebuilt. `cluster_developers.py` reads that same stale CSV, so **running the clustering script today reproduces AUDIT.md's zeros, not the quoted cluster percentages** — the quoted numbers are not currently reproducible from this repository's clustering script + on-disk data.

## 1. Non-null counts, master CSV, Year == 2025

```
rows: 49123
Year                          49123
Age                           49123
Education_Level               48087
Years_of_Experience           43000
Employment_Status             48277
Yearly_Compensation           23928
Usage_Frequency                   0
AI_Tool_Usage                      0
AI_Usage_Status               33686
Has_SO_account                     0
Part_of_community                  0
Participates_in_questions          0
Visits_SO_freq                     0
experience_is_proxy           49123
```

This matches AUDIT.md's 2025 row exactly. AUDIT.md is an accurate description of `data/processed/harmonized_stack_overflow_2011_2025.csv` as it currently exists on disk.

## 2. What dataframe the clustering code consumes

`src/analysis/cluster_developers.py`, `__main__` block:

```python
df = pd.read_csv("data/processed/harmonized_stack_overflow_2011_2025.csv")
df = df[df["Year"] == 2025]
df = cluster_developers(df, n_clusters=5)
```

It reads **the exact same master CSV** used by AUDIT.md — not a separate cleaned annual file, not a raw file, and it builds nothing itself. Filtered to `Year == 2025` this loads **49,123 rows**, identical to AUDIT.md's row count. There is only one clustering entry point in the repo (no notebook, no second script) — `Glob` for `*cluster*` and `*kmodes*` across the repository returns only this file.

Since it reads the same stale file, running this script today produces clusters where `Usage_Frequency`, `AI_Tool_Usage`, `Has_SO_account`, `Part_of_community`, `Participates_in_questions`, and `Visits_SO_freq` are **100% "Missing"** for every 2025 respondent, in every cluster — never 43.4%, never 46.0%. The quoted cluster description could not have come from running this script against the file currently on disk.

## 3. Why the master CSV disagrees with current harmonization code

`src/cleaning/data_harmonization.py`'s `schema_mapping['2025']` **does** map source survey columns to all three of the columns in question:

```python
'2025': {
    'Age': 'Age',
    'Employment': 'Employment_Status',
    'EdLevel': 'Education_Level',
    'YearsCode': 'Years_of_Experience',
    'ConvertedCompYearly': 'Yearly_Compensation',
    'AISelect': 'AI_Usage_Status',
    'SOPartFreq': 'Participates_in_questions',
    'SOComm': 'Part_of_community',
    'SOVisitFreq': 'Visits_SO_freq',
}
```

There is no fillna/ffill/merge trick pulling in values from other years — `harmonize_schema` reads only same-year source columns (with a `bfill(axis=1)` across duplicate-target source columns, none of which apply here) and otherwise assigns `pd.NA`.

Calling `harmonize_schema()` directly, right now, against the current cleaned 2025 file (`data/clean/2025/survey_results_public_2025_cleaned.csv`) produces:

```
Part_of_community            31678 non-null   (17445 null)
Participates_in_questions    32200 non-null   (16923 null)
Visits_SO_freq                32680 non-null   (16443 null)
```

i.e. the mapping works correctly today and yields real, substantial coverage — nowhere close to the 0 found in the on-disk master CSV. This proves the master CSV predates this mapping (or predates its last edit) and was never regenerated after it changed. `data/processed/` is git-ignored (`.gitignore` excludes `data/`), so there is no commit history to pin the exact staleness date; the file's on-disk timestamp (2026-08-04) is older than the harmonization script's, consistent with this explanation.

Two columns remain genuinely absent from the 2025 mapping and are correctly 0 in any build, stale or fresh:
- `Usage_Frequency` — no 2025 mapping entry at all (this concept isn't asked the same way in 2025; see below).
- `Has_SO_account` — the raw 2025 column `SOAccount` exists and is populated (32,767 non-null of 49,123), but `schema_mapping['2025']` never maps it to `Has_SO_account`. This is a real, separate mapping gap in the current code (independent of the staleness issue above) — even a freshly rebuilt master CSV would still show 0 for `Has_SO_account` in 2025 until `'SOAccount': 'Has_SO_account'` is added to the mapping.
- `AI_Tool_Usage` — see below, the concept does not exist in the 2025 questionnaire.

## 4. Do these concepts exist in the raw 2025 survey?

Checked `data/clean/2025/survey_results_public_2025_cleaned.csv` (134 columns) directly:

| Concept | Column exists in 2025? | Column name | Non-null | Why not in master (fresh build) |
| --- | --- | --- | --- | --- |
| Part of SO community | Yes | `SOComm` | 31,678 / 49,123 | Mapped correctly; master is just stale |
| Participates in Q&A | Yes | `SOPartFreq` | 32,200 / 49,123 | Mapped correctly; master is just stale |
| Visits SO frequency | Yes | `SOVisitFreq` | 32,680 / 49,123 | Mapped correctly; master is just stale |
| Has SO account | Yes | `SOAccount` | 32,767 / 49,123 | **Column exists but is never mapped** — genuine gap in `schema_mapping['2025']` |
| AI tool usage ("currently using") | No | — (no `AIToolCurrently Using` equivalent; 2025's `AITool*` columns are phrased as `AIToolCurrently partially AI`, `AIToolCurrently mostly AI`, etc. — a differently-structured question, not a direct match) | — | Genuinely not asked in the same form in 2025; no 1:1 source column |
| Usage_Frequency (StackOverflowVisit-style, only used pre-2019) | No | — | — | This concept was superseded by `Visits_SO_freq`/`SOVisitFreq` starting 2019 and 2025 has no equivalent to the old `Usage_Frequency` question either |

So: `Part_of_community`, `Participates_in_questions`, and `Visits_SO_freq` questions **do exist** in the 2025 questionnaire and **are** correctly configured in the harmonization mapping — the master CSV is simply out of date. `Has_SO_account`'s source column also exists but was never added to the mapping. `AI_Tool_Usage` and `Usage_Frequency` have no matching 2025 question at all, so 0 is correct for those two regardless of staleness.

## 5. Which source is correct?

- **AUDIT.md is correct** — as a description of the file `data/processed/harmonized_stack_overflow_2011_2025.csv` currently on disk.
- **The clustering output/description quoted in the prompt is not reproducible** from the current repository: running `cluster_developers.py`'s own `__main__` block today, against the same file AUDIT.md describes, yields 100% "Missing" for `Part_of_community`, `Visits_SO_freq`, `Participates_in_questions`, `Usage_Frequency`, `AI_Tool_Usage`, and `Has_SO_account` in every 2025 cluster — it cannot produce figures like "43.4%" or "46.0%" for those columns. Whatever produced those percentages must have run against a differently-built (likely earlier, fresher) version of the master CSV than what's on disk now, since the harmonization mapping itself is capable of producing those values when run fresh (see §3).
- **Action needed (not taken — report only):** regenerate `data/processed/harmonized_stack_overflow_2011_2025.csv` by rerunning `src/cleaning/data_harmonization.py`, and add `'SOAccount': 'Has_SO_account'` to `schema_mapping['2025']` if `Has_SO_account` coverage for 2025 is desired.

## Additional items requested

**Number of clusters:** Hard-coded at **`n_clusters=5`** in `cluster_developers.py`'s `__main__` block (`cluster_developers(df, n_clusters=5)`). `cluster_developers()` itself takes `n_clusters` as a required parameter with no default.

**k-selection criterion:** **None.** No elbow method, silhouette score, or K-modes cost curve is computed anywhere in the repository (searched for `silhouette`, `elbow`, `inertia`, `cost` — no matches, and `cluster_developers()` has exactly one call site). `k=5` is a bare hard-coded constant with no supporting selection analysis.

**"Missing" as a K-modes category:** **Yes, explicitly.** `cluster_developers()` does `labeled.astype("string").fillna("Missing")` before handing the array to `KModes`, so `"Missing"` is passed in as a literal category value alongside real survey responses for every column — not dropped, not imputed statistically.

**Missing share per column in the clustering input** (master CSV, 2025 rows, as currently fed to `KModes`):

| Column | % Missing |
| --- | --- |
| Year | 0.0% |
| Age | 0.0% |
| Education_Level | 2.1% |
| Years_of_Experience | 12.5% |
| Employment_Status | 1.7% |
| Yearly_Compensation | 51.3% |
| Usage_Frequency | 100.0% |
| AI_Tool_Usage | 100.0% |
| AI_Usage_Status | 31.4% |
| Has_SO_account | 100.0% |
| Part_of_community | 100.0% |
| Participates_in_questions | 100.0% |
| Visits_SO_freq | 100.0% |
| experience_is_proxy | 0.0% |

With six of fourteen columns 100% "Missing," K-modes on the current (stale) input is guaranteed to assign every 2025 respondent the value "Missing" on those six columns regardless of cluster assignment — those columns cannot discriminate clusters at all in the current build, and any narrative claim about their distribution across clusters is unsupported by this data.
