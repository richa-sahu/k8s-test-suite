import pytest
import allure
from kubernetes import client, stream


@allure.feature("Service Connectivity")
class TestServiceConnectivity:

    @allure.story("Service exists")
    @allure.title("ClusterIP service should exist in test-target namespace")
    @pytest.mark.connectivity
    def test_service_exists(self, helm_release, k8s_client):
        services = k8s_client.list_namespaced_service(
            namespace="test-target"
        ).items
        names = [s.metadata.name for s in services]
        assert f"{helm_release}-svc" in names, (
            f"Service '{helm_release}-svc' not found in test-target"
        )

    @allure.story("Service spec")
    @allure.title("Service should be ClusterIP type on port 80")
    @pytest.mark.connectivity
    def test_service_spec(self, helm_release, k8s_client):
        svc = k8s_client.read_namespaced_service(
            name=f"{helm_release}-svc",
            namespace="test-target"
        )
        assert svc.spec.type == "ClusterIP", (
            f"Expected ClusterIP, got {svc.spec.type}"
        )
        port = svc.spec.ports[0].port
        assert port == 80, f"Expected port 80, got {port}"

    @allure.story("Service endpoints")
    @allure.title("Service should have 3 healthy endpoints")
    @pytest.mark.connectivity
    def test_service_endpoints(self, helm_release, k8s_client):
        endpoints = k8s_client.read_namespaced_endpoints(
            name=f"{helm_release}-svc",
            namespace="test-target"
        )
        subsets = endpoints.subsets
        assert subsets is not None, "No endpoint subsets found"

        total = sum(len(s.addresses) for s in subsets if s.addresses)
        assert total == 3, f"Expected 3 endpoint addresses, got {total}"

    @allure.story("In-cluster connectivity")
    @allure.title("Service should be reachable via curl from inside the cluster")
    @pytest.mark.connectivity
    def test_service_reachable_from_pod(self, helm_release, k8s_client):
        # Create a temporary curl pod
        pod_name = "curl-test"
        namespace = "test-target"
        service_url = f"http://{helm_release}-svc.{namespace}.svc.cluster.local"

        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, namespace=namespace),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="curl",
                        image="curlimages/curl:latest",
                        command=["sleep", "3600"]
                    )
                ],
                restart_policy="Never"
            )
        )

        # Clean up any leftover pod from a previous run
        try:
            k8s_client.delete_namespaced_pod(name=pod_name, namespace=namespace)
            import time; time.sleep(3)
        except Exception:
            pass

        # Create the pod
        k8s_client.create_namespaced_pod(namespace=namespace, body=pod_manifest)

        # Wait for it to be running
        import time
        for _ in range(30):
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.status.phase == "Running":
                break
            time.sleep(2)
        else:
            pytest.fail("curl-test pod did not reach Running state in time")

        # Exec curl inside the pod
        response = stream.stream(
            k8s_client.connect_get_namespaced_pod_exec,
            name=pod_name,
            namespace=namespace,
            command=["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", service_url],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False
        )

        # Clean up
        k8s_client.delete_namespaced_pod(name=pod_name, namespace=namespace)

        assert response.strip() == "200", (
            f"Expected HTTP 200 from service, got: {response.strip()}"
        )