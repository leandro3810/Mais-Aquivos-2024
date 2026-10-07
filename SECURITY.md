# Política de segurança

## Versões com suporte

As correções de segurança são aplicadas à versão estável mais recente do projeto.

| Versão | Suporte |
| --- | --- |
| 0.3.x | Sim |
| versões anteriores | Não |

## Reportar uma vulnerabilidade

Não publique vulnerabilidades em issues, pull requests ou discussões públicas.
Envie o relato privadamente pela [página de avisos de segurança do repositório](https://github.com/leandro3810/Mais-Aquivos-2024/security/advisories/new).
Inclua os passos para reproduzir o problema, seu impacto e, se possível, uma sugestão de correção.

Esperamos confirmar o recebimento em até cinco dias úteis e manter quem reportou
informado sobre a avaliação e a resolução. Pedimos que aguarde uma correção ou
orientação antes de divulgar publicamente os detalhes.

## Proteções do agente

O agente bloqueia alguns comandos destrutivos conhecidos, impede gravações em
caminhos sensíveis (`.git`, `.github/workflows` e `SECURITY.md`), exige aprovação
explícita para gravar arquivos e limita a duração de comandos externos. Essas
proteções reduzem riscos, mas não substituem a revisão dos comandos executados
nem o uso do agente em um ambiente confiável.
