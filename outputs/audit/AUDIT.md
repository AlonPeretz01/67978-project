# Stack Overflow Survey Audit
Generated directly from the existing harmonized master dataset and existing source code. `NOT AVAILABLE` means the current repository does not define or retain the requested quantity.
## MASTER DATASET

Total rows: **768404**  
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
| 2011 | 2747 |
| 2012 | 5959 |
| 2013 | 9056 |
| 2014 | 7427 |
| 2015 | 24460 |
| 2016 | 54713 |
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
| 2011 | 2747 | 2725 | 0 | 2725 | 2647 | 2366 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2747 |
| 2012 | 5959 | 0 | 0 | 5920 | 5738 | 5238 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5959 |
| 2013 | 9056 | 0 | 0 | 9011 | 8218 | 7059 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9056 |
| 2014 | 7427 | 0 | 0 | 7344 | 7344 | 6898 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7427 |
| 2015 | 24460 | 24296 | 0 | 23768 | 22294 | 19481 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24460 |
| 2016 | 54713 | 54047 | 44955 | 49520 | 49518 | 41742 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 54713 |
| 2017 | 51392 | 0 | 51392 | 40890 | 51392 | 12891 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 51392 |
| 2018 | 98855 | 64574 | 94703 | 77903 | 95321 | 47702 | 76811 | 0 | 0 | 0 | 0 | 0 | 0 | 98855 |
| 2019 | 88883 | 79210 | 86390 | 74331 | 87181 | 55823 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 88883 |
| 2020 | 64461 | 45446 | 57431 | 46349 | 63854 | 34756 | 0 | 0 | 0 | 56805 | 56476 | 46792 | 56970 | 64461 |
| 2021 | 83439 | 82407 | 83126 | 61216 | 83323 | 46844 | 0 | 0 | 0 | 82525 | 82319 | 67553 | 82413 | 83439 |
| 2022 | 73268 | 70946 | 71571 | 51833 | 71709 | 38071 | 0 | 0 | 0 | 71572 | 71408 | 58229 | 70961 | 73268 |
| 2023 | 89184 | 89184 | 87973 | 66136 | 87898 | 48019 | 0 | 36137 | 87973 | 0 | 0 | 0 | 0 | 89184 |
| 2024 | 65437 | 65437 | 60784 | 51610 | 65437 | 23435 | 0 | 35072 | 60907 | 0 | 0 | 0 | 0 | 65437 |
| 2025 | 49123 | 49123 | 48087 | 43000 | 48277 | 23928 | 0 | 0 | 33686 | 0 | 0 | 0 | 0 | 49123 |

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
| 2011 | 2747 | 2724 | 503.000000 | 0.184655 | [0.170531, 0.199667] | 685.400000 | 0.251615 | [0.235677, 0.268253] | 1535.600000 | 0.563730 | [0.545030, 0.582251] | NO |
| 2012 | 5959 | 5919 | 1634.000000 | 0.276060 | [0.264819, 0.287591] | 1618.600000 | 0.273458 | [0.262253, 0.284958] | 2666.400000 | 0.450482 | [0.437843, 0.463185] | NO |
| 2013 | 9056 | 9010 | 2272.000000 | 0.252164 | [0.243305, 0.261235] | 2314.000000 | 0.256826 | [0.247910, 0.265949] | 4424.000000 | 0.491010 | [0.480694, 0.501334] | NO |
| 2014 | 7427 | 7343 | 2288.000000 | 0.311589 | [0.301097, 0.322279] | 1928.800000 | 0.262672 | [0.252732, 0.272860] | 3126.200000 | 0.425739 | [0.414471, 0.437084] | NO |
| 2015 | 24460 | 23768 | 8554.500000 | 0.359917 | [0.353838, 0.366041] | 6040.700000 | 0.254153 | [0.248658, 0.259727] | 9172.800000 | 0.385931 | [0.379761, 0.392138] | NO |
| 2016 | 54713 | 49520 | 16949.500000 | 0.342276 | [0.338109, 0.346467] | 12550.500000 | 0.253443 | [0.249631, 0.257293] | 20020.000000 | 0.404281 | [0.399966, 0.408611] | NO |
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

Non-null `Years_of_Experience` values in master: **23768**.

Raw distribution in the cleaned source file actually used by harmonization:

| Raw source value | Count |
| --- | --- |
| '2 - 5 years' | 7631 |
| '11+ years' | 5835 |
| '6 - 10 years' | 5563 |
| '1 - 2 years' | 3197 |
| 'Less than 1 year' | 1542 |
| <NULL> | 692 |

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
| '1 - 2 years' | 6119 |
| <NULL> | 5193 |
| 'Less than 1 year' | 2882 |


## RANDOM FOREST MODEL

Exact target variable: **Part of the Stack Overflow community**; source harmonized column selected by `engagement_target`: `Part_of_community` (the visit column is evaluated only as a fallback). It appears with mapped binary values in years: 2022.

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
| 0 | 40113 | 0.571671 |
| 1 | 30055 | 0.428329 |

Final labelled n used to fit the retained full reference model: **70168**. The separate reproducible stratified 70/30 held-out evaluation, including test metrics and permutation importance, is in `RF_EVAL.md`.

Features actually fed to the estimator after the existing imputation/one-hot encoding:

| Encoded feature | dtype |
| --- | --- |
| Years_of_Experience | float64 |
| Yearly_Compensation | float64 |
| Education_Level=Associate degree (A.A., A.S., etc.) | float64 |
| Education_Level=Bachelor’s degree (B.A., B.S., B.Eng., etc.) | float64 |
| Education_Level=Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | float64 |
| Education_Level=Other doctoral degree (Ph.D., Ed.D., etc.) | float64 |
| Education_Level=Primary/elementary school | float64 |
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
| Years_of_Experience | 0.137420 |
| Yearly_Compensation | 0.842433 |
| Education_Level | 0.020147 |

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
| Full Dataset | 2020 | 15 | 3 | const | 0.366775 | 0.026330 | [0.309406, 0.424144] | 9.03346e-09 | 0.672986 |
| Full Dataset | 2020 | 15 | 3 | time | 0.012682 | 0.005151 | [0.001458, 0.023906] | 0.0299423 | 0.672986 |
| Full Dataset | 2020 | 15 | 3 | slope_change | -0.062000 | 0.013629 | [-0.091696, -0.032304] | 0.000667364 | 0.672986 |
| Full Dataset | 2022 | 15 | 3 | const | 0.328116 | 0.032128 | [0.258114, 0.398117] | 2.85158e-07 | 0.511060 |
| Full Dataset | 2022 | 15 | 3 | time | 0.004406 | 0.005035 | [-0.006565, 0.015377] | 0.39877 | 0.511060 |
| Full Dataset | 2022 | 15 | 3 | slope_change | -0.077704 | 0.024738 | [-0.131604, -0.023803] | 0.008516 | 0.511060 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | const | 0.340646 | 0.026017 | [0.281792, 0.399500] | 3.65185e-07 | 0.782349 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | time | -0.001116 | 0.007670 | [-0.018467, 0.016235] | 0.887559 | 0.782349 |
| 2014+ Truncated Sample | 2020 | 12 | 3 | slope_change | -0.041077 | 0.015234 | [-0.075538, -0.006615] | 0.0245384 | 0.782349 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | const | 0.290114 | 0.028280 | [0.226141, 0.354087] | 2.89168e-06 | 0.741779 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | time | -0.009417 | 0.006080 | [-0.023170, 0.004337] | 0.155821 | 0.741779 |
| 2014+ Truncated Sample | 2022 | 12 | 3 | slope_change | -0.047595 | 0.021921 | [-0.097183, 0.001993] | 0.0579976 | 0.741779 |

The reported `slope_change` p-value tests the coefficient on `max(0, year − break_year)`: a difference between post-break and pre-break slopes. The specification is continuous and has no level-shift term, so it tests neither a level shift nor a joint level-and-slope break. `slope variance 0.0011`: **NOT AVAILABLE: no statistic with that name or value is calculated in the repository.** It must not be treated as a model result without identifying its source.

## COUNTRY COMPOSITION

Country is not retained in the 13-column master dataset; these figures are computed from each cleaned annual input, which is the closest available respondent-level source. Percentages use all rows in that annual cleaned file as the denominator. Western Europe is operationalized as UN M49 Western Europe (Austria, Belgium, France, Germany, Liechtenstein, Luxembourg, Monaco, Netherlands, Switzerland).

### 2011 (source column: `What Country or Region do you live in?`; n = 2747)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 1026 | 0.373498 |
| Other Europe | 428 | 0.155806 |
| United Kingdom | 307 | 0.111758 |
| Canada | 153 | 0.055697 |
| Australia | 111 | 0.040408 |
| Germany | 101 | 0.036767 |
| India | 92 | 0.033491 |
| South America | 90 | 0.032763 |
| Other Asia | 78 | 0.028395 |
| Middle East | 70 | 0.025482 |

### 2012 (source column: `What Country or Region do you live in?`; n = 5959)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 1755 | 0.294513 |
| Other Europe | 1108 | 0.185937 |
| United Kingdom | 572 | 0.095989 |
| India | 479 | 0.080383 |
| Canada | 335 | 0.056217 |
| Germany | 257 | 0.043128 |
| Other Asia | 206 | 0.034570 |
| South America | 178 | 0.029871 |
| Australia | 175 | 0.029367 |
| Russia | 152 | 0.025508 |

### 2013 (source column: `What Country or Region do you live in?`; n = 9056)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States of America | 3101 | 0.342425 |
| Other Europe | 1381 | 0.152496 |
| United Kingdom | 870 | 0.096069 |
| India | 662 | 0.073101 |
| Germany | 515 | 0.056868 |
| Canada | 463 | 0.051126 |
| Other Asia | 331 | 0.036550 |
| Australia | 236 | 0.026060 |
| Russia | 225 | 0.024845 |
| France | 221 | 0.024404 |

### 2014 (source column: `What Country do you live in?`; n = 7427)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 2083 | 0.280463 |
| India | 849 | 0.114313 |
| United Kingdom | 702 | 0.094520 |
| Germany | 441 | 0.059378 |
| Canada | 289 | 0.038912 |
| France | 198 | 0.026659 |
| Australia | 179 | 0.024101 |
| Russia | 155 | 0.020870 |
| Netherlands | 152 | 0.020466 |
| Poland | 126 | 0.016965 |

### 2015 (source column: `Country`; n = 24460)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 4482 | 0.183238 |
| United Kingdom | 2244 | 0.091742 |
| India | 2138 | 0.087408 |
| Germany | 1822 | 0.074489 |
| Canada | 788 | 0.032216 |
| Poland | 751 | 0.030703 |
| France | 735 | 0.030049 |
| Russian Federation | 604 | 0.024693 |
| Australia | 601 | 0.024571 |
| Netherlands | 594 | 0.024285 |

### 2016 (source column: `country`; n = 54713)

| Country | Respondents | Proportion |
| --- | --- | --- |
| United States | 13153 | 0.240400 |
| United Kingdom | 4487 | 0.082010 |
| India | 3903 | 0.071336 |
| Germany | 3768 | 0.068868 |
| Canada | 1981 | 0.036207 |
| Poland | 1886 | 0.034471 |
| France | 1595 | 0.029152 |
| Russian Federation | 1363 | 0.024912 |
| Sweden | 1311 | 0.023961 |
| Netherlands | 1173 | 0.021439 |

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
| 2011 | 1393 | 0.507099 |
| 2012 | 2612 | 0.438329 |
| 2013 | 4496 | 0.496466 |
| 2014 | 3368 | 0.453481 |
| 2015 | 9349 | 0.382216 |
| 2016 | 23296 | 0.425785 |
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

Core variables with at least one non-null 2025 value: `Year`, `Age`, `Education_Level`, `Years_of_Experience`, `Employment_Status`, `Yearly_Compensation`, `AI_Usage_Status`.

`Years_of_Experience` is sourced from configured column(s) `YearsCode`; the cleaned 2025 input contains experience-like column(s) `YearsCode`. `YearsCodePro` is genuinely absent from raw 2025, so the available `YearsCode` is used as a tagged proxy (`experience_is_proxy=True`) rather than treated as professional experience.

## DISCREPANCY FLAGS

- NONE: no internally inconsistent computed values were detected.
