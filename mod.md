# ATX Coverage – Relatório IBGE e Tiles de Cobertura

## Contexto
- Objetivo: incorporar ao pipeline de geração de relatórios (`/relatorios/digital`) informações sociodemográficas (população total e renda per capita) dos municípios cujo campo elétrico estimado excede **25 dBµV/m**.
- Fonte auxiliar: documento `docs/ibge.pdf` (“API IBGE_ População Ativa e Renda”) contendo tabelas de referência para população ativa, renda e outras métricas.
- Cobertura: os tiles rasterizados (`/projects/<slug>/assets/<asset_id>/tiles/{z}/{x}/{y}.png`) representam a mancha de cobertura – precisamos analisá-los para encontrar áreas acima do limiar definido.

## Requisitos Funcionais
1. **Parser do PDF (`docs/ibge.pdf`):**
   - Extrair para estrutura tabular os campos necessários (ex.: código IBGE, município, UF, população total, renda per capita).
   - Normalizar nomes de municípios/UF para coincidir com os retornos do reverse geocoding e da API IBGE já utilizada.
   - Persistir os dados em cache (ex.: JSON ou base) para acesso rápido durante a geração do relatório.

2. **Análise da Mancha (tiles) com limiar 25 dBµV/m:**
   - Converter os tiles (PNG) em matriz numérica e reconstruir o grid em coordenadas geográficas.
   - Identificar pixels com valores ≥ 25 dBµV/m.
   - Determinar municípios que possuem interseção com estes pixels (usando shapefile/IBGE API ou reverse geocoding em grade reduzida).
   - Consolidar lista única de municípios elegíveis, com estatísticas agregadas (área coberta, porcentagem da mancha, etc. – opcional).

3. **Integração ao Relatório:**
   - Expandir `app_core/reporting/service.py` para incluir sessão “Demografia e Renda por Município Coberto”.
   - Exibir, para cada município elegível:
     - População total
     - Renda per capita
     - Fonte (IBGE, ano)
   - Ajustar `build_analysis_preview` e `generate_analysis_report` para expor esses dados (JSON + PDF).
   - Incluir nota metodológica (limiar 25 dBµV/m, uso de tiles, referência ao documento IBGE).

## Requisitos Técnicos
- Dependências potenciais: `pdfplumber` ou `camelot` para parsing do PDF; `rasterio`, `numpy`, `shapely` para análise espacial.
- Definir camada de cache (ex.: armazenar CSV/JSON em `storage/<uuid>/<slug>/assets/ibge/`).
- Garantir que o parser seja idempotente e reutilizável (executado uma vez e reaproveitado).
- Adicionar testes unitários cobrindo:
  - Extração de dados do PDF (amostra).
  - Pipeline que recebe tiles sintéticos e identifica municípios corretos.
  - Geração de relatório com blocos adicionais.

## Próximos Passos
1. Implementar módulo `app_core/analytics/ibge_catalog.py` (ou similar) para ler `docs/ibge.pdf` e salvar dados normalizados.
2. Criar utilitário `app_core/coverage/tiles_analysis.py`:
   - Funções para baixar tiles locais, reconstituir grid georreferenciado e aplicar limiar.
   - Função para mapear pixels → município (usar reverse geocode com cache ou geometria municipal).
3. Integrar resultados na camada de serviço `reporting.service` e atualizar `AI` prompt se necessário.
4. Atualizar documentação e notas do relatório para refletir a nova sessão e fontes de dados.

> **Nota:** o parser do PDF deve ser robusto a formatações (colunas múltiplas, cabeçalhos) — avaliar se exportar previamente para CSV facilita a manutenção.





