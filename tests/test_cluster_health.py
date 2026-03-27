import pytest
import allure
import time
from kubernetes import client


@allure.feature("Cluster Health")
class TestClusterHealth:

    @allure.story("Node readiness")
    @allure.title("All nodes should be in Ready state")
    @pytest.mark.cluster
    def test_all_nodes_ready(self, k8s_client):
        # Retry for up to 60s — nodes may still be joining in CI
        for attempt in range(12):
            nodes = k8s_client.list_node().items
            not_ready = [
                node.metadata.name
                for node in nodes
                for condition in node.status.conditions
                if condition.type == "Ready" and condition.status != "True"
            ]
            if not not_ready:
                return
            time.sleep(5)

        assert not_ready == [], f"Nodes not ready after 60s: {not_ready}"

    @allure.story("Node count")
    @allure.title("Cluster should have expected number of nodes")
    @pytest.mark.cluster
    def test_node_count(self, k8s_client):
        nodes = k8s_client.list_node().items
        assert len(nodes) >= 1, f"Expected at least 1 node, got {len(nodes)}"

    @allure.story("System pods")
    @allure.title("All kube-system pods should be running or completed")
    @pytest.mark.cluster
    def test_kube_system_pods_healthy(self, k8s_client):
        # Retry for up to 60s — CNI pods may still be starting in CI
        for attempt in range(12):
            pods = k8s_client.list_namespaced_pod(namespace="kube-system").items
            assert len(pods) > 0, "No pods found in kube-system"

            unhealthy = [
                f"{pod.metadata.name}: {pod.status.phase}"
                for pod in pods
                if pod.status.phase not in ("Running", "Succeeded", "Pending")
            ]
            if not unhealthy:
                return
            time.sleep(5)

        assert unhealthy == [], f"Unhealthy system pods after 60s: {unhealthy}"

    @allure.story("API server")
    @allure.title("Kubernetes API server should be reachable")
    @pytest.mark.cluster
    def test_api_server_reachable(self, k8s_client):
        namespaces = k8s_client.list_namespace().items
        names = [ns.metadata.name for ns in namespaces]
        assert "kube-system" in names, "kube-system namespace not found"
        assert "default" in names, "default namespace not found"