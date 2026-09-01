# Significance tests

## ASR comparisons — Fisher exact test on pooled triggered source-class samples

> Note: pooling assumes the triggered samples are independent across seeds. State in the paper whether the test split changes with the seed.

- **backdoor_fedavg/at2fb/blue/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **trigger_control/at2fb/blue/none** (6/45 = 0.1333; s42: 4/15, s123: 1/15, s2026: 1/15)  → Fisher exact two-sided p = 3.469e-19, odds ratio = inf
- **backdoor_fedavg/at2fb/full/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **trigger_control/at2fb/full/none** (7/45 = 0.1556; s42: 4/15, s123: 1/15, s2026: 2/15)  → Fisher exact two-sided p = 2.577e-18, odds ratio = inf
- **backdoor_fedavg/at2fb/red/none** (5/15 = 0.3333; s42: 5/15)  vs  **trigger_control/at2fb/red/none** (4/15 = 0.2667; s42: 4/15)  → Fisher exact two-sided p = 1, odds ratio = 1.38
- **backdoor_fedavg/at2fb/green/none** (5/15 = 0.3333; s42: 5/15)  vs  **trigger_control/at2fb/green/none** (4/15 = 0.2667; s42: 4/15)  → Fisher exact two-sided p = 1, odds ratio = 1.38
- **backdoor_fedavg/at2fb/blue/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_defense/at2fb/blue/multikrum** (23/45 = 0.5111; s42: 15/15, s123: 3/15, s2026: 5/15)  → Fisher exact two-sided p = 1.545e-08, odds ratio = inf
- **backdoor_fedavg/at2fb/full/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_defense/at2fb/full/multikrum** (27/45 = 0.6000; s42: 6/15, s123: 15/15, s2026: 6/15)  → Fisher exact two-sided p = 9.056e-07, odds ratio = inf
- **backdoor_fedavg/at2fb/blue/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_fedavg/at2fb/red/none** (5/15 = 0.3333; s42: 5/15)  → Fisher exact two-sided p = 3.983e-08, odds ratio = inf
- **backdoor_fedavg/at2fb/blue/none** (45/45 = 1.0000; s42: 15/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_fedavg/at2fb/green/none** (5/15 = 0.3333; s42: 5/15)  → Fisher exact two-sided p = 3.983e-08, odds ratio = inf

## Clean-performance comparisons — paired across seeds

> n = number of shared seeds. With n = 3 the two-sided Wilcoxon minimum p is 0.25 and the paired t-test has 2 df; these tests are low-powered and should be reported with that caveat.

- **clean_fl/-/none/none → backdoor_fedavg/at2fb/blue/none** on clean_acc (n = 3 seeds): mean diff = +0.0044 (sd 0.0407); paired t p = 0.8679 (df = 2); Wilcoxon p = 1. [s42: 0.8267→0.8400, s123: 0.8133→0.7733, s2026: 0.8400→0.8800]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/blue/none** on macro_f1 (n = 3 seeds): mean diff = +0.0065 (sd 0.0435); paired t p = 0.821 (df = 2); Wilcoxon p = 0.75. [s42: 0.8264→0.8395, s123: 0.8147→0.7747, s2026: 0.8355→0.8818]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/full/none** on clean_acc (n = 3 seeds): mean diff = +0.0000 (sd 0.0481); paired t p = 1 (df = 2); Wilcoxon p = 1. [s42: 0.8267→0.8400, s123: 0.8133→0.7600, s2026: 0.8400→0.8800]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/full/none** on macro_f1 (n = 3 seeds): mean diff = +0.0007 (sd 0.0518); paired t p = 0.9842 (df = 2); Wilcoxon p = 1. [s42: 0.8264→0.8401, s123: 0.8147→0.7583, s2026: 0.8355→0.8802]
- **backdoor_fedavg/at2fb/blue/none → backdoor_defense/at2fb/blue/multikrum** on clean_acc (n = 3 seeds): mean diff = -0.0133 (sd 0.0667); paired t p = 0.7628 (df = 2); Wilcoxon p = 0.75. [s42: 0.8400→0.8267, s123: 0.7733→0.8267, s2026: 0.8800→0.8000]
- **backdoor_fedavg/at2fb/full/none → backdoor_defense/at2fb/full/multikrum** on clean_acc (n = 3 seeds): mean diff = -0.0311 (sd 0.0539); paired t p = 0.4229 (df = 2); Wilcoxon p = 0.5. [s42: 0.8400→0.7600, s123: 0.7600→0.7867, s2026: 0.8800→0.8400]
