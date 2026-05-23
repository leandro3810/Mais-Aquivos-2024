"""Agente de automação para o projeto.

MVP:
1) analisar mudanças do repositório
2) rodar testes Python
3) validar arquivos de configuração JSON
4) gerar resumo final
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

__version__ = "0.2.0"


DEFAULT_TEST_COMMAND = ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]
DEFAULT_CONFIG_FILES = [
    "package.json",
    ".snapshots/config.json",
    ".snapshots/Package.json",
    ".snapshots/.eslintrc.json",
    ".snapshots/Composer.Json",
]
SENSITIVE_PATHS = [".git", ".github/workflows", "SECURITY.md"]
DESTRUCTIVE_COMMAND_PATTERNS = [
    "rm -rf",
    "git reset --hard",
    "git clean -fd",
    "git clean -fdx",
]


class AgentError(Exception):
    """Erro de validação do agente."""


@dataclass
class ExecutionRecord:
    action: str
    status: str
    details: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


class AgentMemory:
    """Memória curta da execução para rastreabilidade."""

    def __init__(self, max_records: int = 20) -> None:
        if max_records <= 0:
            raise ValueError("max_records deve ser maior que zero")
        self.max_records = max_records
        self._records: list[ExecutionRecord] = []

    def add(self, action: str, status: str, details: str) -> None:
        self._records.append(ExecutionRecord(action=action, status=status, details=details))
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]

    def recent(self) -> list[ExecutionRecord]:
        return list(self._records)


class ToolLayer:
    """Camada de ferramentas com proteções de segurança."""

    def __init__(self, repo_root: str | Path, memory: AgentMemory | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.memory = memory or AgentMemory()

    def _is_destructive_command(self, command: Iterable[str]) -> bool:
        joined = " ".join(command).lower()
        return any(pattern in joined for pattern in DESTRUCTIVE_COMMAND_PATTERNS)

    def _to_repo_relative(self, path: str | Path) -> Path:
        path_obj = Path(path)
        if path_obj.is_absolute():
            resolved = path_obj.resolve()
        else:
            resolved = (self.repo_root / path_obj).resolve()

        try:
            return resolved.relative_to(self.repo_root)
        except ValueError as exc:
            raise AgentError("Caminho fora do repositório") from exc

    def _is_sensitive_path(self, relative_path: Path) -> bool:
        relative_str = relative_path.as_posix()
        for sensitive in SENSITIVE_PATHS:
            normalized = sensitive.strip("/")
            if relative_str == normalized or relative_str.startswith(f"{normalized}/"):
                return True
        return False

    def analyze_changes(self) -> dict:
        command = ["git", "-C", str(self.repo_root), "status", "--porcelain"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        files = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            files.append(line[3:].strip())

        payload = {
            "success": result.returncode == 0,
            "changed_files": files,
            "has_changes": bool(files),
            "error": result.stderr.strip(),
        }
        self.memory.add("analyze_changes", "ok" if payload["success"] else "failed", str(payload))
        return payload

    def run_command(self, command: list[str], allow_destructive: bool = False) -> dict:
        if self._is_destructive_command(command) and not allow_destructive:
            raise AgentError("Comando bloqueado por política de segurança")

        result = subprocess.run(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        payload = {
            "command": command,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        status = "ok" if payload["success"] else "failed"
        self.memory.add("run_command", status, f"rc={result.returncode}")
        return payload

    def run_tests(self, command: list[str] | None = None) -> dict:
        test_command = command or DEFAULT_TEST_COMMAND
        result = self.run_command(test_command)
        self.memory.add("run_tests", "ok" if result["success"] else "failed", str(test_command))
        return result

    def validate_configs(self, config_files: list[str] | None = None) -> dict:
        files = config_files or DEFAULT_CONFIG_FILES
        checked: list[str] = []
        errors: list[str] = []

        for item in files:
            rel = self._to_repo_relative(item)
            full_path = self.repo_root / rel
            checked.append(rel.as_posix())

            if not full_path.exists():
                errors.append(f"arquivo ausente: {rel.as_posix()}")
                continue

            try:
                with open(full_path, encoding="utf-8") as fh:
                    json.load(fh)
            except json.JSONDecodeError as exc:
                errors.append(f"JSON inválido em {rel.as_posix()}: {exc.msg}")

        payload = {"success": not errors, "checked": checked, "errors": errors}
        self.memory.add("validate_configs", "ok" if payload["success"] else "failed", str(payload))
        return payload

    def write_file(self, relative_path: str, content: str, approved: bool = False) -> str:
        rel = self._to_repo_relative(relative_path)
        if self._is_sensitive_path(rel):
            raise AgentError("Alteração bloqueada: caminho sensível")
        if not approved:
            raise AgentError("Alteração exige aprovação explícita")

        target = self.repo_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)

        self.memory.add("write_file", "ok", rel.as_posix())
        return str(target)


class AgentOrchestrator:
    """Camada de orquestração do fluxo MVP."""

    def __init__(self, tools: ToolLayer) -> None:
        self.tools = tools

    def execute(
        self,
        run_tests: bool = True,
        run_config_validation: bool = True,
        run_analyze_changes: bool = True,
        test_command: list[str] | None = None,
    ) -> dict:
        started_at = datetime.now(timezone.utc)
        summary: dict = {
            "workflow": "mvp",
            "version": __version__,
            "started_at": started_at.isoformat(timespec="seconds"),
            "duration_seconds": None,
            "changes": None,
            "tests": None,
            "config_validation": None,
            "memory": [],
            "status": "success",
        }

        if run_analyze_changes:
            summary["changes"] = self.tools.analyze_changes()

        if run_tests:
            summary["tests"] = self.tools.run_tests(command=test_command)
            if not summary["tests"]["success"]:
                summary["status"] = "failed"

        if run_config_validation:
            summary["config_validation"] = self.tools.validate_configs()
            if not summary["config_validation"]["success"]:
                summary["status"] = "failed"

        summary["duration_seconds"] = round(
            (datetime.now(timezone.utc) - started_at).total_seconds(), 3
        )
        summary["memory"] = [record.__dict__ for record in self.tools.memory.recent()]
        return summary

    @staticmethod
    def render_text_summary(summary: dict) -> str:
        lines = [
            f"Resumo do agente (MVP) v{summary.get('version', '')}",
            f"Iniciado em: {summary.get('started_at', '-')}",
            f"Duração: {summary.get('duration_seconds', '-')}s",
            f"Status final: {summary['status']}",
        ]

        changes = summary.get("changes")
        if changes is not None:
            lines.append(f"Arquivos alterados detectados: {len(changes['changed_files'])}")

        if summary.get("tests") is not None:
            lines.append(
                "Testes: " + ("sucesso" if summary["tests"].get("success") else "falha")
            )

        config = summary.get("config_validation")
        if config is not None:
            lines.append(
                "Configs: " + ("válidas" if config.get("success") else "inválidas")
            )
            if config.get("errors"):
                lines.extend(f"- {err}" for err in config["errors"])

        return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agente de automação do projeto")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("--repo-root", default=".", help="Raiz do repositório")
    parser.add_argument("--skip-tests", action="store_true", help="Pula etapa de testes")
    parser.add_argument(
        "--skip-config-validation",
        action="store_true",
        help="Pula validação de arquivos JSON",
    )
    parser.add_argument(
        "--skip-analyze-changes",
        action="store_true",
        help="Pula análise de mudanças no repositório",
    )
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--summary-file", help="Arquivo de saída opcional para o resumo")
    parser.add_argument(
        "--approve-write",
        action="store_true",
        help="Permite gravação do arquivo de resumo quando informado",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    tools = ToolLayer(args.repo_root)
    orchestrator = AgentOrchestrator(tools)

    summary = orchestrator.execute(
        run_tests=not args.skip_tests,
        run_config_validation=not args.skip_config_validation,
        run_analyze_changes=not args.skip_analyze_changes,
    )

    if args.output == "json":
        rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    else:
        rendered = orchestrator.render_text_summary(summary)

    if args.summary_file:
        tools.write_file(args.summary_file, rendered + "\n", approved=args.approve_write)

    print(rendered)
    return 0 if summary.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
