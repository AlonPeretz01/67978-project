# Random-forest held-out evaluation

Target: **Part of the Stack Overflow community**. Target-covered years: **2022**. AI-related variable ever included as a feature: **NO**; the feature list is exactly `Years_of_Experience`, `Yearly_Compensation`, and `Education_Level`.

Stratified split: random_state=42, train n=49117, test n=21051.

| Metric | Test-set value |
| --- | --- |
| accuracy | 0.541542 |
| precision | 0.469682 |
| recall | 0.544638 |
| f1 | 0.504391 |
| roc_auc | 0.547923 |
| majority_class_accuracy | 0.571659 |

Permutation importance uses test-set accuracy, n_repeats=10, random_state=42. Encoded-feature results:

| Encoded feature | Mean decrease | Std |
| --- | --- | --- |
| Years_of_Experience | 0.022731 | 0.002354 |
| Yearly_Compensation | 0.032602 | 0.002232 |
| Education_Level=Associate degree (A.A., A.S., etc.) | -0.000979 | 0.000339 |
| Education_Level=Bachelor’s degree (B.A., B.S., B.Eng., etc.) | -0.008484 | 0.001447 |
| Education_Level=Master’s degree (M.A., M.S., M.Eng., MBA, etc.) | -0.001682 | 0.001334 |
| Education_Level=Other doctoral degree (Ph.D., Ed.D., etc.) | 0.000936 | 0.000279 |
| Education_Level=Primary/elementary school | -0.000504 | 0.000532 |
| Education_Level=Professional degree (JD, MD, etc.) | -0.000385 | 0.000155 |
| Education_Level=Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.) | -0.001615 | 0.001053 |
| Education_Level=Some college/university study without earning a degree | -0.003857 | 0.000795 |
| Education_Level=Something else | -0.000542 | 0.000252 |

Aggregated to the three original source features (standard deviations combined as root-sum-of-squares):

| Source feature | Mean decrease | Std |
| --- | --- | --- |
| Years_of_Experience | 0.022731 | 0.002354 |
| Yearly_Compensation | 0.032602 | 0.002232 |
| Education_Level | -0.017111 | 0.002485 |
