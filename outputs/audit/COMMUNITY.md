# Community and participation figure audit

The share columns below are the exact metric tables returned by the two existing figure functions. Wilson 95% confidence intervals use `wilson_interval` from `scripts.audit.generate_audit`. Response categories are shown after the whitespace trim used by the figures.

## Belonging, 2017-2025

| Year | n answered | n total | non-response rate | yes/agree count | yes/agree share | yes/agree Wilson 95% CI | no/disagree count | no/disagree share | no/disagree Wilson 95% CI | excluded count | excluded share | excluded Wilson 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2017 | 32410 | 51392 | 0.369357 | 20673 | 0.637859 | [0.632610, 0.643075] | 11737 | 0.362141 | [0.356925, 0.367390] | 0 | 0.000000 | [-0.000000, 0.000119] |
| 2018 | 76007 | 98855 | 0.231126 | 42146 | 0.554502 | [0.550965, 0.558032] | 33861 | 0.445498 | [0.441968, 0.449035] | 0 | 0.000000 | [0.000000, 0.000051] |
| 2019 | 88131 | 88883 | 0.008461 | 42754 | 0.485119 | [0.481820, 0.488419] | 27477 | 0.311775 | [0.308725, 0.314841] | 17900 | 0.203107 | [0.200464, 0.205776] |
| 2020 | 56476 | 64461 | 0.123873 | 24213 | 0.428731 | [0.424654, 0.432817] | 20545 | 0.363783 | [0.359825, 0.367760] | 11718 | 0.207486 | [0.204162, 0.210851] |
| 2021 | 82319 | 83439 | 0.013423 | 36472 | 0.443057 | [0.439666, 0.446453] | 28763 | 0.349409 | [0.346159, 0.352673] | 17084 | 0.207534 | [0.204777, 0.210318] |
| 2022 | 71408 | 73268 | 0.025386 | 30055 | 0.420891 | [0.417274, 0.424516] | 26424 | 0.370043 | [0.366508, 0.373591] | 14929 | 0.209066 | [0.206099, 0.212064] |
| 2023 | 87692 | 89184 | 0.016729 | 27022 | 0.308147 | [0.305099, 0.311211] | 41637 | 0.474810 | [0.471506, 0.478116] | 19033 | 0.217044 | [0.214328, 0.219785] |
| 2024 | 59163 | 65437 | 0.095878 | 20034 | 0.338624 | [0.334821, 0.342448] | 26575 | 0.449183 | [0.445178, 0.453194] | 12554 | 0.212193 | [0.208918, 0.215507] |
| 2025 | 31678 | 49123 | 0.355129 | 10424 | 0.329061 | [0.323908, 0.334256] | 14861 | 0.469127 | [0.463635, 0.474626] | 6393 | 0.201812 | [0.197429, 0.206268] |

## Participation at least a few times per month, 2019-2025

| Year | n answered | n total | non-response rate | frequent count | frequent share | frequent Wilson 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | 74692 | 88883 | 0.159659 | 26965 | 0.361016 | [0.357579, 0.364467] |
| 2020 | 46792 | 64461 | 0.274104 | 15933 | 0.340507 | [0.336226, 0.344814] |
| 2021 | 67553 | 83439 | 0.190391 | 22532 | 0.333546 | [0.330000, 0.337110] |
| 2022 | 58229 | 73268 | 0.205260 | 17885 | 0.307149 | [0.303415, 0.310909] |
| 2023 | 66061 | 89184 | 0.259273 | 14439 | 0.218571 | [0.215436, 0.221739] |
| 2024 | 45237 | 65437 | 0.308694 | 9932 | 0.219555 | [0.215764, 0.223393] |
| 2025 | 32200 | 49123 | 0.344503 | 3182 | 0.098820 | [0.095608, 0.102127] |

## Belonging raw-category mapping

| Year | Raw response category | Count | Mapped figure value |
| --- | --- | --- | --- |
| 2017 | Agree | 7212 | yes/agree |
| 2017 | Disagree | 9069 | no/disagree |
| 2017 | Somewhat agree | 10829 | yes/agree |
| 2017 | Strongly agree | 2632 | yes/agree |
| 2017 | Strongly disagree | 2668 | no/disagree |
| 2017 | <NULL or blank> | 18982 | non-response (excluded before figure calculation) |
| 2018 | I'm not sure | 16842 | no/disagree |
| 2018 | No | 17019 | no/disagree |
| 2018 | Yes | 42146 | yes/agree |
| 2018 | <NULL or blank> | 22848 | non-response (excluded before figure calculation) |
| 2019 | Neutral | 17900 | excluded (neither yes/agree nor no/disagree) |
| 2019 | No, not at all | 6447 | no/disagree |
| 2019 | No, not really | 19858 | no/disagree |
| 2019 | Not sure | 1172 | no/disagree |
| 2019 | Yes, definitely | 15302 | yes/agree |
| 2019 | Yes, somewhat | 27452 | yes/agree |
| 2019 | <NULL or blank> | 752 | non-response (excluded before figure calculation) |
| 2020 | Neutral | 11718 | excluded (neither yes/agree nor no/disagree) |
| 2020 | No, not at all | 4828 | no/disagree |
| 2020 | No, not really | 14672 | no/disagree |
| 2020 | Not sure | 1045 | no/disagree |
| 2020 | Yes, definitely | 8940 | yes/agree |
| 2020 | Yes, somewhat | 15273 | yes/agree |
| 2020 | <NULL or blank> | 7985 | non-response (excluded before figure calculation) |
| 2021 | Neutral | 17084 | excluded (neither yes/agree nor no/disagree) |
| 2021 | No, not at all | 6633 | no/disagree |
| 2021 | No, not really | 20697 | no/disagree |
| 2021 | Not sure | 1433 | no/disagree |
| 2021 | Yes, definitely | 12888 | yes/agree |
| 2021 | Yes, somewhat | 23584 | yes/agree |
| 2021 | <NULL or blank> | 1120 | non-response (excluded before figure calculation) |
| 2022 | Neutral | 14929 | excluded (neither yes/agree nor no/disagree) |
| 2022 | No, not at all | 6456 | no/disagree |
| 2022 | No, not really | 18728 | no/disagree |
| 2022 | Not sure | 1240 | no/disagree |
| 2022 | Yes, definitely | 10381 | yes/agree |
| 2022 | Yes, somewhat | 19674 | yes/agree |
| 2022 | <NULL or blank> | 1860 | non-response (excluded before figure calculation) |
| 2023 | Neutral | 19033 | excluded (neither yes/agree nor no/disagree) |
| 2023 | No, not at all | 11598 | no/disagree |
| 2023 | No, not really | 29100 | no/disagree |
| 2023 | Not sure | 939 | no/disagree |
| 2023 | Yes, definitely | 7996 | yes/agree |
| 2023 | Yes, somewhat | 19026 | yes/agree |
| 2023 | <NULL or blank> | 1492 | non-response (excluded before figure calculation) |
| 2024 | Neutral | 12554 | excluded (neither yes/agree nor no/disagree) |
| 2024 | No, not at all | 8193 | no/disagree |
| 2024 | No, not really | 17730 | no/disagree |
| 2024 | Not sure | 652 | no/disagree |
| 2024 | Yes, definitely | 6139 | yes/agree |
| 2024 | Yes, somewhat | 13895 | yes/agree |
| 2024 | <NULL or blank> | 6274 | non-response (excluded before figure calculation) |
| 2025 | Neutral | 6393 | excluded (neither yes/agree nor no/disagree) |
| 2025 | No, not at all | 4622 | no/disagree |
| 2025 | No, not really | 9943 | no/disagree |
| 2025 | Not sure | 296 | no/disagree |
| 2025 | Yes, definitely | 3036 | yes/agree |
| 2025 | Yes, somewhat | 7388 | yes/agree |
| 2025 | <NULL or blank> | 17445 | non-response (excluded before figure calculation) |

## Participation raw-category mapping

| Year | Raw response category | Count | Mapped figure value |
| --- | --- | --- | --- |
| 2019 | A few times per month or weekly | 14094 | frequent (at least a few times per month) |
| 2019 | A few times per week | 7040 | frequent (at least a few times per month) |
| 2019 | Daily or almost daily | 3695 | frequent (at least a few times per month) |
| 2019 | I have never participated in Q&A on Stack Overflow | 17287 | infrequent |
| 2019 | Less than once per month or monthly | 30440 | infrequent |
| 2019 | Multiple times per day | 2136 | frequent (at least a few times per month) |
| 2019 | <NULL or blank> | 14191 | non-response (excluded before figure calculation) |
| 2020 | A few times per month or weekly | 8317 | frequent (at least a few times per month) |
| 2020 | A few times per week | 4193 | frequent (at least a few times per month) |
| 2020 | Daily or almost daily | 2198 | frequent (at least a few times per month) |
| 2020 | I have never participated in Q&A on Stack Overflow | 10427 | infrequent |
| 2020 | Less than once per month or monthly | 20432 | infrequent |
| 2020 | Multiple times per day | 1225 | frequent (at least a few times per month) |
| 2020 | <NULL or blank> | 17669 | non-response (excluded before figure calculation) |
| 2021 | A few times per month or weekly | 12978 | frequent (at least a few times per month) |
| 2021 | A few times per week | 5687 | frequent (at least a few times per month) |
| 2021 | Daily or almost daily | 2613 | frequent (at least a few times per month) |
| 2021 | I have never participated in Q&A on Stack Overflow | 14243 | infrequent |
| 2021 | Less than once per month or monthly | 30778 | infrequent |
| 2021 | Multiple times per day | 1254 | frequent (at least a few times per month) |
| 2021 | <NULL or blank> | 15886 | non-response (excluded before figure calculation) |
| 2022 | A few times per month or weekly | 10559 | frequent (at least a few times per month) |
| 2022 | A few times per week | 4433 | frequent (at least a few times per month) |
| 2022 | Daily or almost daily | 1881 | frequent (at least a few times per month) |
| 2022 | I have never participated in Q&A on Stack Overflow | 13498 | infrequent |
| 2022 | Less than once per month or monthly | 26846 | infrequent |
| 2022 | Multiple times per day | 1012 | frequent (at least a few times per month) |
| 2022 | <NULL or blank> | 15039 | non-response (excluded before figure calculation) |
| 2023 | A few times per month or weekly | 9160 | frequent (at least a few times per month) |
| 2023 | A few times per week | 3285 | frequent (at least a few times per month) |
| 2023 | Daily or almost daily | 1309 | frequent (at least a few times per month) |
| 2023 | I have never participated in Q&A on Stack Overflow | 16961 | infrequent |
| 2023 | Less than once per month or monthly | 34661 | infrequent |
| 2023 | Multiple times per day | 685 | frequent (at least a few times per month) |
| 2023 | <NULL or blank> | 23123 | non-response (excluded before figure calculation) |
| 2024 | A few times per month or weekly | 6277 | frequent (at least a few times per month) |
| 2024 | A few times per week | 2278 | frequent (at least a few times per month) |
| 2024 | Daily or almost daily | 936 | frequent (at least a few times per month) |
| 2024 | I have never participated in Q&A on Stack Overflow | 11143 | infrequent |
| 2024 | Less than once per month or monthly | 24162 | infrequent |
| 2024 | Multiple times per day | 441 | frequent (at least a few times per month) |
| 2024 | <NULL or blank> | 20200 | non-response (excluded before figure calculation) |
| 2025 | A few times per month or weekly | 1906 | frequent (at least a few times per month) |
| 2025 | A few times per week | 759 | frequent (at least a few times per month) |
| 2025 | Daily or almost daily | 335 | frequent (at least a few times per month) |
| 2025 | I have never participated in Q&A on Stack Overflow | 9949 | infrequent |
| 2025 | Infrequently, less than once per year | 12057 | infrequent |
| 2025 | Less than once every 2 - 3 months | 4586 | infrequent |
| 2025 | Less than once per month or monthly | 2426 | infrequent |
| 2025 | Multiple times per day | 182 | frequent (at least a few times per month) |
| 2025 | <NULL or blank> | 16923 | non-response (excluded before figure calculation) |
