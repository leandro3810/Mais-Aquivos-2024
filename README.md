# Mais Arquivos 2024 — Projeto de automação

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Versão](https://img.shields.io/badge/versão-0.2.0-green)](pyproject.toml)
[![Licença](https://img.shields.io/badge/licença-MIT-lightgrey)](LICENSE)

Este repositório reúne arquivos de snapshot, transformações XSLT e um agente Python de automação para validar o projeto.

## Estrutura principal

```
Mais-Aquivos-2024/
├── ai_project_agent.py    # Agente MVP de automação (v0.2.0)
├── App.xsl/               # Diretório com transformações XSLT e arquivos XML
├── .snapshots/            # Arquivos de configuração e utilitários
├── tests/                 # Suíte de testes automatizados
├── pyproject.toml         # Configuração do projeto Python e CLI
├── requirements-test.txt  # Dependências de teste
└── README.md              # Este arquivo
```

## Agente de automação (MVP)

O agente executa um fluxo simples em três camadas:

| Camada | Classe | Responsabilidade |
|--------|--------|-----------------|
| Memória curta | `AgentMemory` | Histórico circular (FIFO) das ações da execução |
| Ferramentas | `ToolLayer` | Executa comandos e valida arquivos com proteções |
| Orquestração | `AgentOrchestrator` | Coordena o fluxo e gera o sumário final |

### Fluxo padrão

1. Analisar mudanças no repositório (`git status --porcelain`)
2. Rodar testes Python (`unittest discover`)
3. Validar arquivos JSON de configuração
4. Gerar resumo final (texto ou JSON)

### Segurança aplicada no agente

- Bloqueia comandos destrutivos (`rm -rf`, `git reset --hard`, `git clean -fdx`)
- Exige `--approve-write` para gravar arquivo
- Bloqueia escrita em caminhos sensíveis (`.git`, `.github/workflows`, `SECURITY.md`)

## Como instalar

```bash
# Na raiz do repositório
pip install -e .
pip install -r requirements-test.txt
```

## Como executar o agente

```bash
# Exibir versão
mais-arquivos-agent --version

# Via script Python
python3 ai_project_agent.py --repo-root .

# Via comando CLI instalado pelo pyproject
mais-arquivos-agent --repo-root .

# Saída em JSON (inclui started_at e duration_seconds)
mais-arquivos-agent --output json

# Pular análise de mudanças
mais-arquivos-agent --skip-analyze-changes

# Gravar resumo em arquivo (exige aprovação explícita)
mais-arquivos-agent --summary-file reports/agent-summary.txt --approve-write
```

## Testes

O projeto possui uma suíte de testes automatizados cobrindo:

| Arquivo de teste | O que cobre |
|-----------------|-------------|
| `tests/test_ai_project_agent.py` | Regras e fluxo completo do agente |
| `tests/test_config_json.py` | Estrutura e tipos dos arquivos JSON |
| `tests/test_xsl_transformations.py` | Transformações XSLT em `App.xsl/` |
| `tests/test_generate_pycache.py` | Script `.snapshots/Generate_pycache.py` |

### Executar testes

```bash
python3 -m unittest discover -s tests -v
```

## Snapshots

Os snapshots registram o estado do projeto em datas específicas:

| Arquivo | Data |
|---------|------|
| [`Snapshot-2025-04-19.md`](Snapshot-2025-04-19.md) | 19 de abril de 2025 |
| [`Snapshot-2026-08-28.md`](Snapshot-2026-08-28.md) | 28 de agosto de 2026 |

## Dependências Python

| Pacote | Versão |
|--------|--------|
| `lxml` | `>=4.9.0` (teste) |
| `setuptools` | `>=61.0` (build) |

> Dependências extras de projeto (Django, numpy, pandas, requests, scikit-learn) estão declaradas em `.snapshots/Requirements.txt`.
