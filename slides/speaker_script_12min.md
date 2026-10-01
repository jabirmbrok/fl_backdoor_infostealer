# Speaker script, 12 minutes

Channel-Aware Backdoor Attacks Against Federated Infostealer Malware Classification Using Dynamic API-Call and Network Representations. IWBIS 2026.

Pace: about 125 words per minute. The time after each slide title is how long to spend on it, and the clock time is where you should be when you leave the slide. The talk ends at 11:40, which leaves 20 seconds of slack inside a 12-minute slot, on top of the few seconds each slide's time already allows for changing slides. Words in *italics* are cues, not text to read.

This is the 15-minute script with three slides moved to the backup section (dataset table, backbone selection, seed-42 training curves) and the remaining sections tightened. What was cut from the spoken text is kept in each slide's Q&A notes in the deck.

Pronunciation: StealC "steal-see"; Vidar "VEE-dar"; Multi-Krum "multi-KROOM"; AdamW "Adam-double-you"; ResNet18 "res-net eighteen"; IID "I-I-D".

---

## Slide 1. Title (0:20, clock 0:20)

Good morning, everyone. My name is Moh. Jabir Mubarok, from Institut Teknologi Sepuluh Nopember. Together with Mochamad Asryl Aziz and Eka Fitria, I will present our work on channel-aware backdoor attacks against federated infostealer malware classification.

## Slide 2. Background and Motivation (0:50, clock 1:10)

Infostealers steal credentials, browser data and session cookies, so knowing which infostealer family we are dealing with helps threat intelligence, triage and incident response.

To classify the family, we use dynamic analysis. API-call sequences describe what the malware does on the host, and network artifacts describe how it communicates. Both can be turned into images and classified with a CNN.

Organizations often cannot share raw samples. Federated learning lets them train one classifier together without moving the data. But a malicious client can inject a backdoor: a hidden rule that makes the model give a chosen wrong label whenever a small trigger appears.

## Slide 3. Research Problem and Objectives (1:00, clock 2:10)

Most backdoor research in federated learning looks at general image tasks or at model-level poisoning, not at the channels of a malware representation. In an RGB-stack representation, each data source gets its own color channel, so a trigger in one channel need not behave like a trigger in another. This is still underexplored for dynamic malware representations.

So we have three objectives. First, we build API-call and network representations from Cuckoo Sandbox reports of five infostealer families. Second, we select the representation and the CNN architecture. Third, we evaluate channel-aware backdoor attacks in federated learning, with trigger controls and a Multi-Krum defense analysis.

*Point to the blue box at the bottom.* In one sentence, our idea is to treat the representation's channels as the attack surface.

## Slide 4. Overall Research Workflow (0:20, clock 2:30)

This is the overall workflow. From dynamic analysis reports we create the dataset, construct the representations and select the model. Then we run the federated learning experiments, evaluate the backdoor attacks, and finish with trigger controls and defenses.

## Slide 5. From Sandbox Reports to Image Tiles (1:10, clock 3:40)

*Left figure.* Each sample is run in Cuckoo Sandbox. API calls are mapped into behavior categories and counted over time, which gives a 16 by 16 tile. On the network side, we keep only the session with the largest payload, and reshape it into a 28 by 28 tile.

*Right figure.* Here are the resulting images for the five families: AgentTesla, FormBook, SalatStealer, StealC and Vidar. We have 100 samples per family, split 70, 15 and 15 percent, with a new split for each seed.

Opacity blend mixes both sources into every channel. RGB-stack keeps them apart: red is the API tile, green is the network tile, and blue is an edge map of their average. So blue adds no new information, and it is the emptiest channel: almost 63 percent of its pixels are exactly zero. Keep that in mind; it comes back at the end.

## Slide 6. Channel-Aware Backdoor in Federated Learning (0:55, clock 4:35)

We use one server and five clients, aggregated with FedAvg. Each client holds 70 images, 14 per family, so the partition is balanced and IID.

One client is malicious. It puts a small white square trigger on AgentTesla training images and relabels them as FormBook: only two images per round, resampled every round. It is pure data poisoning, with no update scaling and no model replacement.

Attack success rate is how many of the 15 AgentTesla test images, with the trigger added, the model labels as FormBook. Because RGB-stack keeps the channels separate, we can put the trigger in red, green, blue, or all three, and compare them.

## Slide 7. Training, Defense and Evaluation (0:50, clock 5:25)

*Left table.* The model is ResNet18, the strongest of the three backbones we compared on RGB-stack, trained from scratch with AdamW. We run 50 federated rounds, with two local epochs per round.

*Right box.* We report the final-round global model, and we measure clean accuracy, macro-F1 and attack success rate over three seeds.

For defense, Multi-Krum is our main baseline: it scores each update by its distance to the others and keeps the most central ones. We also screen clipping, coordinate-wise median and trimmed mean. As a control, we apply the same triggers at test time to a clean model that never saw poisoned data.

## Slide 8. Channel-Aware Backdoor Sweep (1:00, clock 6:25)

This is the central result. On seed 42, we put the same trigger into each channel in turn.

Red, the API channel, and green, the network channel, reach only five out of fifteen, 33 percent. Their trigger controls give four out of fifteen, so they are indistinguishable from the model's natural confusion.

Blue and full RGB reach 100 percent, while clean accuracy stays at 84 to 85 percent, so the model still looks healthy.

The striking part is blue. A trigger in the fusion channel alone is as effective as a trigger across all three channels. And pooled over the three seeds, blue and full RGB differ from their controls with p-values below ten to the minus seventeen.

## Slide 9. Defense Screening (0:35, clock 7:00)

Can standard defenses stop it? We screened four defenses on seed 42. Clipping, coordinate-wise median and trimmed mean all leave the attack success rate at 100 percent for both triggers. Only Multi-Krum reduces it, and only for full RGB: from 100 to 40 percent. Against the blue trigger, even Multi-Krum stays at 100 percent. So Multi-Krum is the only defense we carried into the multi-seed evaluation.

## Slide 10. Multi-Seed Results (1:15, clock 8:15)

*Point to the highlighted rows.* Over three seeds, under FedAvg, both the blue and the full-RGB backdoors reach fifteen out of fifteen on every seed. Clean accuracy stays comparable to the clean baseline, at about 83 percent.

Across all eight controls, the six in this table plus red and green on seed 42, seven give exactly the same target rate with and without the trigger. So the attack success comes from poisoning, not from the pattern.

One note for transparency, in the footnote: the seed-42 clean baseline and its controls come from a shorter run. No attack success result is affected.

Now the Multi-Krum rows. The means, 51 and 60 percent, look like partial protection, but they are misleading. Per seed, blue gives 15, 3 and 5 out of 15, and full RGB gives 6, 15 and 6. On one seed out of three, the backdoor is fully effective.

## Slide 11. Defense Analysis: Bimodal Rather Than Partial (1:10, clock 9:25)

This figure shows both backdoors under FedAvg and under Multi-Krum, across the three seeds. On top, the clean macro-F1 curves of all four settings stay together. *Bottom panel.* Under FedAvg, both triggers settle at 100 percent. Under Multi-Krum, the curves stay unstable. The outcome is bimodal: on a given seed, the backdoor is either mostly suppressed or not suppressed at all.

It tracks selection. Multi-Krum keeps two of the five updates in each round, and the poisoned update is not an outlier, so whether it is kept is close to a coin flip. The malicious client was kept in 8 to 50 percent of the rounds, and that rate correlates with the final attack success, with a correlation of 0.89. With only six runs, this is indicative rather than conclusive.

So Multi-Krum is unreliable as a standalone defense.

## Slide 12. The Blue/Fusion Channel (1:00, clock 10:25)

Finally, why does blue work when red and green do not? Inside the trigger region of the clean images, red is already very bright, with a mean of 214.6. And 37.7 percent of its pixels are already at 254 or above, where a white trigger changes nothing at all. Green's mean is only 48.3, so a white trigger adds a contrast of about 207, and green still fails.

Blue's mean is just 21.6. It cannot win through new information, because it is computed from red and green. What distinguishes it is that it is almost empty, so the trigger is the only strong signal there. This explanation fits our measurements, but it is not proven; a contrast-matched trigger would test it.

## Slide 13. Conclusion and Future Work (1:05, clock 11:30)

The main message is that the channels of this representation are an attack surface. A trigger in the fusion channel alone matches one spanning all three, even though that channel is derived from the other two.

Blue and full-RGB triggers reached 100 percent attack success across three seeds, with clean performance close to the baseline. Multi-Krum reduced the attack only bimodally: for each trigger, it left the backdoor fully effective on one of the three seeds.

So, in this controlled IID setting, channel-aware backdoors are a serious threat to federated malware classifiers, and they motivate defenses that look at the representation, not only at the updates.

Our main limitations are the IID-only partition, a single source-target pair, and three seeds. The next steps are a non-IID partition, a second source-target pair, and a contrast-matched trigger.

## Slide 14. Thank you (0:10, clock 11:40)

Thank you for your attention. I am happy to take your questions.
