# Mais Arquivos 2024 — Projeto de automação

Este repositório reúne arquivos de snapshot, transformações XSLT e um agente Python de automação para validar o projeto.

## Estrutura principal

- `ai_project_agent.py`: agente MVP de automação
- `App.xsl/`: estilos XSLT e arquivos XML de exemplo
- `.snapshots/`: arquivos de configuração e utilitários de snapshot
- `tests/`: suíte de testes automatizados
- `pyproject.toml`: configuração do projeto Python e CLI

## Agente de automação (MVP)

O agente executa um fluxo simples em três camadas:

- **Orquestração**: controla o fluxo da execução
- **Ferramentas**: analisa mudanças, roda testes e valida JSON
- **Memória curta**: mantém histórico das ações da execução atual

### Fluxo padrão

1. Analisar mudanças no repositório (`git status --porcelain`)
2. Rodar testes Python
3. Validar arquivos JSON de configuração
4. Gerar resumo final (texto ou JSON)

### Segurança aplicada no agente

- bloqueia comandos destrutivos (`rm -rf`, `git reset --hard`, `git clean -fdx`)
- exige `--approve-write` para gravar arquivo
- bloqueia escrita em caminhos sensíveis (`.git`, `.github/workflows`, `SECURITY.md`)

## Como instalar

```bash
# Na raiz do repositório
pip install -e .
pip install -r requirements-test.txt
```

## Como executar o agente

```bash
# Via script Python
python3 ai_project_agent.py --repo-root /home/runner/work/Mais-Aquivos-2024/Mais-Aquivos-2024

# Via comando CLI instalado pelo pyproject
mais-arquivos-agent --repo-root /home/runner/work/Mais-Aquivos-2024/Mais-Aquivos-2024

# Saída em JSON
mais-arquivos-agent --output json

# Gravar resumo em arquivo (exige aprovação explícita)
mais-arquivos-agent --summary-file reports/agent-summary.txt --approve-write
```

## Testes

O projeto possui uma suíte de testes automatizados cobrindo:

- `tests/test_generate_pycache.py`: script `.snapshots/Generate_pycache.py`
- `tests/test_xsl_transformations.py`: transformações XSLT em `App.xsl/`
- `tests/test_config_json.py`: estrutura e tipos de arquivos JSON
- `tests/test_ai_project_agent.py`: regras e fluxo do agente

### Executar testes

```bash
python3 -m unittest discover -s tests -v
```
