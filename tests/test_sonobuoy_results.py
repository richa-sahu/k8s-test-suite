import pytest
import allure
import subprocess
import time
import json
import tarfile
import os
import tempfile


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


@allure.feature("Sonobuoy Conformance")
class TestSonobuoyResults:

    @allure.story("Sonobuoy run")
    @allure.title("Sonobuoy quick mode should complete without errors")
    @pytest.mark.sonobuoy
    def test_sonobuoy_run_completes(self):
        # Delete any previous sonobuoy run
        run_command(["sonobuoy", "delete", "--wait"])

        # Run sonobuoy in quick mode (runs a single conformance test, fast)
        stdout, stderr, rc = run_command([
            "sonobuoy", "run",
            "--mode", "quick",
            "--sonobuoy-image", "sonobuoy/sonobuoy:arm64-main",
            "--wait",
            "--timeout", "300"
        ])
        assert rc == 0, f"Sonobuoy run failed:\nstdout: {stdout}\nstderr: {stderr}"

    @allure.story("Sonobuoy results")
    @allure.title("Sonobuoy results should show no failures")
    @pytest.mark.sonobuoy
    def test_sonobuoy_no_failures(self):
        # Retrieve results
        stdout, stderr, rc = run_command(["sonobuoy", "status", "--json"])
        assert rc == 0, f"Could not get sonobuoy status: {stderr}"

        status = json.loads(stdout)
        plugins = status.get("plugins", [])
        assert len(plugins) > 0, "No plugins found in sonobuoy status"

        failures = [
            p for p in plugins
            if p.get("result-status") not in ("passed", "complete")
        ]
        assert failures == [], f"Sonobuoy plugin failures: {failures}"

    @allure.story("Sonobuoy results")
    @allure.title("Sonobuoy results tarball should be retrievable")
    @pytest.mark.sonobuoy
    def test_sonobuoy_results_retrievable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tarball_path = os.path.join(tmpdir, "results.tar.gz")

            # Retrieve results tarball
            stdout, stderr, rc = run_command([
                "sonobuoy", "retrieve", tmpdir
            ])
            assert rc == 0, f"Could not retrieve sonobuoy results: {stderr}"

            # Find the tarball (sonobuoy names it with a timestamp)
            tarballs = [f for f in os.listdir(tmpdir) if f.endswith(".tar.gz")]
            assert len(tarballs) > 0, "No results tarball found"

            # Verify tarball is valid and non-empty
            tarball_path = os.path.join(tmpdir, tarballs[0])
            assert os.path.getsize(tarball_path) > 0, "Results tarball is empty"

            with tarfile.open(tarball_path, "r:gz") as tar:
                members = tar.getnames()
                assert len(members) > 0, "Tarball contains no files"

    @allure.story("Sonobuoy cleanup")
    @allure.title("Sonobuoy resources should clean up successfully")
    @pytest.mark.sonobuoy
    def test_sonobuoy_cleanup(self):
        stdout, stderr, rc = run_command(["sonobuoy", "delete", "--wait"])
        assert rc == 0, f"Sonobuoy cleanup failed: {stderr}"