# Configuração do Ambiente de Desenvolvimento para IA

Este guia ajudará você a configurar um ambiente de desenvolvimento para projetos de Inteligência Artificial (IA).

## 1. Escolha do Ambiente Base
- **Sistema Operacional**: Recomendado usar Ubuntu 20.04+ ou Windows 10/11 com WSL2.
- **Gerenciadores de Pacotes**:
  - `conda` (Anaconda/Miniconda) — Gerenciamento de ambientes virtuais.
  - `pip` — Gerenciador de pacotes Python.

## 2. Instalação de Dependências
### 2.1 Instale Python
- Recomendado: Python 3.8 ou superior.
- Verifique a instalação: `python --version`.

### 2.2 Configure um Ambiente Virtual
```bash
# Usando Conda
conda create -n ia_env python=3.8
conda activate ia_env

# Ou usando venv
python -m venv ia_env
source ia_env/bin/activate  # Para Linux/Mac
ia_env\Scripts\activate     # Para Windows
