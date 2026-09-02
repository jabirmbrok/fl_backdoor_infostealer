# Significance tests

## ASR comparisons — Fisher exact test on pooled triggered source-class samples

> Note: pooling assumes the triggered samples are independent across seeds. State in the paper whether the test split changes with the seed.

- **backdoor_fedavg/at2fb/blue/none** (67/75 = 0.8933; s7: 12/15, s42: 15/15, s99: 10/15, s123: 15/15, s2026: 15/15)  vs  **trigger_control/at2fb/blue/none** (10/75 = 0.1333; s7: 2/15, s42: 4/15, s99: 2/15, s123: 1/15, s2026: 1/15)  → Fisher exact two-sided p = 3.235e-22, odds ratio = 54.4
- **backdoor_fedavg/at2fb/full/none** (71/75 = 0.9467; s7: 15/15, s42: 15/15, s99: 11/15, s123: 15/15, s2026: 15/15)  vs  **trigger_control/at2fb/full/none** (11/75 = 0.1467; s7: 2/15, s42: 4/15, s99: 2/15, s123: 1/15, s2026: 2/15)  → Fisher exact two-sided p = 2.48e-25, odds ratio = 103
- **backdoor_fedavg/at2fb/red/none** (8/45 = 0.1778; s42: 5/15, s123: 1/15, s2026: 2/15)  vs  **trigger_control/at2fb/red/none** (6/45 = 0.1333; s42: 4/15, s123: 1/15, s2026: 1/15)  → Fisher exact two-sided p = 0.7722, odds ratio = 1.41
- **backdoor_fedavg/at2fb/green/none** (10/45 = 0.2222; s42: 5/15, s123: 2/15, s2026: 3/15)  vs  **trigger_control/at2fb/green/none** (6/45 = 0.1333; s42: 4/15, s123: 1/15, s2026: 1/15)  → Fisher exact two-sided p = 0.4089, odds ratio = 1.86
- **backdoor_fedavg/at2fb/blue/none** (67/75 = 0.8933; s7: 12/15, s42: 15/15, s99: 10/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_defense/at2fb/blue/multikrum** (40/75 = 0.5333; s7: 15/15, s42: 15/15, s99: 2/15, s123: 3/15, s2026: 5/15)  → Fisher exact two-sided p = 1.476e-06, odds ratio = 7.33
- **backdoor_fedavg/at2fb/full/none** (71/75 = 0.9467; s7: 15/15, s42: 15/15, s99: 11/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_defense/at2fb/full/multikrum** (57/75 = 0.7600; s7: 15/15, s42: 6/15, s99: 15/15, s123: 15/15, s2026: 6/15)  → Fisher exact two-sided p = 0.002093, odds ratio = 5.61
- **backdoor_fedavg/at2fb/blue/none** (67/75 = 0.8933; s7: 12/15, s42: 15/15, s99: 10/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_fedavg/at2fb/red/none** (8/45 = 0.1778; s42: 5/15, s123: 1/15, s2026: 2/15)  → Fisher exact two-sided p = 1.654e-15, odds ratio = 38.7
- **backdoor_fedavg/at2fb/blue/none** (67/75 = 0.8933; s7: 12/15, s42: 15/15, s99: 10/15, s123: 15/15, s2026: 15/15)  vs  **backdoor_fedavg/at2fb/green/none** (10/45 = 0.2222; s42: 5/15, s123: 2/15, s2026: 3/15)  → Fisher exact two-sided p = 7.294e-14, odds ratio = 29.3

## Clean-performance comparisons — paired across seeds

> n = number of shared seeds. With n = 3 the two-sided Wilcoxon minimum p is 0.25 and the paired t-test has 2 df; these tests are low-powered and should be reported with that caveat.

- **clean_fl/-/none/none → backdoor_fedavg/at2fb/blue/none** on clean_acc (n = 5 seeds): mean diff = +0.0267 (sd 0.0422); paired t p = 0.2303 (df = 4); Wilcoxon p = 0.25. [s7: 0.7600→0.8267, s42: 0.8267→0.8400, s99: 0.8000→0.8533, s123: 0.8133→0.7733, s2026: 0.8400→0.8800]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/blue/none** on macro_f1 (n = 5 seeds): mean diff = +0.0263 (sd 0.0411); paired t p = 0.2261 (df = 4); Wilcoxon p = 0.1875. [s7: 0.7679→0.8275, s42: 0.8264→0.8395, s99: 0.8007→0.8531, s123: 0.8147→0.7747, s2026: 0.8355→0.8818]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/full/none** on clean_acc (n = 5 seeds): mean diff = +0.0160 (sd 0.0415); paired t p = 0.4373 (df = 4); Wilcoxon p = 0.5. [s7: 0.7600→0.8133, s42: 0.8267→0.8400, s99: 0.8000→0.8267, s123: 0.8133→0.7600, s2026: 0.8400→0.8800]
- **clean_fl/-/none/none → backdoor_fedavg/at2fb/full/none** on macro_f1 (n = 5 seeds): mean diff = +0.0150 (sd 0.0421); paired t p = 0.4703 (df = 4); Wilcoxon p = 0.625. [s7: 0.7679→0.8140, s42: 0.8264→0.8401, s99: 0.8007→0.8276, s123: 0.8147→0.7583, s2026: 0.8355→0.8802]
- **backdoor_fedavg/at2fb/blue/none → backdoor_defense/at2fb/blue/multikrum** on clean_acc (n = 5 seeds): mean diff = -0.0240 (sd 0.0503); paired t p = 0.3462 (df = 4); Wilcoxon p = 0.4375. [s7: 0.8267→0.8000, s42: 0.8400→0.8267, s99: 0.8533→0.8000, s123: 0.7733→0.8267, s2026: 0.8800→0.8000]
- **backdoor_fedavg/at2fb/full/none → backdoor_defense/at2fb/full/multikrum** on clean_acc (n = 5 seeds): mean diff = -0.0267 (sd 0.0389); paired t p = 0.2001 (df = 4); Wilcoxon p = 0.25. [s7: 0.8133→0.8000, s42: 0.8400→0.7600, s99: 0.8267→0.8000, s123: 0.7600→0.7867, s2026: 0.8800→0.8400]
