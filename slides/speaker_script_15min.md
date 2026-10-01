# Speaker script, 15 minutes

Channel-Aware Backdoor Attacks Against Federated Infostealer Malware Classification Using Dynamic API-Call and Network Representations. IWBIS 2026.

Pace: about 125 words per minute. The time after each slide title is how long to spend on it, and the clock time is where you should be when you leave the slide. Words in *italics* are cues, not text to read.

Pronunciation: StealC "steal-see"; Vidar "VEE-dar"; Multi-Krum "multi-KROOM"; AdamW "Adam-double-you"; ResNet18 "res-net eighteen"; RTX 3080 "R-T-X thirty-eighty"; IID "I-I-D".

---

## Slide 1. Title (0:20, clock 0:20)

Good morning, everyone. My name is Moh. Jabir Mubarok, from Institut Teknologi Sepuluh Nopember. Together with Mochamad Asryl Aziz and Eka Fitria, I will present our work on channel-aware backdoor attacks against federated infostealer malware classification.

## Slide 2. Background and Motivation (1:05, clock 1:25)

Infostealers target credentials, browser data and session cookies, which can enable account compromise. So knowing which infostealer family we are dealing with helps threat intelligence, triage and incident response.

To classify the family, dynamic analysis is useful. API-call sequences describe what the malware does on the host, and network artifacts describe how it communicates. Both can be turned into images and classified with a CNN.

Security data is spread across organizations, and they often cannot share raw samples. Federated learning lets them train one classifier together without moving the data. But the server only sees the updates the clients send, so a malicious client can inject a backdoor: a hidden rule that makes the model give a chosen wrong label whenever a small trigger appears.

## Slide 3. Research Problem and Objectives (1:10, clock 2:35)

Most backdoor research in federated learning looks at general image tasks or at model-level poisoning. It does not look at the channels of a malware representation. An RGB-stack representation, one image in which each data source gets its own color channel, puts API-call, network and fused information in separate channels. A trigger in one channel need not behave like a trigger in another, and this is still underexplored for dynamic malware representations.

First, we build dynamic API-call and network representations from Cuckoo Sandbox reports of five infostealer families. Second, we select the representation and the CNN architecture. Third, we evaluate channel-aware backdoor attacks in federated learning, with four triggers: red, green, blue, and full RGB. We add trigger controls and a Multi-Krum defense analysis.

*Point to the blue box at the bottom.* In one sentence, our idea is to treat the representation's channels as the attack surface.

## Slide 4. Overall Research Workflow (0:30, clock 3:05)

This is the overall workflow. We start from dynamic analysis reports, create the dataset, construct the representations and select the model. Then we run the federated learning experiments, evaluate the backdoor attacks, and finish with trigger controls and defenses. We report accuracy and macro-F1 throughout, and attack success rate for every attack.

## Slide 5. From Sandbox Reports to Image Tiles (1:10, clock 4:15)

*Left figure.* Each sample is run in Cuckoo Sandbox, and we take two artifacts from the report. API calls are mapped into behavior categories and counted over time, which gives a 16 by 16 category-by-time tile. On the network side, we keep only the session with the largest payload, to reduce leakage between samples. We reshape it into a 28 by 28 tile.

*Right figure.* Here are the resulting images for the five families. We compare two ways of combining the tiles. Opacity blend mixes both sources into every channel. RGB-stack keeps them apart: red is the API tile, green is the network tile, and blue is an edge map of their average.

So blue adds no new information, and it is the emptiest channel: almost 63 percent of its pixels are exactly zero. Keep that in mind; it comes back at the end.

## Slide 6. Dataset Creation (0:25, clock 4:40)

The dataset has five families, AgentTesla, FormBook, SalatStealer, StealC and Vidar, with 100 samples each, so 500 in total. We split it 70, 15 and 15 percent into training, validation and test, stratified by family, and we draw a new split for each seed.

## Slide 7. Channel-Aware Backdoor in Federated Learning (1:05, clock 5:45)

We use one server and five clients. Each client holds 70 images, 14 per family, so the partition is balanced and IID. The server aggregates the updates with FedAvg.

One client is malicious and runs a targeted backdoor. It puts a small white square trigger on AgentTesla training images and relabels them as FormBook. The poison rate is 20 percent of its 14 AgentTesla images, so only two images per round, resampled every round. It is pure data poisoning, with no update scaling and no model replacement.

Attack success rate is how many of the 15 AgentTesla test images, with the trigger added, the model labels as FormBook. Because RGB-stack keeps the channels separate, we can put the trigger in red, green, blue, or all three, and compare them.

## Slide 8. Training, Defense and Evaluation (1:10, clock 6:55)

*Left tables.* Training runs in PyTorch on an RTX 3080, and the federated learning is a simulation we implemented ourselves in PyTorch. The model is trained from scratch with AdamW and batch size 16. The learning rate and the weight decay are both ten to the minus four. We run 50 federated rounds, with two local epochs per round.

*Right box.* We report the final-round global model, with no best-validation selection, and we measure clean accuracy, macro-F1 and attack success rate over three seeds: 42, 123 and 2026.

For defense, Multi-Krum is our main robust-aggregation baseline. It scores each update by its distance to the others and keeps the most central ones. We also screen clipping, coordinate-wise median and trimmed mean. As a control, we apply the same triggers at test time to a clean model that never saw poisoned data.

## Slide 9. Backbone Selection Results (0:35, clock 7:30)

Now the results. First, the model. Within RGB-stack, measured on seed 42, ResNet18 is the strongest backbone, at about 79 percent on both accuracy and macro-F1, so we use it for everything that follows. The opacity-blend rows come from a different data split, so they are for reference only, not a head-to-head comparison. We chose RGB-stack because we need the channels to be separate.

## Slide 10. Channel-Aware Backdoor Sweep (1:10, clock 8:40)

This is the central result. On seed 42, we put the same trigger into each channel in turn.

Red, the API channel, and green, the network channel, reach only five out of fifteen, 33 percent. Their trigger controls give four out of fifteen, and the difference is not significant, so on that seed they are indistinguishable from the model's natural confusion.

Blue and full RGB reach 100 percent. Clean accuracy stays at 84 to 85 percent in every case, so the model still looks healthy.

The striking part is blue. A trigger in the fusion channel alone is as effective as a trigger across all three channels. And the difference is categorical: pooled over the three seeds, blue and full RGB differ from their controls with p-values below ten to the minus seventeen.

## Slide 11. Defense Screening (0:40, clock 9:20)

Can standard defenses stop it? We first screened four defenses on seed 42. Clipping, coordinate-wise median and trimmed mean all leave the attack success rate at 100 percent for both triggers. Only Multi-Krum reduces it, and only for full RGB: from 100 to 40 percent, with clean accuracy dropping from 84 to 76 percent on this seed. Against the blue trigger, even Multi-Krum stays at 100 percent. So Multi-Krum is the only defense we carried into the multi-seed evaluation.

## Slide 12. Multi-Seed Results (1:25, clock 10:45)

*Point to the highlighted rows.* Over three seeds, under FedAvg, both the blue and the full-RGB backdoors reach fifteen out of fifteen on every seed. Clean accuracy stays comparable to the clean baseline, at about 83 percent.

For transparency: the seed-42 clean baseline and its trigger controls come from a shorter run, 30 rounds with one local epoch. Re-trained at the full budget, the control rate is six out of fifteen instead of four. No attack success result is affected.

Across all eight controls, the six in this table plus red and green on seed 42, seven give exactly the same target rate with and without the trigger. So the attack success comes from poisoning, not from the pattern.

Now the Multi-Krum rows. The means, 51 and 60 percent, look like partial protection, but they are misleading. Per seed, blue gives 15, 3 and 5 out of 15, and full RGB gives 6, 15 and 6. On one seed out of three, the backdoor is fully effective. I will come back to this after the training curves.

## Slide 13. Clean Macro-F1 and ASR over FL Rounds (0:35, clock 11:20)

These curves show the same story during training, for seed 42. On the left, the clean macro-F1 of the backdoored models tracks the clean baseline. On the right, the attack success rate climbs to 100 percent in the later rounds. The high values in the first few rounds mean nothing: the model is still almost untrained and predicts only one or two classes.

## Slide 14. Defense Analysis: Bimodal Rather Than Partial (1:10, clock 12:30)

This figure shows the blue and full-RGB backdoors under FedAvg and under Multi-Krum, across the three seeds. *Bottom panel.* Under FedAvg, both triggers settle at 100 percent. Under Multi-Krum, the curves stay unstable. The outcome is bimodal: on a given seed, the backdoor is either mostly suppressed or not suppressed at all.

It tracks selection. Multi-Krum keeps two of the five updates in each round. The poisoned update is not an outlier in parameter space, so whether it is kept is close to a coin flip. Across the six Multi-Krum runs, the malicious client was kept in 8 to 50 percent of the rounds, and that rate correlates with the final attack success, with a correlation of 0.89. With only six runs, this is indicative rather than conclusive.

So Multi-Krum lowers the attack success on average, but it is unreliable as a standalone defense.

## Slide 15. The Blue/Fusion Channel (1:00, clock 13:30)

Finally, why does blue work when red and green do not? Inside the trigger region of the clean images, red is already very bright, with a mean of 214.6. And 37.7 percent of its pixels are already at 254 or above, where a white trigger changes nothing at all. Green's mean is only 48.3, so a white trigger adds a contrast of about 207, and green still fails.

Blue's mean is just 21.6. It cannot win through new information, because it is computed from red and green. What distinguishes it is that it is almost empty, so the trigger is the only strong signal there. This explanation fits our measurements, but it is not proven; a contrast-matched trigger would test it.

## Slide 16. Conclusion and Future Work (1:20, clock 14:50)

The main message is that the channels of this representation are an attack surface. A trigger in the fusion channel alone matches one spanning all three channels, even though that channel is derived from the other two.

Blue and full-RGB triggers reached 100 percent attack success across three seeds, with clean performance close to the baseline, and the trigger controls show that the effect comes from poisoning. Multi-Krum reduced the attack only bimodally: for each trigger, it left the backdoor fully effective on one of the three seeds.

So, in this controlled IID setting, channel-aware backdoors are a serious threat to federated malware classifiers. They motivate defenses that look at the representation, not only at the updates.

Our main limitations are the IID-only partition, a single source-target pair, and three seeds, with the red and green results on seed 42 only. The next steps are a non-IID partition, a second source-target pair, and a contrast-matched trigger.

## Slide 17. Thank you (0:10, clock 15:00)

Thank you for your attention. I am happy to take your questions.
