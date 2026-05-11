Diretório de Snapshots
Este diretório contém snapshots do seu código para interações de IA. Cada snapshot é um arquivo markdown que inclui informações relevantes sobre contexto de código e estrutura de projeto.

O que está incluído nos snapshots?
Arquivos de código selecionados e seus conteúdos
Estrutura do projeto (se habilitada)
Sua solicitação/pergunta para a IA
Configuração
Você pode personalizar o comportamento do instantâneo em config.json.

## Testes

O projeto possui uma suíte de testes automatizados cobrindo:

- **`tests/test_generate_pycache.py`** — testa o script `.snapshots/Generate_pycache.py` (compilação de arquivos `.py`, filtragem de tipos, mensagens de saída)
- **`tests/test_xsl_transformations.py`** — testa as transformações XSLT em `App.xsl/` usando `lxml` (saída HTML, saída texto, parâmetros bidi, fixtures XML)
- **`tests/test_config_json.py`** — valida estrutura e tipos dos arquivos JSON de configuração (`config.json`, `package.json`, `.eslintrc.json`, `Composer.Json`)

### Como executar

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt

# Executar todos os testes
python3 -m unittest discover -s tests -v
```

## Agente de IA de automação (MVP)

Foi adicionado o script `ai_project_agent.py` com três camadas:

- **Orquestração**: define e executa o fluxo MVP
- **Ferramentas**: análise de mudanças, execução de testes e validação de JSON
- **Memória curta**: histórico de ações da execução atual

### Fluxo MVP

1. Analisar mudanças no repositório (`git status --porcelain`)
2. Rodar testes Python
3. Validar arquivos JSON de configuração
4. Gerar resumo final (texto ou JSON)

### Entradas, saídas e limites

- **Entradas**: raiz do repositório, opções de execução e comando de teste
- **Saídas**: resumo em stdout e opcionalmente em arquivo
- **Limites de segurança**:
  - bloqueia comandos destrutivos (`rm -rf`, `git reset --hard`, `git clean -fdx`)
  - exige `--approve-write` para gravar arquivo
  - bloqueia escrita em caminhos sensíveis (`.git`, `.github/workflows`, `SECURITY.md`)

### Uso

```bash
# Fluxo completo com resumo em texto
python3 ai_project_agent.py --repo-root /home/runner/work/Mais-Aquivos-2024/Mais-Aquivos-2024

# Resumo em JSON
python3 ai_project_agent.py --output json

# Gravar resumo em arquivo (exige aprovação explícita)
python3 ai_project_agent.py --summary-file reports/agent-summary.txt --approve-write
```

