"""Tests for ai_project_agent.py."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import ai_project_agent

AgentError = ai_project_agent.AgentError
AgentMemory = ai_project_agent.AgentMemory
ToolLayer = ai_project_agent.ToolLayer
AgentOrchestrator = ai_project_agent.AgentOrchestrator


class TestAgentMemory(unittest.TestCase):
    def test_keeps_recent_records_only(self):
        memory = AgentMemory(max_records=2)
        memory.add("a1", "ok", "d1")
        memory.add("a2", "ok", "d2")
        memory.add("a3", "ok", "d3")

        records = memory.recent()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].action, "a2")
        self.assertEqual(records[1].action, "a3")

    def test_invalid_max_records(self):
        with self.assertRaises(ValueError):
            AgentMemory(max_records=0)


class _RepoFixture:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="agent-fixture-")
        self.repo = Path(self.tmpdir)

    def create(self):
        (self.repo / ".snapshots").mkdir(parents=True, exist_ok=True)

        data = {
            "package.json": {"name": "repo", "version": "1.0.0"},
            ".snapshots/config.json": {
                "excluded_patterns": [".git"],
                "included_patterns": ["package.json"],
                "default": {
                    "default_prompt": "ok",
                    "default_include_all_files": False,
                    "default_include_entire_project_structure": False,
                },
            },
            ".snapshots/Package.json": {"name": "snap", "version": "1.0.0"},
            ".snapshots/.eslintrc.json": {"env": {"browser": True}, "rules": {}},
            ".snapshots/Composer.Json": {
                "require": {"php": ">=8.0"},
                "autoload": {},
                "require-dev": {},
                "scripts": {"test": "phpunit"},
            },
        }

        for rel, payload in data.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)

        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "tests@example.com"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tests"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class TestToolLayer(unittest.TestCase):
    def setUp(self):
        self.fixture = _RepoFixture()
        self.fixture.create()
        self.tools = ToolLayer(self.fixture.repo)

    def tearDown(self):
        self.fixture.cleanup()

    def test_validate_configs_success(self):
        result = self.tools.validate_configs()
        self.assertTrue(result["success"])
        self.assertEqual(result["errors"], [])

    def test_validate_configs_missing_file(self):
        os.remove(self.fixture.repo / ".snapshots" / "Composer.Json")
        result = self.tools.validate_configs()
        self.assertFalse(result["success"])
        self.assertTrue(any("arquivo ausente" in err for err in result["errors"]))

    def test_write_file_requires_approval(self):
        with self.assertRaises(AgentError):
            self.tools.write_file("output/summary.txt", "conteúdo", approved=False)

    def test_write_file_blocks_sensitive_path(self):
        with self.assertRaises(AgentError):
            self.tools.write_file(".github/workflows/test.yml", "name: ci", approved=True)

    def test_run_command_failure(self):
        result = self.tools.run_command(["python3", "-c", "import sys; sys.exit(3)"])
        self.assertFalse(result["success"])
        self.assertEqual(result["returncode"], 3)

    def test_destructive_command_is_blocked(self):
        with self.assertRaises(AgentError):
            self.tools.run_command(["bash", "-lc", "rm -rf /tmp/something"])


class TestAgentOrchestrator(unittest.TestCase):
    def setUp(self):
        self.fixture = _RepoFixture()
        self.fixture.create()
        self.tools = ToolLayer(self.fixture.repo)
        self.orchestrator = AgentOrchestrator(self.tools)

    def tearDown(self):
        self.fixture.cleanup()

    def test_execute_success(self):
        summary = self.orchestrator.execute(
            run_tests=True,
            run_config_validation=True,
            test_command=["python3", "-c", "print('ok')"],
        )

        self.assertEqual(summary["workflow"], "mvp")
        self.assertEqual(summary["status"], "success")
        self.assertTrue(summary["tests"]["success"])
        self.assertTrue(summary["config_validation"]["success"])
        self.assertGreater(len(summary["memory"]), 0)

    def test_execute_test_failure(self):
        summary = self.orchestrator.execute(
            run_tests=True,
            run_config_validation=False,
            test_command=["python3", "-c", "import sys; sys.exit(1)"],
        )
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["tests"]["success"])

    def test_execute_invalid_config(self):
        os.remove(self.fixture.repo / ".snapshots" / "config.json")
        summary = self.orchestrator.execute(
            run_tests=False,
            run_config_validation=True,
        )
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["config_validation"]["success"])

    def test_summary_contains_version(self):
        summary = self.orchestrator.execute(run_tests=False, run_config_validation=False)
        self.assertIn("version", summary)
        self.assertEqual(summary["version"], ai_project_agent.__version__)

    def test_summary_contains_timestamps(self):
        summary = self.orchestrator.execute(run_tests=False, run_config_validation=False)
        self.assertIn("started_at", summary)
        self.assertIn("duration_seconds", summary)
        self.assertIsNotNone(summary["started_at"])
        self.assertGreaterEqual(summary["duration_seconds"], 0)

    def test_skip_analyze_changes(self):
        summary = self.orchestrator.execute(
            run_tests=False,
            run_config_validation=False,
            run_analyze_changes=False,
        )
        self.assertIsNone(summary["changes"])
        self.assertEqual(summary["status"], "success")

    def test_render_text_includes_version_and_timestamps(self):
        summary = self.orchestrator.execute(
            run_tests=False,
            run_config_validation=False,
            test_command=["python3", "-c", "print('ok')"],
        )
        rendered = AgentOrchestrator.render_text_summary(summary)
        self.assertIn(ai_project_agent.__version__, rendered)
        self.assertIn("Iniciado em:", rendered)
        self.assertIn("Duração:", rendered)


if __name__ == "__main__":
    unittest.main()
