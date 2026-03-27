# k8s-test-suite

![CI](https://github.com/richa-sahu/k8s-test-suite/actions/workflows/ci.yml/badge.svg)

A Kubernetes-native test framework for cluster validation, deployment verification, and service connectivity testing using Python, Pytest, Helm, and Sonobuoy.

## What this tests

| Suite | What it validates |
|---|---|
| `test_cluster_health` | Node readiness, kube-system pod health, API server reachability |
| `test_deployment_validation` | Helm chart deploy, replica count, rollout status, pod readiness |
| `test_service_connectivity` | ClusterIP existence, endpoint health, in-cluster HTTP via exec |
| `test_sonobuoy_results` | Conformance run, zero failures, results retrieval, cleanup |

## Tech stack

- **Python 3.10+** + Pytest + Allure reporting
- **Kubernetes Python SDK** — direct API server queries
- **Helm** — chart authoring and session-scoped deploy/teardown
- **Sonobuoy** — conformance and cluster validation
- **kind** — local Kubernetes cluster in Docker
- **GitHub Actions** — CI with kind cluster, allure artifact upload

## Local setup

### Prerequisites
- Docker
- kind, kubectl, helm, sonobuoy (`brew install kind kubectl helm sonobuoy`)

### Create the cluster
```bash
kind create cluster --config kind-config.yaml --name k8s-test-suite
kubectl get nodes
```

### Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run all tests
```bash
pytest tests/ -v
```

### Run by layer
```bash
pytest tests/ -m cluster       # cluster health only
pytest tests/ -m deployment    # deployment validation only
pytest tests/ -m connectivity  # service connectivity only
pytest tests/ -m sonobuoy      # conformance tests (runs locally only, ~15 min)
```

### View Allure report
```bash
allure serve allure-results
```

## CI

GitHub Actions runs on every push and pull request to `main`. The pipeline:
1. Spins up a kind cluster inside the CI runner
2. Installs kubectl, helm, and sonobuoy
3. Runs all tests except sonobuoy (conformance tests run on-demand locally)
4. Uploads Allure results as a build artifact
5. Tears down the cluster

Sonobuoy conformance tests are excluded from CI (`-m "not sonobuoy"`) as they require
15+ minutes and are designed to run on-demand against a target cluster.

## Project structure
```
k8s-test-suite/
├── .github/workflows/ci.yml      # GitHub Actions pipeline
├── charts/test-app/              # Helm chart for nginx target app
├── tests/
│   ├── conftest.py               # k8s client fixtures, helm deploy/teardown
│   ├── test_cluster_health.py    # node and system pod validation
│   ├── test_deployment_validation.py  # helm + replica + rollout checks
│   ├── test_service_connectivity.py   # ClusterIP + in-cluster curl
│   └── test_sonobuoy_results.py  # conformance run and results parsing
├── kind-config.yaml              # 1 control-plane + 2 worker nodes
├── Dockerfile                    # test runner image
└── requirements.txt
```

## Author

**Richa Sahu** — Senior SDET  
[GitHub](https://github.com/richa-sahu) · [LinkedIn](https://linkedin.com/in/richasahu27)
