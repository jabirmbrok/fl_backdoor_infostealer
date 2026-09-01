# Per-channel intensity statistics of clean RGB-stack images

Images: 500; trigger side = 10% of the image (≈13 px); trigger value assumed = 255.

Contrast = |trigger value − mean intensity of the channel inside the bottom-right trigger region|. The channel with the largest contrast is where a bright square trigger is most salient.

| Family | n | R mean | G mean | B mean | R contrast | G contrast | B contrast | R already-white | G already-white | B already-white | G all-zero (no traffic) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AgentTesla | 100 | 238.9 | 109.8 | 11.9 | 20.0 | 149.3 | 225.9 | 53.6% | 0.5% | 0.0% | 0.0% |
| FormBook | 100 | 238.6 | 84.1 | 10.8 | 55.3 | 185.1 | 231.7 | 24.1% | 0.4% | 0.0% | 0.0% |
| SalatStealer | 100 | 240.4 | 63.4 | 9.1 | 37.1 | 247.2 | 237.3 | 36.3% | 0.1% | 0.0% | 0.0% |
| StealC | 100 | 244.2 | 63.8 | 9.0 | 53.8 | 246.8 | 238.9 | 24.4% | 0.1% | 0.0% | 0.0% |
| Vidar | 100 | 246.6 | 86.7 | 10.3 | 35.5 | 204.9 | 233.1 | 49.8% | 0.2% | 0.0% | 0.0% |
| ALL | 500 | 241.7 | 81.5 | 10.2 | 40.4 | 206.7 | 233.4 | 37.7% | 0.3% | 0.0% | 0.0% |

Contrast ranking over all images: B > G > R.
"already-white" is the share of trigger-region pixels that are already >= 254 in that channel, i.e. where writing the trigger changes nothing at all.

Read this together with the measured ASR ordering (blue = full > red = green). Contrast alone predicts B > G > R, so it explains why the red trigger is nearly invisible, but not why green fails despite high contrast. The Tier 3 contrast-matched trigger separates the two explanations.
