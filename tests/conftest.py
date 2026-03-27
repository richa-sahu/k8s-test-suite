import pytest
import subprocess
from kubernetes import client, config


@pytest.fixture(scope="session")
def k8s_client():
    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture(scope="session")
def k8s_apps_client():
    config.load_kube_config()
    return client.AppsV1Api()


@pytest.fixture(scope="session")
def helm_release(k8s_client):
    release = "test-app"
    namespace = "test-target"

    subprocess.run(["kubectl", "create", "namespace", namespace], check=False)
    subprocess.run([
        "helm", "upgrade", "--install", release,
        "./charts/test-app",
        "--namespace", namespace,
        "--wait", "--timeout", "120s"
    ], check=True)

    yield release

    subprocess.run(["helm", "uninstall", release, "--namespace", namespace], check=True)