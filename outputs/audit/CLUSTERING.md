# K-modes clustering — audit tables

Input: the 2025 rows of the harmonized master, **49,123 respondents**, all 14 columns treated as categorical. Nulls are passed to K-modes as a literal `Missing` category rather than dropped, so cluster sizes sum to the full input.

## 1. Hyperparameter grid searched

K is the only searched hyperparameter; initialisation is held fixed so the cost values across K are comparable.

| Hyperparameter | Value(s) searched |
| --- | --- |
| `n_clusters` (K) | 2, 3, 4, 5, 6, 7, 8 |
| `init` | `Huang` (fixed) |
| `n_init` | 5 (fixed) — best of 5 restarts per K |
| `random_state` | 42 (fixed, so the search is reproducible) |

That is **7 candidate values of K x 5 restarts = 35 K-modes fits**.

## 2. Selection criterion and its value per K

The criterion is the K-modes cost (total within-cluster Hamming dissimilarity to the assigned mode), which falls monotonically with K and so cannot be minimised to choose K. K is taken at the **elbow**: both axes are min-max normalised, and the selected K is the grid point furthest from the straight line joining the first and last points. `elbow distance` below is that perpendicular distance, and the largest value wins.

The elbow criterion selects K=3. K=5 is used for the reported partition: the cost curve is effectively flat for K >= 3 (reductions of 4,575 / 4,296 / 5,993 / 3,862 after the initial 17,829), so cost alone does not discriminate among these values, and K=3 separates the active respondents on a single axis only. K=5 was chosen on interpretability grounds and is a deliberate human override, not an automated selection. The full grid is retained above as a sensitivity check.

| K | Cost | Cost reduction vs previous K | Elbow distance | Iterations to converge | Selected |
| --- | --- | --- | --- | --- | --- |
| 2 | 239,615 | — | 0.0000 | 1 |  |
| 3 | 221,786 | 17,829 | 0.2123 | 2 | **YES** |
| 4 | 217,211 | 4,575 | 0.1792 | 3 |  |
| 5 | 212,915 | 4,296 | 0.1409 | 2 |  |
| 6 | 206,922 | 5,993 | 0.1340 | 3 |  |
| 7 | 203,060 | 3,862 | 0.0877 | 3 |  |
| 8 | 201,432 | 1,628 | 0.0000 | 2 |  |

## 3. Chosen configuration

| Setting | Value |
| --- | --- |
| `n_clusters` | **5** |
| `init` | `Huang` |
| `n_init` | 5 |
| `random_state` | 42 |
| Cost at chosen K | 212,915 |
| Rows clustered | 49,123 |

## 4. Feature diagnostics

K-modes weights every column equally under Hamming distance. A constant column contributes no discriminating power, and a high-cardinality column contributes a near-constant mismatch to every pair. Both are reported rather than dropped, because the figure was produced with all columns in the input.

| Column | Distinct categories | Missing | Missing share | Role in the distance |
| --- | --- | --- | --- | --- |
| `Year` | 1 | 0 | 0.00% | constant (no discriminating power) |
| `Age` | 7 | 0 | 0.00% | discriminating |
| `Education_Level` | 9 | 1,036 | 2.11% | discriminating |
| `Years_of_Experience` | 79 | 6,123 | 12.46% | discriminating |
| `Employment_Status` | 7 | 846 | 1.72% | discriminating |
| `Yearly_Compensation` | 6,235 | 25,195 | 51.29% | high-cardinality (near-constant mismatch) |
| `Usage_Frequency` | 1 | 49,123 | 100.00% | constant (no discriminating power) |
| `AI_Tool_Usage` | 1 | 49,123 | 100.00% | constant (no discriminating power) |
| `AI_Usage_Status` | 6 | 15,437 | 31.43% | discriminating |
| `Has_SO_account` | 4 | 16,356 | 33.30% | discriminating |
| `Part_of_community` | 7 | 17,445 | 35.51% | discriminating |
| `Participates_in_questions` | 9 | 16,923 | 34.45% | discriminating |
| `Visits_SO_freq` | 8 | 16,443 | 33.47% | discriminating |
| `experience_is_proxy` | 2 | 0 | 0.00% | discriminating |

**Caveat.** `Year`, `Yearly_Compensation`, `Usage_Frequency`, `AI_Tool_Usage` do not separate respondents: they are either constant across the input or so nearly unique that every pair mismatches. Cluster differences are therefore carried by the remaining columns, and no claim in the report should rest on these.

## 5. Cluster sizes

| Cluster | Rows | Share of input |
| --- | --- | --- |
| 0 | 10,289 | 20.95% |
| 1 | 16,902 | 34.41% |
| 2 | 11,596 | 23.61% |
| 3 | 6,898 | 14.04% |
| 4 | 3,438 | 7.00% |

Sizes sum to 49,123, the full input.

## 6. Composition table behind the heatmap

This is exactly the matrix plotted in `outputs/figures/cluster_developers_heatmap.png`: for each category of `Age` and `AI_Usage_Status`, the share of that cluster's members giving that answer. Each cluster's rows sum to 100% within a single source column.

| Category | Cluster 0 | Cluster 1 | Cluster 2 | Cluster 3 | Cluster 4 |
| --- | --- | --- | --- | --- | --- |
| Age: 18-24 years old | 36.88% | 23.56% | 5.77% | 8.23% | 5.26% |
| Age: 25-34 years old | 21.34% | 36.55% | 55.34% | 17.98% | 13.23% |
| Age: 35-44 years old | 14.94% | 23.97% | 18.62% | 51.96% | 55.29% |
| Age: 45-54 years old | 14.44% | 10.05% | 13.65% | 13.47% | 16.55% |
| Age: 55-64 years old | 8.20% | 3.51% | 4.86% | 5.80% | 6.57% |
| Age: 65 years or older | 3.36% | 1.25% | 1.41% | 1.91% | 2.56% |
| Age: Prefer not to say | 0.83% | 1.12% | 0.35% | 0.65% | 0.52% |
| AI_Usage_Status: Missing | 2.31% | 88.43% | 0.88% | 1.16% | 2.07% |
| AI_Usage_Status: No, and I don't plan to | 35.32% | 0.98% | 5.79% | 8.06% | 12.42% |
| AI_Usage_Status: No, but I plan to soon | 6.17% | 0.89% | 3.75% | 5.16% | 6.34% |
| AI_Usage_Status: Yes, I use AI tools daily | 23.09% | 6.47% | 66.56% | 60.61% | 14.40% |
| AI_Usage_Status: Yes, I use AI tools monthly or infrequently | 16.34% | 1.38% | 11.19% | 13.00% | 14.95% |
| AI_Usage_Status: Yes, I use AI tools weekly | 16.77% | 1.85% | 11.83% | 12.00% | 49.83% |

## 7. Modal profile of every cluster

The most common answer in each cluster for every clustered column, with the share of the cluster giving it.

| Cluster | Column | Modal value | Count | Share of cluster |
| --- | --- | --- | --- | --- |
| 0 | `Year` | 2025 | 10,289 | 100.00% |
| 0 | `Age` | 18-24 years old | 3,795 | 36.88% |
| 0 | `Education_Level` | Bachelor’s degree (B.A., B.S., B.Eng., etc.) | 5,415 | 52.63% |
| 0 | `Years_of_Experience` | 10.0 | 978 | 9.51% |
| 0 | `Employment_Status` | Employed | 6,418 | 62.38% |
| 0 | `Yearly_Compensation` | Missing | 4,063 | 39.49% |
| 0 | `Usage_Frequency` | Missing | 10,289 | 100.00% |
| 0 | `AI_Tool_Usage` | Missing | 10,289 | 100.00% |
| 0 | `AI_Usage_Status` | No, and I don't plan to | 3,634 | 35.32% |
| 0 | `Has_SO_account` | Yes | 7,525 | 73.14% |
| 0 | `Part_of_community` | Yes, somewhat | 3,001 | 29.17% |
| 0 | `Participates_in_questions` | I have never participated in Q&A on Stack Overflow | 4,946 | 48.07% |
| 0 | `Visits_SO_freq` | A few times per week | 5,186 | 50.40% |
| 0 | `experience_is_proxy` | True | 10,178 | 98.92% |
| 1 | `Year` | 2025 | 16,902 | 100.00% |
| 1 | `Age` | 25-34 years old | 6,177 | 36.55% |
| 1 | `Education_Level` | Bachelor’s degree (B.A., B.S., B.Eng., etc.) | 6,898 | 40.81% |
| 1 | `Years_of_Experience` | Missing | 5,840 | 34.55% |
| 1 | `Employment_Status` | Employed | 10,726 | 63.46% |
| 1 | `Yearly_Compensation` | Missing | 15,413 | 91.19% |
| 1 | `Usage_Frequency` | Missing | 16,902 | 100.00% |
| 1 | `AI_Tool_Usage` | Missing | 16,902 | 100.00% |
| 1 | `AI_Usage_Status` | Missing | 14,946 | 88.43% |
| 1 | `Has_SO_account` | Missing | 16,313 | 96.52% |
| 1 | `Part_of_community` | Missing | 16,780 | 99.28% |
| 1 | `Participates_in_questions` | Missing | 16,654 | 98.53% |
| 1 | `Visits_SO_freq` | Missing | 16,388 | 96.96% |
| 1 | `experience_is_proxy` | True | 11,062 | 65.45% |
| 2 | `Year` | 2025 | 11,596 | 100.00% |
| 2 | `Age` | 25-34 years old | 6,417 | 55.34% |
| 2 | `Education_Level` | Bachelor’s degree (B.A., B.S., B.Eng., etc.) | 6,652 | 57.36% |
| 2 | `Years_of_Experience` | 15.0 | 1,395 | 12.03% |
| 2 | `Employment_Status` | Employed | 8,878 | 76.56% |
| 2 | `Yearly_Compensation` | Missing | 2,876 | 24.80% |
| 2 | `Usage_Frequency` | Missing | 11,596 | 100.00% |
| 2 | `AI_Tool_Usage` | Missing | 11,596 | 100.00% |
| 2 | `AI_Usage_Status` | Yes, I use AI tools daily | 7,718 | 66.56% |
| 2 | `Has_SO_account` | Yes | 10,496 | 90.51% |
| 2 | `Part_of_community` | Yes, somewhat | 3,583 | 30.90% |
| 2 | `Participates_in_questions` | Infrequently, less than once per year | 7,020 | 60.54% |
| 2 | `Visits_SO_freq` | A few times per month or weekly | 5,141 | 44.33% |
| 2 | `experience_is_proxy` | True | 11,515 | 99.30% |
| 3 | `Year` | 2025 | 6,898 | 100.00% |
| 3 | `Age` | 35-44 years old | 3,584 | 51.96% |
| 3 | `Education_Level` | Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | 4,055 | 58.79% |
| 3 | `Years_of_Experience` | 10.0 | 696 | 10.09% |
| 3 | `Employment_Status` | Employed | 5,097 | 73.89% |
| 3 | `Yearly_Compensation` | Missing | 1,886 | 27.34% |
| 3 | `Usage_Frequency` | Missing | 6,898 | 100.00% |
| 3 | `AI_Tool_Usage` | Missing | 6,898 | 100.00% |
| 3 | `AI_Usage_Status` | Yes, I use AI tools daily | 4,181 | 60.61% |
| 3 | `Has_SO_account` | Yes | 5,185 | 75.17% |
| 3 | `Part_of_community` | No, not really | 4,020 | 58.28% |
| 3 | `Participates_in_questions` | I have never participated in Q&A on Stack Overflow | 3,642 | 52.80% |
| 3 | `Visits_SO_freq` | A few times per month or weekly | 3,005 | 43.56% |
| 3 | `experience_is_proxy` | True | 6,836 | 99.10% |
| 4 | `Year` | 2025 | 3,438 | 100.00% |
| 4 | `Age` | 35-44 years old | 1,901 | 55.29% |
| 4 | `Education_Level` | Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | 1,780 | 51.77% |
| 4 | `Years_of_Experience` | 20.0 | 709 | 20.62% |
| 4 | `Employment_Status` | Employed | 2,590 | 75.33% |
| 4 | `Yearly_Compensation` | Missing | 957 | 27.84% |
| 4 | `Usage_Frequency` | Missing | 3,438 | 100.00% |
| 4 | `AI_Tool_Usage` | Missing | 3,438 | 100.00% |
| 4 | `AI_Usage_Status` | Yes, I use AI tools weekly | 1,713 | 49.83% |
| 4 | `Has_SO_account` | Yes | 3,120 | 90.75% |
| 4 | `Part_of_community` | Neutral | 1,745 | 50.76% |
| 4 | `Participates_in_questions` | Infrequently, less than once per year | 2,299 | 66.87% |
| 4 | `Visits_SO_freq` | Less than once per month or monthly | 1,001 | 29.12% |
| 4 | `experience_is_proxy` | True | 3,409 | 99.16% |
