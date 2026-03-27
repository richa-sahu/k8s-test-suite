import pytest
import allure
from kubernetes import client


@allure.feature("Deployment Validation")
class TestDeploymentValidation:

    @allure.story("Helm release")
    @allure.title("Helm release should deploy successfully")
    @pytest.mark.deployment
    def test_helm_release_deployed(self, helm_release, k8s_apps_client):
        deployments = k8s_apps_client.list_namespaced_deployment(
            namespace="test-target"
        ).items
        names = [d.metadata.name for d in deployments]
        assert helm_release in names, f"Release '{helm_release}' not found in test-target"

    @allure.story("Replica count")
    @allure.title("Deployment should have 3 ready replicas")
    @pytest.mark.deployment
    def test_replica_count(self, helm_release, k8s_apps_client):
        deployment = k8s_apps_client.read_namespaced_deployment(
            name=helm_release,
            namespace="test-target"
        )
        assert deployment.spec.replicas == 3, (
            f"Expected 3 replicas, got {deployment.spec.replicas}"
        )
        assert deployment.status.ready_replicas == 3, (
            f"Expected 3 ready replicas, got {deployment.status.ready_replicas}"
        )

    @allure.story("Rollout status")
    @allure.title("Deployment rollout should be complete")
    @pytest.mark.deployment
    def test_rollout_complete(self, helm_release, k8s_apps_client):
        deployment = k8s_apps_client.read_namespaced_deployment(
            name=helm_release,
            namespace="test-target"
        )
        spec_replicas = deployment.spec.replicas
        updated = deployment.status.updated_replicas
        available = deployment.status.available_replicas

        assert updated == spec_replicas, (
            f"Rollout incomplete: {updated}/{spec_replicas} updated"
        )
        assert available == spec_replicas, (
            f"Rollout incomplete: {available}/{spec_replicas} available"
        )

    @allure.story("Pod readiness")
    @allure.title("All deployment pods should be ready")
    @pytest.mark.deployment
    def test_all_pods_ready(self, helm_release, k8s_client):
        pods = k8s_client.list_namespaced_pod(
            namespace="test-target",
            label_selector=f"app={helm_release}"
        ).items

        assert len(pods) == 3, f"Expected 3 pods, got {len(pods)}"

        not_ready = []
        for pod in pods:
            if pod.status.phase != "Running":
                not_ready.append(f"{pod.metadata.name}: {pod.status.phase}")
                continue
            for condition in pod.status.conditions:
                if condition.type == "Ready" and condition.status != "True":
                    not_ready.append(f"{pod.metadata.name}: not ready")

        assert not_ready == [], f"Pods not ready: {not_ready}"

    @allure.story("Namespace")
    @allure.title("test-target namespace should exist")
    @pytest.mark.deployment
    def test_namespace_exists(self, helm_release, k8s_client):
        namespaces = k8s_client.list_namespace().items
        names = [ns.metadata.name for ns in namespaces]
        assert "test-target" in names, "test-target namespace not found"