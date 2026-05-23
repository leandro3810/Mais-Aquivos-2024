"""Testes de unidade e integração para ai_project_agent.py.

Cobre as três camadas do agente MVP:

- :class:`TestAgentMemory`      — histórico circular de execução.
- :class:`TestToolLayer`        — ferramentas concretas com proteções.
- :class:`TestAgentOrchestrator` — fluxo completo de orquestração.

A classe auxiliar :class:`_RepoFixture` cria um repositório Git temporário
com os arquivos de configuração mínimos esperados pelo agente, e limpa tudo
no ``tearDown`` de cada teste.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# Adiciona a raiz do repositório ao sys.path para que a importação funcione
# independentemente do diretório de trabalho atual.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import ai_project_agent

# Atalhos para as classes públicas do módulo, usados em todos os testes.
AgentError = ai_project_agent.AgentError
AgentMemory = ai_project_agent.AgentMemory
ToolLayer = ai_project_agent.ToolLayer
AgentOrchestrator = ai_project_agent.AgentOrchestrator


# ---------------------------------------------------------------------------
# Testes da camada de memória
# ---------------------------------------------------------------------------


class TestAgentMemory(unittest.TestCase):
    """Testa a política de retenção e a validação de parâmetros de AgentMemory."""

    def test_keeps_recent_records_only(self):
        """Verifica que o histórico descarta registros antigos quando cheio.

        Com max_records=2, ao adicionar um 3º registro o primeiro deve ser
        removido, mantendo sempre os dois mais recentes.
        """
        memory = AgentMemory(max_records=2)
        memory.add("a1", "ok", "d1")
        memory.add("a2", "ok", "d2")
        # Este registro deve expulsar "a1" do histórico.
        memory.add("a3", "ok", "d3")

        records = memory.recent()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].action, "a2")
        self.assertEqual(records[1].action, "a3")

    def test_invalid_max_records(self):
        """max_records=0 deve lançar ValueError imediatamente na construção."""
        with self.assertRaises(ValueError):
            AgentMemory(max_records=0)


# ---------------------------------------------------------------------------
# Fixture de repositório Git temporário
# ---------------------------------------------------------------------------


class _RepoFixture:
    """Cria e gerencia um repositório Git temporário para testes do agente.

    O repositório contém todos os arquivos JSON exigidos por
    ``DEFAULT_CONFIG_FILES`` para que ``validate_configs`` passe por padrão.
    """

    def __init__(self):
        # Diretório temporário criado em disco; será removido em cleanup().
        self.tmpdir = tempfile.mkdtemp(prefix="agent-fixture-")
        self.repo = Path(self.tmpdir)

    def create(self):
        """Inicializa os arquivos de configuração e o repositório Git."""
        (self.repo / ".snapshots").mkdir(parents=True, exist_ok=True)

        # Conteúdo mínimo de cada arquivo de configuração esperado pelo agente.
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

        # Inicializa o repositório Git e faz um commit inicial para que
        # ``git status --porcelain`` retorne código 0 durante os testes.
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
        """Remove o diretório temporário e todos os seus arquivos."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Testes da camada de ferramentas
# ---------------------------------------------------------------------------


class TestToolLayer(unittest.TestCase):
    """Testa as ferramentas concretas e suas proteções de segurança."""

    def setUp(self):
        """Cria um repositório fixture e uma instância de ToolLayer para cada teste."""
        self.fixture = _RepoFixture()
        self.fixture.create()
        self.tools = ToolLayer(self.fixture.repo)

    def tearDown(self):
        """Remove o repositório fixture após cada teste."""
        self.fixture.cleanup()

    def test_validate_configs_success(self):
        """Todos os arquivos presentes e válidos devem resultar em sucesso."""
        result = self.tools.validate_configs()
        self.assertTrue(result["success"])
        self.assertEqual(result["errors"], [])

    def test_validate_configs_missing_file(self):
        """Um arquivo ausente deve ser reportado como erro e success=False."""
        os.remove(self.fixture.repo / ".snapshots" / "Composer.Json")
        result = self.tools.validate_configs()
        self.assertFalse(result["success"])
        self.assertTrue(any("arquivo ausente" in err for err in result["errors"]))

    def test_write_file_requires_approval(self):
        """Tentar escrever sem approved=True deve lançar AgentError."""
        with self.assertRaises(AgentError):
            self.tools.write_file("output/summary.txt", "conteúdo", approved=False)

    def test_write_file_blocks_sensitive_path(self):
        """Escrever em .github/workflows deve ser bloqueado mesmo com approved=True."""
        with self.assertRaises(AgentError):
            self.tools.write_file(".github/workflows/test.yml", "name: ci", approved=True)

    def test_run_command_failure(self):
        """Um comando que sai com código não-zero deve retornar success=False."""
        result = self.tools.run_command(["python3", "-c", "import sys; sys.exit(3)"])
        self.assertFalse(result["success"])
        self.assertEqual(result["returncode"], 3)

    def test_destructive_command_is_blocked(self):
        """Comandos com 'rm -rf' devem ser bloqueados pela política de segurança."""
        with self.assertRaises(AgentError):
            self.tools.run_command(["bash", "-lc", "rm -rf /tmp/something"])


# ---------------------------------------------------------------------------
# Testes do orquestrador
# ---------------------------------------------------------------------------


class TestAgentOrchestrator(unittest.TestCase):
    """Testa o fluxo de execução MVP e a geração do sumário."""

    def setUp(self):
        """Cria fixture, ToolLayer e AgentOrchestrator para cada teste."""
        self.fixture = _RepoFixture()
        self.fixture.create()
        self.tools = ToolLayer(self.fixture.repo)
        self.orchestrator = AgentOrchestrator(self.tools)

    def tearDown(self):
        """Remove o repositório fixture após cada teste."""
        self.fixture.cleanup()

    def test_execute_success(self):
        """Fluxo completo com testes e configs válidos deve retornar status 'success'."""
        summary = self.orchestrator.execute(
            run_tests=True,
            run_config_validation=True,
            # Usa um comando trivial para não depender de pytest/unittest reais.
            test_command=["python3", "-c", "print('ok')"],
        )

        self.assertEqual(summary["workflow"], "mvp")
        self.assertEqual(summary["status"], "success")
        self.assertTrue(summary["tests"]["success"])
        self.assertTrue(summary["config_validation"]["success"])
        # O histórico deve conter pelo menos um registro de cada etapa executada.
        self.assertGreater(len(summary["memory"]), 0)

    def test_execute_test_failure(self):
        """Testes que falham devem rebaixar o status global para 'failed'."""
        summary = self.orchestrator.execute(
            run_tests=True,
            run_config_validation=False,
            test_command=["python3", "-c", "import sys; sys.exit(1)"],
        )
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["tests"]["success"])

    def test_execute_invalid_config(self):
        """Config ausente deve rebaixar o status global para 'failed'."""
        os.remove(self.fixture.repo / ".snapshots" / "config.json")
        summary = self.orchestrator.execute(
            run_tests=False,
            run_config_validation=True,
        )
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["config_validation"]["success"])

    def test_summary_contains_version(self):
        """O sumário deve incluir a versão exata do módulo."""
        summary = self.orchestrator.execute(run_tests=False, run_config_validation=False)
        self.assertIn("version", summary)
        self.assertEqual(summary["version"], ai_project_agent.__version__)

    def test_summary_contains_timestamps(self):
        """O sumário deve conter started_at e duration_seconds >= 0."""
        summary = self.orchestrator.execute(run_tests=False, run_config_validation=False)
        self.assertIn("started_at", summary)
        self.assertIn("duration_seconds", summary)
        self.assertIsNotNone(summary["started_at"])
        self.assertGreaterEqual(summary["duration_seconds"], 0)

    def test_skip_analyze_changes(self):
        """Pular a etapa de análise de mudanças deve manter changes=None no sumário."""
        summary = self.orchestrator.execute(
            run_tests=False,
            run_config_validation=False,
            run_analyze_changes=False,
        )
        self.assertIsNone(summary["changes"])
        self.assertEqual(summary["status"], "success")

    def test_render_text_includes_version_and_timestamps(self):
        """O sumário em texto deve conter a versão, 'Iniciado em:' e 'Duração:'."""
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
