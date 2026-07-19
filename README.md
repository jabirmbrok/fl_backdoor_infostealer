# FL Backdoor Infostealer

A research project focused on **Federated Learning (FL)** for **infostealer malware classification** and the evaluation of **backdoor attacks** in distributed machine learning environments.

This repository contains the implementation, experiments, and supporting resources used to study the robustness and security of federated learning models when applied to malware classification.

## Overview

Federated Learning enables multiple clients to collaboratively train a machine learning model without directly sharing their local datasets. While this approach offers privacy advantages, it also introduces new security risks, including poisoning and backdoor attacks.

This project investigates the application of federated learning for classifying infostealer malware families and analyzes how backdoor attacks may affect the performance and reliability of the global federated model.

## Research Objectives

The main objectives of this project are:

* Develop a federated learning framework for infostealer malware classification.
* Evaluate the performance of federated learning under distributed and potentially non-IID data conditions.
* Investigate the impact of backdoor attacks on the global model.
* Measure model robustness using classification and attack-specific evaluation metrics.
* Analyze the trade-off between classification performance and security in federated environments.

## Research Scope

The research focuses on:

* Federated Learning
* Malware Classification
* Infostealer Malware
* Backdoor Attacks
* Data Poisoning
* Machine Learning Security
* Cybersecurity

## Project Structure

```text
fl_backdoor_infostealer/
│
├── data/               # Dataset and preprocessing resources
├── models/             # Machine learning model definitions
├── clients/            # Federated learning client implementation
├── server/             # Federated learning server implementation
├── attacks/            # Backdoor or poisoning attack implementation
├── evaluation/         # Evaluation scripts and metrics
├── experiments/        # Experiment configurations
├── results/            # Experimental results
├── utils/              # Utility functions
├── requirements.txt    # Python dependencies
└── README.md
```

> The project structure may change as the research implementation evolves.

## Experimental Workflow

The general experimental workflow is:

1. Prepare and preprocess the malware dataset.
2. Extract or load malware features.
3. Distribute the dataset across multiple federated clients.
4. Train local models independently on each client.
5. Aggregate local model updates into a global model.
6. Introduce malicious clients or backdoor attacks in selected experiments.
7. Evaluate the global model on clean and backdoored test samples.
8. Compare performance across different federated learning scenarios.

## Evaluation Metrics

The experiments may use the following metrics:

* Accuracy
* Precision
* Recall
* F1-Score
* Confusion Matrix
* Attack Success Rate (ASR)
* Clean Accuracy
* Backdoor Accuracy

Additional metrics may be included depending on the experimental configuration.

## Requirements

The project is primarily implemented in Python.

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

It is recommended to use a Python virtual environment.

Example:

```bash
python -m venv venv
```

Activate the environment on Windows:

```powershell
venv\Scripts\activate
```

Activate the environment on Linux:

```bash
source venv/bin/activate
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

The exact execution commands depend on the experiment configuration.

A typical workflow may involve running the federated server first:

```bash
python server.py
```

Then starting one or more federated clients:

```bash
python client.py
```

Experiment-specific commands will be documented as the implementation is finalized.

## Backdoor Attack Experiments

Backdoor experiments are designed to evaluate how malicious participants may influence the federated global model during training.

The experiments may include:

* Clean federated learning baseline
* Single malicious client scenario
* Multiple malicious client scenarios
* Different poisoning ratios
* Different attack trigger configurations
* Comparison of clean accuracy and attack success rate

The implementation in this repository is intended for controlled academic research and defensive cybersecurity analysis.

## Disclaimer

This repository is intended solely for **academic research, cybersecurity education, and defensive security analysis**.

Malware-related datasets, samples, and experimental code should only be used in authorized and isolated research environments. The authors are not responsible for misuse of the materials provided in this repository.

## Author

**Moh. Jabir Mubarok**

GitHub: [@jabirmbrok](https://github.com/jabirmbrok)

## License

This project is intended for academic and research purposes.

License information will be added based on the final distribution and publication requirements.
