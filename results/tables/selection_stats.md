# Multi-Krum: how often the malicious client survives selection

Attacker = client 0. `selected_clients` is logged per round in results/defense_*/history.json.

| Run | Rounds | Malicious selected | Rate | First half | Last half | Final ASR |
|---|---|---|---|---|---|---|
| defense_blue_multi_krum | 50 | 25 | 50% | 15 | 10 | 15/15 = 1.0000 |
| defense_blue_multi_krum_seed123 | 50 | 4 | 8% | 1 | 3 | 3/15 = 0.2000 |
| defense_blue_multi_krum_seed2026 | 50 | 16 | 32% | 10 | 6 | 5/15 = 0.3333 |
| defense_full_multi_krum | 50 | 14 | 28% | 12 | 2 | 6/15 = 0.4000 |
| defense_full_multi_krum_seed123 | 50 | 22 | 44% | 11 | 11 | 15/15 = 1.0000 |
| defense_full_multi_krum_seed2026 | 50 | 9 | 18% | 6 | 3 | 6/15 = 0.4000 |

Selection rate vs final ASR (n = 6): Spearman rho = 0.794 (p = 0.0590), Pearson r = 0.893 (p = 0.0166).

Reading: Multi-Krum does not fail or succeed as a property of the channel — it fails in the seeds where the poisoned update happens to stay inside the selected subset often enough. With f = 1 and m = 2 out of 5 clients, that is a coin flip the attacker only has to win sometimes. This is the mechanism behind the bimodal ASR across seeds, and it is what the paper should report instead of an average ASR.
