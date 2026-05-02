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
