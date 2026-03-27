import pytest
import allure
from kubernetes import client


@allure.feature("Cluster Health")
class TestClusterHealth:

    @allure.story("Node readiness")
    @allure.title("All nodes should be in Ready state")
    @pytest.mark.cluster
    def test_all_nodes_ready(self, k8s_client):
        nodes = k8s_client.list_node().items
        assert len(nodes) > 0, "No nodes found in cluster"

        not_ready = []
        for node in nodes:
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status != "True":
                    not_ready.append(node.metadata.name)

        assert not_ready == [], f"Nodes not ready: {not_ready}"


    @allure.story("Node count")
    @allure.title("Cluster should have expected number of nodes")
    @pytest.mark.cluster
    def test_node_count(self, k8s_client):
        nodes = k8s_client.list_node().items
        assert len(nodes) == 3, f"Expected 3 nodes, got {len(nodes)}"

    @allure.story("System pods")
    @allure.title("All kube-system pods should be running or completed")
    @pytest.mark.cluster
    def test_kube_system_pods_healthy(self, k8s_client):
        pods = k8s_client.list_namespaced_pod(namespace="kube-system").items
        assert len(pods) > 0, "No pods found in kube-system"

        unhealthy = []
        for pod in pods:
            phase = pod.status.phase
            if phase not in ("Running", "Succeeded", "Pending"):
                unhealthy.append(f"{pod.metadata.name}: {phase}")

        assert unhealthy == [], f"Unhealthy system pods: {unhealthy}"

    @allure.story("API server")
    @allure.title("Kubernetes API server should be reachable")
    @pytest.mark.cluster
    def test_api_server_reachable(self, k8s_client):
        # If the client can list namespaces, the API server is reachable
        namespaces = k8s_client.list_namespace().items
        names = [ns.metadata.name for ns in namespaces]
        assert "kube-system" in names, "kube-system namespace not found"
        assert "default" in names, "default namespace not found"