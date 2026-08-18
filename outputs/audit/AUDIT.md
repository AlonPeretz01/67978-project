# Stack Overflow Survey Audit
Generated directly from the existing harmonized master dataset and existing source code. `NOT AVAILABLE` means the current repository does not define or retain the requested quantity.
## MASTER DATASET

Total rows: **772603**  
Total columns: **14**

Exact column names:

```text
Year
Age
Education_Level
Years_of_Experience
Employment_Status
Yearly_Compensation
Usage_Frequency
AI_Tool_Usage
AI_Usage_Status
Has_SO_account
Part_of_community
Participates_in_questions
Visits_SO_freq
experience_is_proxy
```

Per-year row count:

| Year | n |
| --- | --- |
| 2011 | 2814 |
| 2012 | 6244 |
| 2013 | 9743 |
| 2014 | 7644 |
| 2015 | 26086 |
| 2016 | 56030 |
| 2017 | 51392 |
| 2018 | 98855 |
| 2019 | 88883 |
| 2020 | 64461 |
| 2021 | 83439 |
| 2022 | 73268 |
| 2023 | 89184 |
| 2024 | 65437 |
| 2025 | 49123 |

Years present at all: **2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025**.

## FACT CHECK

Per-year non-null count for every current master column (the first 13 are the original core variables; `experience_is_proxy` is the required provenance flag):

| Year | Year | Age | Education_Level | Years_of_Experience | Employment_Status | Yearly_Compensation | Usage_Frequency | AI_Tool_Usage | AI_Usage_Status | Has_SO_account | Part_of_community | Participates_in_questions | Visits_SO_freq | experience_is_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2011 | 2814 | 2730 | 0 | 2730 | 2647 | 2366 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2814 |
| 2012 | 6244 | 0 | 0 | 5965 | 5738 | 5238 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6244 |
| 2013 | 9743 | 0 | 0 | 9437 | 8219 | 7059 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9743 |
| 2014 | 7644 | 0 | 0 | 7347 | 7347 | 6901 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7644 |
| 2015 | 26086 | 25831 | 0 | 24827 | 22294 | 19481 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26086 |
| 2016 | 56030 | 55336 | 44955 | 49520 | 49519 | 41742 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 56030 |
| 2017 | 51392 | 0 | 51392 | 40890 | 51392 | 12891 | 0 | 0 | 0 | 0 | 32410 | 0 | 0 | 51392 |
| 2018 | 98855 | 64574 | 94703 | 77903 | 95321 | 47702 | 76811 | 0 | 0 | 0 | 76007 | 0 | 0 | 98855 |
| 2019 | 88883 | 79210 | 86390 | 74331 | 87181 | 55823 | 0 | 0 | 0 | 0 | 88131 | 74692 | 88263 | 88883 |
| 2020 | 64461 | 45446 | 57431 | 46349 | 63854 | 34756 | 0 | 0 | 0 | 56805 | 56476 | 46792 | 56970 | 64461 |
| 2021 | 83439 | 82407 | 83126 | 61216 | 83323 | 46844 | 0 | 0 | 0 | 82525 | 82319 | 67553 | 82413 | 83439 |
| 2022 | 73268 | 70946 | 71571 | 51833 | 71709 | 38071 | 0 | 0 | 0 | 71572 | 71408 | 58229 | 70961 | 73268 |
| 2023 | 89184 | 89184 | 87973 | 66136 | 87898 | 48019 | 0 | 36137 | 87973 | 0 | 87692 | 66061 | 87140 | 89184 |
| 2024 | 65437 | 65437 | 60784 | 51610 | 65437 | 23435 | 0 | 35072 | 60907 | 0 | 59163 | 45237 | 59536 | 65437 |
| 2025 | 49123 | 49123 | 48087 | 43000 | 48277 | 23928 | 0 | 0 | 33686 | 32767 | 31678 | 32200 | 32680 | 49123 |

## EXPERIENCE COHORTS

Counts may be fractional because the existing cohort function allocates ranges across integer years. `n_with_valid_experience` means parsable by that function, which can be lower than non-null source values. Wilson intervals use the fractional allocated count and the number of parsable responses.

```python
def experience_cohort_weights(value: object) -> tuple[float, float, float]:
    """Allocate inclusive integer experience ranges across junior/mid/senior."""
    interval = experience_interval(value)
    if interval is None:
        return np.nan, np.nan, np.nan
    lower, upper = interval
    years = np.arange(np.ceil(lower), np.floor(upper) + 1, dtype=float)
    if years.size == 0:
        years = np.array([(lower + upper) / 2.0])
    return (
        float(np.mean(years <= 3)),
        float(np.mean((years >= 4) & (years <= 7))),
        float(np.mean(years >= 8)),
    )
```

| Year | n_total | n_with_valid_experience | junior count | junior proportion | junior Wilson 95% CI | mid count | mid proportion | mid Wilson 95% CI | senior count | senior proportion | senior Wilson 95% CI | junior > senior? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2011 | 2814 | 2729 | 504.500000 | 0.184866 | [0.170748, 0.199870] | 687.300000 | 0.251850 | [0.235921, 0.268478] | 1537.200000 | 0.563283 | [0.544599, 0.581790] | NO |
| 2012 | 6244 | 5964 | 1661.000000 | 0.278504 | [0.267273, 0.290021] | 1632.200000 | 0.273675 | [0.262509, 0.285134] | 2670.800000 | 0.447820 | [0.435238, 0.460470] | NO |
| 2013 | 9743 | 9436 | 2437.000000 | 0.258266 | [0.249535, 0.267194] | 2448.400000 | 0.259474 | [0.250729, 0.268415] | 4550.600000 | 0.482259 | [0.472187, 0.492347] | NO |
| 2014 | 7644 | 7346 | 2290.500000 | 0.311802 | [0.301310, 0.322491] | 1929.300000 | 0.262633 | [0.252695, 0.272818] | 3126.200000 | 0.425565 | [0.414300, 0.436907] | NO |
| 2015 | 26086 | 24827 | 9038.500000 | 0.364059 | [0.358096, 0.370065] | 6326.100000 | 0.254807 | [0.249425, 0.260265] | 9462.400000 | 0.381133 | [0.375111, 0.387193] | NO |
| 2016 | 56030 | 49520 | 16949.500000 | 0.342276 | [0.338109, 0.346467] | 12550.500000 | 0.253443 | [0.249631, 0.257293] | 20020.000000 | 0.404281 | [0.399966, 0.408611] | NO |
| 2017 | 51392 | 40890 | 15091.500000 | 0.369076 | [0.364411, 0.373765] | 11127.500000 | 0.272133 | [0.267840, 0.276468] | 14671.000000 | 0.358792 | [0.354156, 0.363454] | YES |
| 2018 | 98855 | 77903 | 30541.666667 | 0.392047 | [0.388625, 0.395481] | 21831.333333 | 0.280237 | [0.277095, 0.283402] | 25530.000000 | 0.327715 | [0.324428, 0.331020] | YES |
| 2019 | 88883 | 74331 | 24198.000000 | 0.325544 | [0.322184, 0.328921] | 20902.000000 | 0.281202 | [0.277981, 0.284445] | 29231.000000 | 0.393254 | [0.389749, 0.396772] | NO |
| 2020 | 64461 | 46349 | 14621.000000 | 0.315454 | [0.311239, 0.319700] | 12664.000000 | 0.273231 | [0.269193, 0.277307] | 19064.000000 | 0.411314 | [0.406842, 0.415801] | NO |
| 2021 | 83439 | 61216 | 17030.000000 | 0.278195 | [0.274659, 0.281759] | 16861.000000 | 0.275435 | [0.271910, 0.278987] | 27325.000000 | 0.446370 | [0.442436, 0.450311] | NO |
| 2022 | 73268 | 51833 | 12822.000000 | 0.247371 | [0.243676, 0.251105] | 13885.000000 | 0.267880 | [0.264084, 0.271709] | 25126.000000 | 0.484749 | [0.480448, 0.489052] | NO |
| 2023 | 89184 | 66136 | 13274.000000 | 0.200708 | [0.197672, 0.203778] | 15908.000000 | 0.240535 | [0.237292, 0.243807] | 36954.000000 | 0.558758 | [0.554970, 0.562538] | NO |
| 2024 | 65437 | 51610 | 13756.000000 | 0.266537 | [0.262740, 0.270369] | 12101.000000 | 0.234470 | [0.230835, 0.238145] | 25753.000000 | 0.498992 | [0.494679, 0.503306] | NO |
| 2025 | 49123 | 42929 | 2987.000000 | 0.069580 | [0.067211, 0.072026] | 7603.000000 | 0.177106 | [0.173524, 0.180747] | 32339.000000 | 0.753314 | [0.749213, 0.757369] | NO |

Years where junior_proportion > senior_proportion: **2017, 2018**

## 2015 / 2016 PROVENANCE
### 2015
Exact source column(s) used: `Years IT / Programming Experience`.

Exact configured mapping dict:

```python
{'Age': 'Age', 'Years IT / Programming Experience': 'Years_of_Experience', 'Occupation': 'Employment_Status', 'Employment Status': 'Employment_Status', 'Compensation': 'Yearly_Compensation', 'Compensation: midpoint': 'Yearly_Compensation'}
```

Non-null `Years_of_Experience` values in master: **24827**.

Raw distribution in the cleaned source file actually used by harmonization:

| Raw source value | Count |
| --- | --- |
| '2 - 5 years' | 8037 |
| '11+ years' | 6001 |
| '6 - 10 years' | 5769 |
| '1 - 2 years' | 3373 |
| 'Less than 1 year' | 1647 |
| <NULL> | 1259 |

### 2016
Exact source column(s) used: `experience_range`.

Exact configured mapping dict:

```python
{'age_midpoint': 'Age', 'occupation': 'Employment_Status', 'education': 'Education_Level', 'experience_range': 'Years_of_Experience', 'salary_midpoint': 'Yearly_Compensation'}
```

Non-null `Years_of_Experience` values in master: **49520**.

Raw distribution in the cleaned source file actually used by harmonization:

| Raw source value | Count |
| --- | --- |
| '2 - 5 years' | 15897 |
| '11+ years' | 13117 |
| '6 - 10 years' | 11505 |
| <NULL> | 6510 |
| '1 - 2 years' | 6119 |
| 'Less than 1 year' | 2882 |


## RANDOM FOREST MODEL

Exact target variable: **Part of the Stack Overflow community**; source harmonized column selected by `engagement_target`: `Part_of_community` (the visit column is evaluated only as a fallback). It appears with mapped binary values in years: 2022, 2023, 2024, 2025.

Binarization source code:

```python
def engagement_target(data: pd.DataFrame) -> tuple[pd.Series, str]:
    """Map the best-covered engagement measure to active (1) / inactive (0)."""
    community_map = {
        "yes, definitely": 1.0, "yes, somewhat": 1.0, "neutral": 0.0,
        "no, not really": 0.0, "no, not at all": 0.0,
    }
    visit_map = {
        "multiple times per day": 1.0, "daily or almost daily": 1.0,
        "a few times per week": 1.0, "a few times per month or weekly": 0.0,
        "less than once per month or monthly": 0.0,
        "i have never visited stack overflow (before today)": 0.0,
    }
    community = data["Part_of_community"].astype("string").str.strip().str.lower().map(community_map)
    visits = data["Visits_SO_freq"].astype("string").str.strip().str.lower().map(visit_map)
    if community.notna().sum() >= 100 and community.nunique(dropna=True) == 2:
        return community, "Part of the Stack Overflow community"
    if visits.notna().sum() >= 100 and visits.nunique(dropna=True) == 2:
        return visits, "Frequent Stack Overflow visits"
    raise ValueError("Recent survey rows do not contain a binary engagement target with at least 100 usable responses.")
```

Class balance:

| Class | Count | Proportion |
| --- | --- | --- |
| 0 | 159279 | 0.645340 |
| 1 | 87535 | 0.354660 |

Final labelled n used to fit the retained full reference model: **246814**. The separate reproducible stratified 70/30 held-out evaluation, including test metrics and permutation importance, is in `RF_EVAL.md`.

Features actually fed to the estimator after the existing imputation/one-hot encoding:

| Encoded feature | dtype |
| --- | --- |
| Years_of_Experience | float64 |
| Yearly_Compensation | float64 |
| Education_Level=Associate degree (A.A., A.S., etc.) | float64 |
| Education_Level=Bachelor’s degree (B.A., B.S., B.Eng., etc.) | float64 |
| Education_Level=Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | float64 |
| Education_Level=Other (please specify): | float64 |
| Education_Level=Other doctoral degree (Ph.D., Ed.D., etc.) | float64 |
| Education_Level=Primary/elementary school | float64 |
| Education_Level=Professional degree (JD, MD, Ph.D, Ed.D, etc.) | float64 |
| Education_Level=Professional degree (JD, MD, etc.) | float64 |
| Education_Level=Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.) | float64 |
| Education_Level=Some college/university study without earning a degree | float64 |
| Education_Level=Something else | float64 |

Estimator get_params():

```python
{'bootstrap': True, 'ccp_alpha': 0.0, 'class_weight': 'balanced', 'criterion': 'gini', 'max_depth': None, 'max_features': 'sqrt', 'max_leaf_nodes': None, 'max_samples': None, 'min_impurity_decrease': 0.0, 'min_samples_leaf': 1, 'min_samples_split': 2, 'min_weight_fraction_leaf': 0.0, 'monotonic_cst': None, 'n_estimators': 100, 'n_jobs': -1, 'oob_score': False, 'random_state': 42, 'verbose': 0, 'warm_start': False}
```

Impurity-based `feature_importances_`, aggregated to the original source features as in the project code (sum = 1.000000):

| Source feature | Importance |
| --- | --- |
| Years_of_Experience | 0.084568 |
| Yearly_Compensation | 0.895511 |
| Education_Level | 0.019921 |

## PIECEWISE / STRUCTURAL BREAK REGRESSION

Exact fitting-function source:

```python
def _fit_broken_stick(
    sample: pd.DataFrame, year_column: str, metric: str, knot_year: int
) -> object:
    """Fit a continuous two-slope linear model at a supplied candidate knot."""
    pre_count = int((sample[year_column] < knot_year).sum())
    post_count = int((sample[year_column] >= knot_year).sum())
    if pre_count < 2 or post_count < 2:
        raise ValueError(
            f"The {knot_year} intervention needs at least two observations on each side "
            f"in the analysed sample; received {pre_count} pre and {post_count} post."
        )
    if len(sample) <= 3:
        raise ValueError("At least four observations are required for piecewise regression.")
    time = sample[year_column].astype(float) - knot_year
    design = pd.DataFrame({"time": time, "slope_change": np.maximum(time, 0.0)})
    return sm.OLS(
        sample[metric].astype(float), sm.add_constant(design, has_constant="add")
    ).fit()
```

Input is annual `Junior_Proportion` for years 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 (n = 15). Each fit has 3 estimated parameters: `const`, `time`, and `slope_change`.

| Sample | Break year | n | Parameters | Coefficient | Estimate | SE | 95% CI | p-value | R-squared |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Dataset | 2020 | 15 | 3 | const | 0.366646 | 0.026422 | [0.309077, 0.424214] | 9.43359e-09 | 0.671866 |
| Full Dataset | 2020 | 15 | 3 | time | 0.012359 | 0.005169 | [0.001096, 0.023622] | 0.0340853 | 0.671866 |
| Full Dataset | 2020 | 15 | 3 | slope_change | -0.061642 | 0.013677 | [-0.091441, -0.031843] | 0.000717778 | 0.671866 |
| Full Dataset | 2022 | 15 | 3 | const | 0.327711 | 0.032142 | [0.257680, 0.397742] | 2.90315e-07 | 0.512369 |
| Full Dataset | 2022 | 15 | 3 | time | 0.004131 | 0.005037 | [-0.006845, 0.015106] | 0.428192 | 0.512369 |
| Full Dataset | 2022 | 15 | 3 | slope_change | -0.077255 | 0.024749 | [-0.131178, -0.023332] | 0.00882893 | 0.512369 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | const | 0.340411 | 0.026093 | [0.281384, 0.399439] | 3.76741e-07 | 0.782601 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | time | -0.001411 | 0.007693 | [-0.018813, 0.015990] | 0.858485 | 0.782601 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | slope_change | -0.040717 | 0.015279 | [-0.075280, -0.006154] | 0.0258365 | 0.782601 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | const | 0.289768 | 0.028293 | [0.225764, 0.353772] | 2.93245e-06 | 0.743341 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | time | -0.009628 | 0.006083 | [-0.023388, 0.004132] | 0.147907 | 0.743341 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | slope_change | -0.047235 | 0.021931 | [-0.096847, 0.002377] | 0.0596684 | 0.743341 |

The reported `slope_change` p-value tests the coefficient on `max(0, year − break_year)`: a difference between post-break and pre-break slopes. The specification is continuous and has no level-shift term, so it tests neither a level shift nor a joint level-and-slope break. `slope variance 0.0011`: **NOT AVAILABLE: no statistic with that name or value is calculated in the repository.** It must not be treated as a model result without identifying its source.

## COUNTRY COMPOSITION

Country is not retained in the 13-column master dataset; these figures are computed from each cleaned annual input, which is the closest available respondent-level source. Percentages use all rows in that annual cleaned file as the denominator. Western Europe is operationalized as UN M49 Western Europe (Austria, Belgium, France, Germany, Liechtenstein, Luxembourg, Monaco, Netherlands, Switzerland).

### 2011 (source column: `What Country or Region do you live in?`; n = 2814)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 1037 | 0.368515 |
| Other Europe | 451 | 0.160270 |
| United Kingdom | 314 | 0.111585 |
| Canada | 156 | 0.055437 |
| Australia | 112 | 0.039801 |
| Germany | 106 | 0.037669 |
| India | 95 | 0.033760 |
| South America | 91 | 0.032338 |
| Other Asia | 81 | 0.028785 |
| Middle East | 73 | 0.025942 |

### 2012 (source column: `What Country or Region do you live in?`; n = 6244)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 1785 | 0.285874 |
| Other Europe | 1168 | 0.187060 |
| United Kingdom | 589 | 0.094331 |
| India | 537 | 0.086003 |
| Canada | 348 | 0.055734 |
| Germany | 273 | 0.043722 |
| Other Asia | 221 | 0.035394 |
| Australia | 185 | 0.029628 |
| South America | 182 | 0.029148 |
| Russia | 162 | 0.025945 |

### 2013 (source column: `What Country or Region do you live in?`; n = 9743)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 3181 | 0.326491 |
| Other Europe | 1626 | 0.166889 |
| United Kingdom | 935 | 0.095966 |
| India | 737 | 0.075644 |
| Germany | 583 | 0.059838 |
| Canada | 490 | 0.050293 |
| Other Asia | 367 | 0.037668 |
| Australia | 246 | 0.025249 |
| Russia | 241 | 0.024736 |
| France | 232 | 0.023812 |

### 2014 (source column: `What Country do you live in?`; n = 7644)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 2128 | 0.278388 |
| India | 881 | 0.115254 |
| United Kingdom | 721 | 0.094322 |
| Germany | 455 | 0.059524 |
| Canada | 306 | 0.040031 |
| France | 198 | 0.025903 |
| Australia | 182 | 0.023810 |
| Russia | 166 | 0.021716 |
| Netherlands | 154 | 0.020147 |
| Poland | 131 | 0.017138 |

### 2015 (source column: `Country`; n = 26086)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 4745 | 0.181898 |
| India | 2461 | 0.094342 |
| United Kingdom | 2403 | 0.092118 |
| Germany | 1976 | 0.075749 |
| Poland | 833 | 0.031933 |
| Canada | 828 | 0.031741 |
| France | 776 | 0.029748 |
| Russian Federation | 650 | 0.024918 |
| Australia | 618 | 0.023691 |
| Netherlands | 614 | 0.023538 |

### 2016 (source column: `country`; n = 56030)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 13539 | 0.241638 |
| United Kingdom | 4573 | 0.081617 |
| India | 4193 | 0.074835 |
| Germany | 3883 | 0.069302 |
| Canada | 2024 | 0.036124 |
| Poland | 1971 | 0.035178 |
| France | 1626 | 0.029020 |
| Russian Federation | 1419 | 0.025326 |
| Sweden | 1328 | 0.023702 |
| Netherlands | 1188 | 0.021203 |

### 2017 (source column: `Country`; n = 51392)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 11455 | 0.222895 |
| India | 5197 | 0.101125 |
| United Kingdom | 4395 | 0.085519 |
| Germany | 4143 | 0.080616 |
| Canada | 2233 | 0.043450 |
| France | 1740 | 0.033857 |
| Poland | 1290 | 0.025101 |
| Australia | 913 | 0.017765 |
| Russian Federation | 873 | 0.016987 |
| Spain | 864 | 0.016812 |

### 2018 (source column: `Country`; n = 98855)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 20309 | 0.205442 |
| India | 13721 | 0.138799 |
| Germany | 6459 | 0.065338 |
| United Kingdom | 6221 | 0.062931 |
| Canada | 3393 | 0.034323 |
| Russian Federation | 2869 | 0.029022 |
| France | 2572 | 0.026018 |
| Brazil | 2505 | 0.025340 |
| Poland | 2122 | 0.021466 |
| Australia | 2018 | 0.020414 |

### 2019 (source column: `Country`; n = 88883)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 20949 | 0.235692 |
| India | 9061 | 0.101943 |
| Germany | 5866 | 0.065997 |
| United Kingdom | 5737 | 0.064546 |
| Canada | 3395 | 0.038196 |
| France | 2391 | 0.026901 |
| Brazil | 1948 | 0.021916 |
| Poland | 1922 | 0.021624 |
| Australia | 1903 | 0.021410 |
| Netherlands | 1852 | 0.020836 |

### 2020 (source column: `Country`; n = 64461)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 12469 | 0.193435 |
| India | 8403 | 0.130358 |
| United Kingdom | 3896 | 0.060440 |
| Germany | 3890 | 0.060347 |
| Canada | 2191 | 0.033990 |
| France | 1898 | 0.029444 |
| Brazil | 1818 | 0.028203 |
| Netherlands | 1343 | 0.020834 |
| Poland | 1278 | 0.019826 |
| Australia | 1208 | 0.018740 |

### 2021 (source column: `Country`; n = 83439)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 15288 | 0.183224 |
| India | 10511 | 0.125972 |
| Germany | 5625 | 0.067415 |
| United Kingdom of Great Britain and Northern Ireland | 4475 | 0.053632 |
| Canada | 3012 | 0.036098 |
| France | 2708 | 0.032455 |
| Brazil | 2254 | 0.027014 |
| Poland | 1805 | 0.021633 |
| Netherlands | 1772 | 0.021237 |
| Italy | 1666 | 0.019967 |

### 2022 (source column: `Country`; n = 73268)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 13543 | 0.184842 |
| India | 6639 | 0.090613 |
| Germany | 5395 | 0.073634 |
| United Kingdom of Great Britain and Northern Ireland | 4190 | 0.057187 |
| Canada | 2490 | 0.033985 |
| France | 2328 | 0.031774 |
| Brazil | 2109 | 0.028785 |
| Poland | 1732 | 0.023639 |
| Netherlands | 1555 | 0.021223 |
| Spain | 1521 | 0.020759 |

### 2023 (source column: `Country`; n = 89184)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 18647 | 0.209085 |
| Germany | 7328 | 0.082167 |
| India | 5625 | 0.063072 |
| United Kingdom of Great Britain and Northern Ireland | 5552 | 0.062253 |
| Canada | 3507 | 0.039323 |
| France | 2933 | 0.032887 |
| Poland | 2435 | 0.027303 |
| Netherlands | 2383 | 0.026720 |
| Australia | 2078 | 0.023300 |
| Brazil | 2042 | 0.022896 |

### 2024 (source column: `Country`; n = 65437)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 11095 | 0.169552 |
| Germany | 4947 | 0.075599 |
| India | 4231 | 0.064658 |
| United Kingdom of Great Britain and Northern Ireland | 3224 | 0.049269 |
| Ukraine | 2672 | 0.040833 |
| France | 2110 | 0.032245 |
| Canada | 2104 | 0.032153 |
| Poland | 1534 | 0.023442 |
| Netherlands | 1449 | 0.022143 |
| Brazil | 1375 | 0.021013 |

### 2025 (source column: `Country`; n = 49123)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 7226 | 0.147100 |
| Germany | 3022 | 0.061519 |
| India | 2542 | 0.051748 |
| United Kingdom of Great Britain and Northern Ireland | 2038 | 0.041488 |
| France | 1409 | 0.028683 |
| Canada | 1303 | 0.026525 |
| Ukraine | 964 | 0.019624 |
| Poland | 887 | 0.018057 |
| Netherlands | 867 | 0.017650 |
| Italy | 834 | 0.016978 |

US + Canada + Western Europe:

| Year | Respondents | Proportion |
| --- | --- | --- |
| 2011 | 1414 | 0.502488 |
| 2012 | 2677 | 0.428732 |
| 2013 | 4693 | 0.481679 |
| 2014 | 3454 | 0.451858 |
| 2015 | 9905 | 0.379706 |
| 2016 | 23891 | 0.426397 |
| 2017 | 21942 | 0.426954 |
| 2018 | 37183 | 0.376137 |
| 2019 | 37065 | 0.417009 |
| 2020 | 23463 | 0.363988 |
| 2021 | 30886 | 0.370163 |
| 2022 | 27759 | 0.378869 |
| 2023 | 37943 | 0.425446 |
| 2024 | 23945 | 0.365924 |
| 2025 | 15127 | 0.307941 |

## 2025 SURVEY

Is the 2025 file loaded into the master dataset? **YES**.

Core variables with at least one non-null 2025 value: `Year`, `Age`, `Education_Level`, `Years_of_Experience`, `Employment_Status`, `Yearly_Compensation`, `AI_Usage_Status`, `Has_SO_account`, `Part_of_community`, `Participates_in_questions`, `Visits_SO_freq`.

`Years_of_Experience` is sourced from configured column(s) `YearsCode`; the cleaned 2025 input contains experience-like column(s) `YearsCode`. `YearsCodePro` is genuinely absent from raw 2025, so the available `YearsCode` is used as a tagged proxy (`experience_is_proxy=True`) rather than treated as professional experience.

## DISCREPANCY FLAGS

- NONE: no internally inconsistent computed values were detected.
