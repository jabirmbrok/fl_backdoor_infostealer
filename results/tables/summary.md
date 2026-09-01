# Results summary

Std uses ddof = 1 (as in the paper). ASR per seed = hits/n; pooled = sum(hits)/sum(n).

| Scenario | Variant | Channel | Defense | Seeds | Clean acc | Macro-F1 | ASR | ASR pooled | ASR per seed | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| backbone_sel | opacity_blend-mobilenet_v2 | none | none | 1 (42) | 0.6933 | 0.6903 | – |  |  |  |
| backbone_sel | opacity_blend-resnet18 | none | none | 1 (42) | 0.7733 | 0.7730 | – |  |  |  |
| backbone_sel | opacity_blend-small_cnn | none | none | 1 (42) | 0.5333 | 0.5298 | – |  |  |  |
| backbone_sel | rgb_stack-mobilenet_v2 | none | none | 1 (42) | 0.7200 | 0.7200 | – |  |  |  |
| backbone_sel | rgb_stack-resnet18 | none | none | 1 (42) | 0.7867 | 0.7884 | – |  |  |  |
| backbone_sel | rgb_stack-small_cnn | none | none | 1 (42) | 0.5200 | 0.5144 | – |  |  |  |
| clean_fl | - | none | none | 3 (42 123 2026) | 0.8267 ± 0.0134 | 0.8255 ± 0.0104 | – |  |  |  |
| clean_fl | r50 | none | none | 1 (42) | 0.7867 | 0.7869 | – |  |  |  |
| trigger_control | at2fb | red | none | 1 (42) | 0.8267 | 0.8264 | 0.2667 | 4/15 | 4/15 |  |
| trigger_control | at2fb | green | none | 1 (42) | 0.8267 | 0.8264 | 0.2667 | 4/15 | 4/15 |  |
| trigger_control | at2fb | blue | none | 3 (42 123 2026) | 0.8267 ± 0.0134 | 0.8255 ± 0.0104 | 0.1333 ± 0.1155 | 6/45 | 4/15, 1/15, 1/15 |  |
| trigger_control | at2fb | full | none | 3 (42 123 2026) | 0.8267 ± 0.0134 | 0.8255 ± 0.0104 | 0.1556 ± 0.1018 | 7/45 | 4/15, 1/15, 2/15 |  |
| trigger_control | at2fb-r50 | red | none | 1 (42) | 0.7867 | 0.7869 | 0.4000 | 6/15 | 6/15 |  |
| trigger_control | at2fb-r50 | green | none | 1 (42) | 0.7867 | 0.7869 | 0.4000 | 6/15 | 6/15 |  |
| trigger_control | at2fb-r50 | blue | none | 1 (42) | 0.7867 | 0.7869 | 0.4000 | 6/15 | 6/15 |  |
| trigger_control | at2fb-r50 | full | none | 1 (42) | 0.7867 | 0.7869 | 0.4000 | 6/15 | 6/15 |  |
| backdoor_fedavg | at2fb | red | none | 1 (42) | 0.8533 | 0.8524 | 0.3333 | 5/15 | 5/15 |  |
| backdoor_fedavg | at2fb | green | none | 1 (42) | 0.8400 | 0.8419 | 0.3333 | 5/15 | 5/15 |  |
| backdoor_fedavg | at2fb | blue | none | 3 (42 123 2026) | 0.8311 ± 0.0539 | 0.8320 ± 0.0539 | 1.0000 ± 0.0000 | 45/45 | 15/15, 15/15, 15/15 |  |
| backdoor_fedavg | at2fb | full | none | 3 (42 123 2026) | 0.8267 ± 0.0611 | 0.8262 ± 0.0621 | 1.0000 ± 0.0000 | 45/45 | 15/15, 15/15, 15/15 |  |
| backdoor_fedavg | at2fb-p10 | red | none | 1 (42) | 0.8267 | 0.8261 | 0.3333 | 5/15 | 5/15 |  |
| backdoor_fedavg | at2fb-p30-s12 | red | none | 1 (42) | 0.8133 | 0.8103 | 0.3333 | 5/15 | 5/15 |  |
| backdoor_fedavg | at2fb-p30-s12 | full | none | 1 (42) | 0.8400 | 0.8403 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | blue | clipping | 1 (42) | 0.8533 | 0.8550 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | blue | median | 1 (42) | 0.8133 | 0.8120 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | blue | trimmed_mean | 1 (42) | 0.8267 | 0.8244 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | blue | multikrum | 3 (42 123 2026) | 0.8178 ± 0.0154 | 0.8184 ± 0.0135 | 0.5111 ± 0.4286 | 23/45 | 15/15, 3/15, 5/15 | ASR range ≥ 0.5 across seeds — describe as bimodal/unstable, not as a mean |
| backdoor_defense | at2fb | full | clipping | 1 (42) | 0.8533 | 0.8550 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | full | median | 1 (42) | 0.8400 | 0.8388 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | full | trimmed_mean | 1 (42) | 0.8133 | 0.8145 | 1.0000 | 15/15 | 15/15 |  |
| backdoor_defense | at2fb | full | multikrum | 3 (42 123 2026) | 0.7956 ± 0.0407 | 0.7931 ± 0.0427 | 0.6000 ± 0.3464 | 27/45 | 6/15, 15/15, 6/15 | ASR range ≥ 0.5 across seeds — describe as bimodal/unstable, not as a mean |

## Per-seed values

| exp_id | Scenario | Variant | Channel | Defense | Seed | Clean acc | Macro-F1 | ASR |
|---|---|---|---|---|---|---|---|---|
| backbone_opacity_blend_mobilenet_v2_seed42 | backbone_sel | opacity_blend-mobilenet_v2 | none | none | 42 | 0.6933 | 0.6903 |  |
| backbone_opacity_blend_resnet18_seed42 | backbone_sel | opacity_blend-resnet18 | none | none | 42 | 0.7733 | 0.7730 |  |
| backbone_opacity_blend_small_cnn_seed42 | backbone_sel | opacity_blend-small_cnn | none | none | 42 | 0.5333 | 0.5298 |  |
| backbone_rgb_stack_mobilenet_v2_seed42 | backbone_sel | rgb_stack-mobilenet_v2 | none | none | 42 | 0.7200 | 0.7200 |  |
| backbone_rgb_stack_resnet18_seed42 | backbone_sel | rgb_stack-resnet18 | none | none | 42 | 0.7867 | 0.7884 |  |
| backbone_rgb_stack_small_cnn_seed42 | backbone_sel | rgb_stack-small_cnn | none | none | 42 | 0.5200 | 0.5144 |  |
| defense_blue_clipping | backdoor_defense | at2fb | blue | clipping | 42 | 0.8533 | 0.8550 | 15/15 = 1.0000 |
| defense_blue_median | backdoor_defense | at2fb | blue | median | 42 | 0.8133 | 0.8120 | 15/15 = 1.0000 |
| defense_blue_multi_krum | backdoor_defense | at2fb | blue | multikrum | 42 | 0.8267 | 0.8244 | 15/15 = 1.0000 |
| defense_blue_multi_krum_seed123 | backdoor_defense | at2fb | blue | multikrum | 123 | 0.8267 | 0.8279 | 3/15 = 0.2000 |
| defense_blue_multi_krum_seed2026 | backdoor_defense | at2fb | blue | multikrum | 2026 | 0.8000 | 0.8030 | 5/15 = 0.3333 |
| defense_blue_trimmed_mean | backdoor_defense | at2fb | blue | trimmed_mean | 42 | 0.8267 | 0.8244 | 15/15 = 1.0000 |
| defense_full_clipping | backdoor_defense | at2fb | full | clipping | 42 | 0.8533 | 0.8550 | 15/15 = 1.0000 |
| defense_full_median | backdoor_defense | at2fb | full | median | 42 | 0.8400 | 0.8388 | 15/15 = 1.0000 |
| defense_full_multi_krum | backdoor_defense | at2fb | full | multikrum | 42 | 0.7600 | 0.7542 | 6/15 = 0.4000 |
| defense_full_multi_krum_seed123 | backdoor_defense | at2fb | full | multikrum | 123 | 0.7867 | 0.7864 | 15/15 = 1.0000 |
| defense_full_multi_krum_seed2026 | backdoor_defense | at2fb | full | multikrum | 2026 | 0.8400 | 0.8388 | 6/15 = 0.4000 |
| defense_full_trimmed_mean | backdoor_defense | at2fb | full | trimmed_mean | 42 | 0.8133 | 0.8145 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_blue_p20_s10_r50 | backdoor_fedavg | at2fb | blue | none | 42 | 0.8400 | 0.8395 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_blue_p20_s10_seed123 | backdoor_fedavg | at2fb | blue | none | 123 | 0.7733 | 0.7747 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_blue_p20_s10_seed2026 | backdoor_fedavg | at2fb | blue | none | 2026 | 0.8800 | 0.8818 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_full_p20_s10_r50 | backdoor_fedavg | at2fb | full | none | 42 | 0.8400 | 0.8401 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_full_p20_s10_seed123 | backdoor_fedavg | at2fb | full | none | 123 | 0.7600 | 0.7583 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_full_p20_s10_seed2026 | backdoor_fedavg | at2fb | full | none | 2026 | 0.8800 | 0.8802 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_green_p20_s10_r50 | backdoor_fedavg | at2fb | green | none | 42 | 0.8400 | 0.8419 | 5/15 = 0.3333 |
| fl_backdoor_rgb_resnet18_red_p20_s10_r50 | backdoor_fedavg | at2fb | red | none | 42 | 0.8533 | 0.8524 | 5/15 = 0.3333 |
| fl_backdoor_rgb_resnet18_api_trigger_seed42 | backdoor_fedavg | at2fb-p10 | red | none | 42 | 0.8267 | 0.8261 | 5/15 = 0.3333 |
| fl_backdoor_rgb_resnet18_full_p30_s12_r50 | backdoor_fedavg | at2fb-p30-s12 | full | none | 42 | 0.8400 | 0.8403 | 15/15 = 1.0000 |
| fl_backdoor_rgb_resnet18_red_p30_s12_r50 | backdoor_fedavg | at2fb-p30-s12 | red | none | 42 | 0.8133 | 0.8103 | 5/15 = 0.3333 |
| fl_clean_rgb_resnet18_iid_seed42 | clean_fl | - | none | none | 42 | 0.8267 | 0.8264 |  |
| fl_clean_rgb_resnet18_iid_seed123 | clean_fl | - | none | none | 123 | 0.8133 | 0.8147 |  |
| fl_clean_rgb_resnet18_iid_seed2026 | clean_fl | - | none | none | 2026 | 0.8400 | 0.8355 |  |
| fl_clean_rgb_resnet18_iid_seed42_r50 | clean_fl | r50 | none | none | 42 | 0.7867 | 0.7869 |  |
| clean_model_blue_trigger_control | trigger_control | at2fb | blue | none | 42 | 0.8267 | 0.8264 | 4/15 = 0.2667 |
| clean_model_blue_trigger_control_seed123 | trigger_control | at2fb | blue | none | 123 | 0.8133 | 0.8147 | 1/15 = 0.0667 |
| clean_model_blue_trigger_control_seed2026 | trigger_control | at2fb | blue | none | 2026 | 0.8400 | 0.8355 | 1/15 = 0.0667 |
| clean_model_full_trigger_control | trigger_control | at2fb | full | none | 42 | 0.8267 | 0.8264 | 4/15 = 0.2667 |
| clean_model_full_trigger_control_seed123 | trigger_control | at2fb | full | none | 123 | 0.8133 | 0.8147 | 1/15 = 0.0667 |
| clean_model_full_trigger_control_seed2026 | trigger_control | at2fb | full | none | 2026 | 0.8400 | 0.8355 | 2/15 = 0.1333 |
| clean_model_green_trigger_control | trigger_control | at2fb | green | none | 42 | 0.8267 | 0.8264 | 4/15 = 0.2667 |
| clean_model_red_trigger_control | trigger_control | at2fb | red | none | 42 | 0.8267 | 0.8264 | 4/15 = 0.2667 |
| clean_model_blue_trigger_control_r50 | trigger_control | at2fb-r50 | blue | none | 42 | 0.7867 | 0.7869 | 6/15 = 0.4000 |
| clean_model_full_trigger_control_r50 | trigger_control | at2fb-r50 | full | none | 42 | 0.7867 | 0.7869 | 6/15 = 0.4000 |
| clean_model_green_trigger_control_r50 | trigger_control | at2fb-r50 | green | none | 42 | 0.7867 | 0.7869 | 6/15 = 0.4000 |
| clean_model_red_trigger_control_r50 | trigger_control | at2fb-r50 | red | none | 42 | 0.7867 | 0.7869 | 6/15 = 0.4000 |
