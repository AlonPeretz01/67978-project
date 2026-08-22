# Random-forest held-out evaluation

Target: **Part of the Stack Overflow community**. Target-covered years: **2022, 2023, 2024, 2025**. AI-related variable ever included as a feature: **NO**; the feature list is exactly `Years_of_Experience`, `Yearly_Compensation`, and `Education_Level`.

Stratified split: random_state=42, train n=172769, test n=74045.

| Metric | Test-set value |
| --- | --- |
| accuracy | 0.545398 |
| precision | 0.391769 |
| recall | 0.509996 |
| f1 | 0.443132 |
| roc_auc | 0.539041 |
| majority_class_accuracy | 0.645337 |

Permutation importance uses test-set accuracy, n_repeats=10, random_state=42. Encoded-feature results:

| Encoded feature | Mean decrease | Std |
| --- | --- | --- |
| Years_of_Experience | 0.013559 | 0.001506 |
| Yearly_Compensation | 0.024912 | 0.001558 |
| Education_Level=Associate degree (A.A., A.S., etc.) | 0.000821 | 0.000192 |
| Education_Level=Bachelor’s degree (B.A., B.S., B.Eng., etc.) | -0.015844 | 0.000558 |
| Education_Level=Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | -0.011458 | 0.000762 |
| Education_Level=Other (please specify): | -0.000047 | 0.000033 |
| Education_Level=Other doctoral degree (Ph.D., Ed.D., etc.) | 0.000096 | 0.000080 |
| Education_Level=Primary/elementary school | 0.005456 | 0.000268 |
| Education_Level=Professional degree (JD, MD, Ph.D, Ed.D, etc.) | -0.002072 | 0.000148 |
| Education_Level=Professional degree (JD, MD, etc.) | -0.000054 | 0.000061 |
| Education_Level=Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.) | 0.016081 | 0.000764 |
| Education_Level=Some college/university study without earning a degree | 0.004242 | 0.000701 |
| Education_Level=Something else | 0.002191 | 0.000124 |

Aggregated to the three original source features (standard deviations combined as root-sum-of-squares):

| Source feature | Mean decrease | Std |
| --- | --- | --- |
| Years_of_Experience | 0.013559 | 0.001506 |
| Yearly_Compensation | 0.024912 | 0.001558 |
| Education_Level | -0.000589 | 0.001458 |
