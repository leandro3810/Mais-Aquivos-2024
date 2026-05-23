"""Agente de automação para o projeto.

MVP — fluxo executado em sequência:
1) Analisar mudanças no repositório via ``git status --porcelain``.
2) Rodar a suíte de testes Python (por padrão: ``unittest discover``).
3) Validar se os arquivos de configuração JSON são bem-formados e existem.
4) Gerar um resumo final em texto puro ou JSON.

Arquitetura em três camadas
-----------------------------
- :class:`AgentMemory`      — histórico de curta duração das ações da execução.
- :class:`ToolLayer`        — ferramentas concretas com proteções de segurança.
- :class:`AgentOrchestrator` — coordena o fluxo e produz o sumário final.

Proteções de segurança
-----------------------
- Comandos destrutivos são bloqueados por padrão (veja
  ``DESTRUCTIVE_COMMAND_PATTERNS``).
- Escrita em caminhos sensíveis (p. ex. ``.git``, ``SECURITY.md``) é
  impedida independentemente de aprovação.
- A gravação de arquivos exige o flag ``approved=True`` explícito.

Uso via CLI
-----------
::

    mais-arquivos-agent --repo-root /caminho/do/projeto --output json
    mais-arquivos-agent --skip-tests --summary-file reports/summary.txt --approve-write
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Versão do módulo — deve permanecer sincronizada com pyproject.toml.
__version__ = "0.2.0"


# ---------------------------------------------------------------------------
# Constantes globais
# ---------------------------------------------------------------------------

# Comando padrão para descoberta e execução de testes Python via unittest.
DEFAULT_TEST_COMMAND = ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]

# Arquivos de configuração JSON que o agente valida por padrão.
DEFAULT_CONFIG_FILES = [
    "package.json",
    ".snapshots/config.json",
    ".snapshots/Package.json",
    ".snapshots/.eslintrc.json",
    ".snapshots/Composer.Json",
]

# Caminhos que jamais podem ser sobrescritos pelo agente, mesmo com aprovação.
SENSITIVE_PATHS = [".git", ".github/workflows", "SECURITY.md"]

# Padrões de comandos considerados destrutivos; qualquer correspondência
# aciona bloqueio automático em ``run_command``.
DESTRUCTIVE_COMMAND_PATTERNS = [
    "rm -rf",
    "git reset --hard",
    "git clean -fd",
    "git clean -fdx",
]


# ---------------------------------------------------------------------------
# Exceção personalizada
# ---------------------------------------------------------------------------


class AgentError(Exception):
    """Erro de validação ou política de segurança do agente.

    Lançado sempre que uma operação viola as regras do agente, como tentar
    escrever em um caminho sensível ou executar um comando destrutivo sem
    aprovação explícita.
    """


# ---------------------------------------------------------------------------
# Estrutura de dados de registro
# ---------------------------------------------------------------------------


@dataclass
class ExecutionRecord:
    """Registro de uma ação executada pelo agente durante a sessão atual.

    Attributes:
        action: Nome da ação executada (ex.: ``"run_tests"``).
        status: Resultado da ação — ``"ok"`` ou ``"failed"``.
        details: Informações adicionais em formato de string livre.
        timestamp: Momento ISO-8601 (UTC, precisão de segundos) em que o
            registro foi criado.
    """

    action: str
    status: str
    details: str
    # timestamp gerado automaticamente na criação do registro
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


# ---------------------------------------------------------------------------
# Memória de curta duração
# ---------------------------------------------------------------------------


class AgentMemory:
    """Histórico circular de ações executadas durante a sessão atual.

    Armazena até *max_records* registros mais recentes. Quando o limite é
    atingido, os registros mais antigos são descartados (FIFO).

    Args:
        max_records: Capacidade máxima do histórico. Deve ser > 0.

    Raises:
        ValueError: Se *max_records* for zero ou negativo.

    Example::

        memory = AgentMemory(max_records=5)
        memory.add("run_tests", "ok", "3 passed")
        print(memory.recent())
    """

    def __init__(self, max_records: int = 20) -> None:
        if max_records <= 0:
            raise ValueError("max_records deve ser maior que zero")
        self.max_records = max_records
        # Lista interna que nunca excede max_records elementos.
        self._records: list[ExecutionRecord] = []

    def add(self, action: str, status: str, details: str) -> None:
        """Adiciona um novo registro ao histórico.

        Se o limite *max_records* for atingido, os registros mais antigos
        são removidos para dar espaço ao novo.

        Args:
            action: Nome da ação executada.
            status: ``"ok"`` para sucesso ou ``"failed"`` para falha.
            details: Texto livre com detalhes sobre a execução.
        """
        self._records.append(ExecutionRecord(action=action, status=status, details=details))
        # Mantém somente os últimos max_records elementos para economizar memória.
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]

    def recent(self) -> list[ExecutionRecord]:
        """Retorna uma cópia da lista de registros mais recentes.

        Returns:
            Lista de :class:`ExecutionRecord` em ordem cronológica (mais
            antigo primeiro).
        """
        return list(self._records)


# ---------------------------------------------------------------------------
# Camada de ferramentas
# ---------------------------------------------------------------------------


class ToolLayer:
    """Ferramentas concretas do agente com proteções de segurança integradas.

    Todas as operações que envolvem o sistema de arquivos ou execução de
    processos passam por verificações de caminho e de padrões destrutivos
    antes de prosseguir.

    Args:
        repo_root: Diretório raiz do repositório. Pode ser absoluto ou
            relativo ao diretório de trabalho atual; será resolvido para
            caminho absoluto internamente.
        memory: Instância de :class:`AgentMemory` a ser utilizada. Se
            ``None``, uma nova instância com configuração padrão é criada.
    """

    def __init__(self, repo_root: str | Path, memory: AgentMemory | None = None) -> None:
        # Resolve para caminho absoluto para evitar ambiguidades em verificações de prefixo.
        self.repo_root = Path(repo_root).resolve()
        self.memory = memory or AgentMemory()

    # ------------------------------------------------------------------
    # Métodos privados de validação
    # ------------------------------------------------------------------

    def _is_destructive_command(self, command: Iterable[str]) -> bool:
        """Verifica se o comando contém algum padrão destrutivo conhecido.

        A comparação é feita em letras minúsculas para evitar que variações
        de capitalização contornem a proteção.

        Args:
            command: Sequência de tokens do comando a verificar.

        Returns:
            ``True`` se qualquer padrão de ``DESTRUCTIVE_COMMAND_PATTERNS``
            for encontrado na string unificada do comando.
        """
        # Une os tokens com espaço e normaliza para minúsculas antes de comparar.
        joined = " ".join(command).lower()
        return any(pattern in joined for pattern in DESTRUCTIVE_COMMAND_PATTERNS)

    def _to_repo_relative(self, path: str | Path) -> Path:
        """Converte *path* para um caminho relativo à raiz do repositório.

        Garante que o caminho resultante está dentro de ``self.repo_root``.
        Caminhos absolutos são resolvidos diretamente; caminhos relativos
        são interpretados em relação à raiz do repositório.

        Args:
            path: Caminho a normalizar (absoluto ou relativo).

        Returns:
            Caminho relativo à raiz do repositório como :class:`pathlib.Path`.

        Raises:
            AgentError: Se o caminho resolvido estiver fora de ``repo_root``.
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            resolved = path_obj.resolve()
        else:
            # Caminhos relativos são âncoras na raiz do repositório.
            resolved = (self.repo_root / path_obj).resolve()

        try:
            return resolved.relative_to(self.repo_root)
        except ValueError as exc:
            raise AgentError("Caminho fora do repositório") from exc

    def _is_sensitive_path(self, relative_path: Path) -> bool:
        """Verifica se *relative_path* aponta para um caminho protegido.

        A verificação cobre tanto o caminho exato quanto qualquer arquivo
        dentro de um diretório sensível (ex.: ``.github/workflows/ci.yml``
        é sensível porque está sob ``.github/workflows``).

        Args:
            relative_path: Caminho relativo à raiz do repositório.

        Returns:
            ``True`` se o caminho corresponder a ou estiver dentro de um
            dos ``SENSITIVE_PATHS``.
        """
        relative_str = relative_path.as_posix()
        for sensitive in SENSITIVE_PATHS:
            # Remove barras laterais para normalizar o padrão antes da comparação.
            normalized = sensitive.strip("/")
            if relative_str == normalized or relative_str.startswith(f"{normalized}/"):
                return True
        return False

    # ------------------------------------------------------------------
    # Ferramentas públicas
    # ------------------------------------------------------------------

    def analyze_changes(self) -> dict:
        """Detecta arquivos modificados no repositório Git atual.

        Executa ``git status --porcelain`` e analisa a saída para listar
        todos os arquivos com estado diferente do HEAD.

        Returns:
            Dicionário com as chaves:

            - ``success`` (bool): ``True`` se o comando git retornou código 0.
            - ``changed_files`` (list[str]): Lista de caminhos dos arquivos alterados.
            - ``has_changes`` (bool): ``True`` se houver ao menos um arquivo alterado.
            - ``error`` (str): Mensagem de erro do stderr (vazia em caso de sucesso).
        """
        command = ["git", "-C", str(self.repo_root), "status", "--porcelain"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        files = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            # O formato porcelain usa os dois primeiros caracteres para o estado;
            # a partir do 3º caractere começa o caminho do arquivo.
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
        """Executa um comando de sistema com verificação de segurança.

        Por padrão, qualquer comando que contenha padrões destrutivos é
        bloqueado. Passe ``allow_destructive=True`` somente quando o
        contexto garantir que a operação é intencional e segura.

        Args:
            command: Lista de tokens do comando a executar
                (ex.: ``["python3", "-m", "pytest"]``).
            allow_destructive: Se ``True``, desabilita a verificação de
                padrões destrutivos para este comando.

        Returns:
            Dicionário com as chaves:

            - ``command`` (list[str]): O comando executado.
            - ``returncode`` (int): Código de saída do processo.
            - ``success`` (bool): ``True`` se ``returncode == 0``.
            - ``stdout`` (str): Saída padrão capturada.
            - ``stderr`` (str): Saída de erro capturada.

        Raises:
            AgentError: Se o comando contiver padrões destrutivos e
                *allow_destructive* for ``False``.
        """
        # Bloqueia o comando antes de lançá-lo se for considerado destrutivo.
        if self._is_destructive_command(command) and not allow_destructive:
            raise AgentError("Comando bloqueado por política de segurança")

        result = subprocess.run(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,  # Não levanta exceção em caso de falha; verificamos returncode.
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
        """Executa a suíte de testes do projeto.

        Delega a execução para :meth:`run_command`. Se nenhum comando for
        informado, usa ``DEFAULT_TEST_COMMAND`` (``unittest discover``).

        Args:
            command: Comando customizado para rodar os testes. Quando
                ``None``, usa :data:`DEFAULT_TEST_COMMAND`.

        Returns:
            O mesmo dicionário retornado por :meth:`run_command`.
        """
        test_command = command or DEFAULT_TEST_COMMAND
        result = self.run_command(test_command)
        # Registra separadamente para distinguir execuções de teste no histórico.
        self.memory.add("run_tests", "ok" if result["success"] else "failed", str(test_command))
        return result

    def validate_configs(self, config_files: list[str] | None = None) -> dict:
        """Verifica se os arquivos de configuração JSON existem e são válidos.

        Para cada arquivo da lista, o agente:

        1. Resolve o caminho relativo ao repositório.
        2. Verifica se o arquivo existe em disco.
        3. Tenta desserializar o conteúdo como JSON.

        Args:
            config_files: Lista de caminhos (relativos à raiz do
                repositório) a verificar. Quando ``None``, usa
                :data:`DEFAULT_CONFIG_FILES`.

        Returns:
            Dicionário com as chaves:

            - ``success`` (bool): ``True`` se nenhum erro foi encontrado.
            - ``checked`` (list[str]): Caminhos verificados (relativos).
            - ``errors`` (list[str]): Descrição dos erros encontrados, ou
              lista vazia em caso de sucesso.
        """
        files = config_files or DEFAULT_CONFIG_FILES
        checked: list[str] = []
        errors: list[str] = []

        for item in files:
            rel = self._to_repo_relative(item)
            full_path = self.repo_root / rel
            checked.append(rel.as_posix())

            # Primeiro verifica a existência para evitar erros de I/O enganosos.
            if not full_path.exists():
                errors.append(f"arquivo ausente: {rel.as_posix()}")
                continue

            # Tenta desserializar; qualquer JSON malformado gera um erro descritivo.
            try:
                with open(full_path, encoding="utf-8") as fh:
                    json.load(fh)
            except json.JSONDecodeError as exc:
                errors.append(f"JSON inválido em {rel.as_posix()}: {exc.msg}")

        payload = {"success": not errors, "checked": checked, "errors": errors}
        self.memory.add("validate_configs", "ok" if payload["success"] else "failed", str(payload))
        return payload

    def write_file(self, relative_path: str, content: str, approved: bool = False) -> str:
        """Grava *content* em *relative_path* dentro do repositório.

        A operação é bloqueada em dois casos:

        1. O caminho alvo é sensível (veja :data:`SENSITIVE_PATHS`).
        2. *approved* é ``False`` — toda gravação precisa de aprovação
           explícita para evitar sobrescritas acidentais.

        Diretórios intermediários são criados automaticamente se necessário.

        Args:
            relative_path: Destino da gravação, relativo à raiz do
                repositório (ex.: ``"reports/summary.txt"``).
            content: Conteúdo a ser gravado no arquivo.
            approved: Deve ser ``True`` para autorizar a gravação.
                Qualquer valor falsy causa bloqueio imediato.

        Returns:
            Caminho absoluto do arquivo gravado como string.

        Raises:
            AgentError: Se o caminho for sensível ou se *approved* for ``False``.
        """
        rel = self._to_repo_relative(relative_path)

        # Proteção 1: rejeita caminhos sensíveis antes de qualquer verificação de aprovação.
        if self._is_sensitive_path(rel):
            raise AgentError("Alteração bloqueada: caminho sensível")

        # Proteção 2: exige aprovação explícita para toda escrita em disco.
        if not approved:
            raise AgentError("Alteração exige aprovação explícita")

        target = self.repo_root / rel
        # Cria diretórios intermediários sem falhar se já existirem.
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)

        self.memory.add("write_file", "ok", rel.as_posix())
        return str(target)


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------


class AgentOrchestrator:
    """Coordena o fluxo de execução do MVP e produz o sumário final.

    Cada etapa do fluxo (análise de mudanças, testes, validação de configs)
    é opcional e pode ser desabilitada pelos parâmetros de :meth:`execute`.
    O status final é ``"success"`` apenas quando todas as etapas habilitadas
    concluírem sem erros.

    Args:
        tools: Instância de :class:`ToolLayer` com as ferramentas concretas.
    """

    def __init__(self, tools: ToolLayer) -> None:
        self.tools = tools

    def execute(
        self,
        run_tests: bool = True,
        run_config_validation: bool = True,
        run_analyze_changes: bool = True,
        test_command: list[str] | None = None,
    ) -> dict:
        """Executa o fluxo MVP e retorna um sumário completo da execução.

        As etapas são executadas na ordem: análise de mudanças → testes →
        validação de configs. Qualquer etapa com falha muda o status final
        para ``"failed"``, mas as etapas seguintes ainda são executadas.

        Args:
            run_tests: Se ``True``, executa a suíte de testes.
            run_config_validation: Se ``True``, valida os arquivos JSON de
                configuração.
            run_analyze_changes: Se ``True``, detecta mudanças no repositório.
            test_command: Comando customizado para os testes. Passa direto
                para :meth:`ToolLayer.run_tests`.

        Returns:
            Dicionário com as chaves:

            - ``workflow`` (str): Identificador do fluxo (``"mvp"``).
            - ``version`` (str): Versão do agente.
            - ``started_at`` (str): Timestamp ISO-8601 de início.
            - ``duration_seconds`` (float): Duração total em segundos.
            - ``changes`` (dict | None): Resultado de ``analyze_changes``, ou
              ``None`` se a etapa foi pulada.
            - ``tests`` (dict | None): Resultado de ``run_tests``, ou ``None``.
            - ``config_validation`` (dict | None): Resultado de
              ``validate_configs``, ou ``None``.
            - ``memory`` (list[dict]): Registros do histórico de execução.
            - ``status`` (str): ``"success"`` ou ``"failed"``.
        """
        started_at = datetime.now(timezone.utc)

        # Inicializa o sumário com valores padrão; campos de etapas ficam None
        # até que a etapa correspondente seja executada.
        summary: dict = {
            "workflow": "mvp",
            "version": __version__,
            "started_at": started_at.isoformat(timespec="seconds"),
            "duration_seconds": None,
            "changes": None,
            "tests": None,
            "config_validation": None,
            "memory": [],
            "status": "success",  # será rebaixado para "failed" em caso de erro
        }

        # Etapa 1: detectar arquivos modificados no repositório.
        if run_analyze_changes:
            summary["changes"] = self.tools.analyze_changes()

        # Etapa 2: rodar testes — falha rebaixa o status global.
        if run_tests:
            summary["tests"] = self.tools.run_tests(command=test_command)
            if not summary["tests"]["success"]:
                summary["status"] = "failed"

        # Etapa 3: validar arquivos de configuração JSON — idem.
        if run_config_validation:
            summary["config_validation"] = self.tools.validate_configs()
            if not summary["config_validation"]["success"]:
                summary["status"] = "failed"

        # Calcula a duração total da execução com precisão de milissegundos.
        summary["duration_seconds"] = round(
            (datetime.now(timezone.utc) - started_at).total_seconds(), 3
        )
        # Serializa o histórico de ações para o sumário.
        summary["memory"] = [record.__dict__ for record in self.tools.memory.recent()]
        return summary

    @staticmethod
    def render_text_summary(summary: dict) -> str:
        """Formata o sumário da execução como texto legível por humanos.

        Args:
            summary: Dicionário retornado por :meth:`execute`.

        Returns:
            String multi-linha com as informações principais da execução,
            incluindo versão, timestamps, status e erros de configuração.
        """
        lines = [
            f"Resumo do agente (MVP) v{summary.get('version', '')}",
            f"Iniciado em: {summary.get('started_at', '-')}",
            f"Duração: {summary.get('duration_seconds', '-')}s",
            f"Status final: {summary['status']}",
        ]

        # Exibe a contagem de arquivos alterados se a etapa foi executada.
        changes = summary.get("changes")
        if changes is not None:
            lines.append(f"Arquivos alterados detectados: {len(changes['changed_files'])}")

        # Exibe resultado dos testes se a etapa foi executada.
        if summary.get("tests") is not None:
            lines.append(
                "Testes: " + ("sucesso" if summary["tests"].get("success") else "falha")
            )

        # Exibe resultado da validação de configs e lista erros individuais.
        config = summary.get("config_validation")
        if config is not None:
            lines.append(
                "Configs: " + ("válidas" if config.get("success") else "inválidas")
            )
            if config.get("errors"):
                lines.extend(f"- {err}" for err in config["errors"])

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Constrói e retorna o parser de argumentos da linha de comando.

    Returns:
        Parser configurado com todos os argumentos suportados pelo agente.
    """
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
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Formato de saída: 'text' (padrão) ou 'json'",
    )
    parser.add_argument("--summary-file", help="Arquivo de saída opcional para o resumo")
    parser.add_argument(
        "--approve-write",
        action="store_true",
        help="Permite gravação do arquivo de resumo quando informado",
    )
    return parser


def main() -> int:
    """Ponto de entrada principal do agente via linha de comando.

    Analisa os argumentos, instancia as camadas do agente, executa o fluxo
    MVP e imprime o resultado no stdout. Opcionalmente grava o resultado em
    arquivo se ``--summary-file`` e ``--approve-write`` forem informados.

    Returns:
        Código de saída do processo: ``0`` para sucesso, ``1`` para falha.
    """
    parser = _build_parser()
    args = parser.parse_args()

    # Inicializa as camadas de ferramentas e orquestração.
    tools = ToolLayer(args.repo_root)
    orchestrator = AgentOrchestrator(tools)

    # Executa o fluxo MVP respeitando os flags de controle da CLI.
    summary = orchestrator.execute(
        run_tests=not args.skip_tests,
        run_config_validation=not args.skip_config_validation,
        run_analyze_changes=not args.skip_analyze_changes,
    )

    # Renderiza o sumário no formato solicitado pelo usuário.
    if args.output == "json":
        rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    else:
        rendered = orchestrator.render_text_summary(summary)

    # Grava em arquivo somente se ambos os flags necessários estiverem presentes.
    if args.summary_file:
        tools.write_file(args.summary_file, rendered + "\n", approved=args.approve_write)

    print(rendered)
    # Retorna 1 quando qualquer etapa falhou para que shells possam detectar erros.
    return 0 if summary.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
