# ATX Coverage – Guia de Arquitetura e Onboarding

Este documento consolida tudo o que um(a) novo(a) integrante do time Codex precisa saber para trabalhar no projeto **ATX Coverage**. Ele descreve o funcionamento da aplicação, onde cada parte vive no repositório, como os fluxos principais interagem e quais são os próximos passos prioritários.

## Visão Geral
- **Stack principal:** Flask + SQLAlchemy (backend), templates Jinja + JS modular (frontend), armazenamento de artefatos em `storage/<user_uuid>/<project_slug>/assets`.
- **Domínio:** planejamento de cobertura de radiodifusão (FM/TV). O usuário configura parâmetros do transmissor, executa simulações (P.1546 ou RT3D), inspeciona resultados no mapa e gera relatórios técnicos com apoio de IA (Gemini).
- **Entidades chave:** `User`, `Project`, `Asset`, `CoverageJob`, `Report`. Cada projeto mantém `settings` em JSON incluindo o último snapshot da mancha (`lastCoverage`).

## Organização do Repositório
| Caminho | Propósito |
| --- | --- |
| `app_core/routes/ui.py` | Blueprint principal (`/home`, `/mapa`, `/cobertura`, `/relatorios`). Concentra formulários, execução de cobertura, persistência de snapshots e endpoints utilitários (reverse geocode, download de artefatos, etc.). |
| `app_core/reporting/service.py` | Gera o preview JSON (`/api/reports/analysis/context`) e o PDF final (`/api/reports/analysis`). Empacota métricas, imagens, receptores e dispara o módulo de IA. |
| `app_core/reporting/ai.py` | Monta o prompt do Gemini com foco em ERP calculada a partir de ganho em dBd, executa o `generate_content` e normaliza o JSON de retorno. |
| `app_core/analytics/coverage_ibge.py` | Constrói painéis demográficos cruzando a mancha (>25 dBµV/m) com municípios IBGE. Resultado vai para o snapshot e para o relatório. |
| `static/js/pages/` | Controladores front-end por página (`home.js`, `mapa.js`, `cobertura.js`, `relatorio.js`). Sincronizam formulários, localStorage (`persistProjectSlug`), spinners e chamadas AJAX. |
| `templates/` | Páginas HTML em Jinja (mapa, cobertura, painel, relatório). Os parciais usam os mesmos IDs esperados pelos scripts acima. |
| `storage/` | Onde ficam PNGs (mancha, colorbar, contorno protegido, perfis), JSONs e relatórios emitidos. Funções utilitárias vivem em `app_core/storage.py`. |
| `instruction/Contorno Protegido Rádio e TV Digital.md` | Base normativa para cálculo de contorno protegido e classificação por classe. |

Outros diretórios relevantes: `app_core/regulatory/` (anexos, payloads para pareceres ANATEL), `app_core/integrations/` (IBGE, mapas), `app_core/data_acquisition/` (DEM/SRTM e RT3D), `static/css/pages/` (estilos por tela).

## Fluxos Principais
### 1. Painel / Seleção de Projeto
- `/home` lista projetos acessíveis ao usuário e carrega o que está em `localStorage.activeProject`. A função `persistProjectSlug` em `static/js/pages/home.js` mantém a escolha entre navegações.
- O painel traz mosaicos de artefatos, receptores recentes e relatórios emitidos. A seleção "Projeto em análise" também precisa invocar `persistProjectSlug` para que mapas e IA recebam o slug correto.

### 2. Configuração e Execução da Cobertura
1. **Formulário (`templates/calcular_cobertura.html` + `static/js/pages/cobertura.js`):**
   - Todos os ganhos são informados em **dBd**. O JS converte para número limpo e envia via `/salvar-dados`.
   - Inputs extras: altura torre/RX, tilt, azimute, perdas, potência transmissor, raio alvo, modelo de propagação e engine (P.1546/RT3D).
2. **Persistência (`/salvar-dados` em `ui.py`):**
   - Normaliza floats, aplica `GAIN_OFFSET_DBI_DBD` quando preciso (armazenamos dBi no banco para compatibilidade, mas devolvemos dBd ao front).
   - Atualiza `current_user` e salva parâmetros do projeto corrente.
3. **Execução (`/calculate-coverage`):**
   - Constrói payload (metadados TX, geometria, receptores), chama `_compute_coverage_map`, produz mosaico PNG + colorbar, perfis e contorno protegido.
   - `_persist_coverage_artifacts` escreve os arquivos em `storage/.../assets` e atualiza `project.settings['lastCoverage']` com todas as referências (IDs, coordenadas, HAAT, classe, clima textual, etc.).
4. **Mapa (`templates/mapa.html` + `static/js/pages/mapa.js`):**
   - Usa Leaflet para mostrar tiles da última mancha. Painéis laterais listam receptores com IBGE, estatísticas dos tiles, metadados (ERP, tilt, HAAT, classe, DEM/LULC).
   - Sempre que o usuário troca de projeto, chamar `persistProjectSlug` e recarregar `/mapa?project=<slug>` para manter consistência no painel e no relatório.

### 3. Perfis e Receptores
- Cada clique em "Gerar perfil" salva `profile_asset_id`, `profile_meta` (distância, ERP na direção, perdas) e `profile_info` (linhas formatadas como na modal "Ver perfil").
- O relatório imprime **todos** os perfis registrados (sem limite), mantendo as mesmas linhas de texto do modal e anexando a imagem PNG correspondente. Apenas os dois primeiros entram no prompt do Gemini (`link_payload[:2]`).

### 4. Relatórios Técnicos
1. **Preview JSON** (`/api/reports/analysis/context`):
   - Chama `build_analysis_preview` (service.py) para juntar métricas, receptores, imagens inline (mancha, perfil, diagramas horizontal/vertical) e seções geradas pela IA.
   - O dicionário `diagram_images` devolve os blobs já em data URI para o front preencher `relatorio.js`.
   - Campos críticos: `metrics['tx_power_w']`, `metrics['antenna_gain_dbd']`, `metrics['losses_db']` alimentam o prompt.
2. **Geração do PDF** (`/api/reports/analysis`):
   - `generate_analysis_report` monta cabeçalho com `logo.png`, duas colunas de métricas (serviço, slug, clima, ERP, tilt, perdas), resumo executivo (texto da IA) e as seções: mancha, estatísticas de tiles, IBGE, histórico de manchas, receptores/perfis, conclusão e parecer final.
   - As imagens são inseridas com `_embed_image` / `_embed_binary_image`. Há um contorno protegido e legenda sempre que o snapshot traz os arquivos necessários.
3. **Interação com a IA:**
   - `build_ai_summary` limita o `link_payload` aos dois principais RX, gera o prompt `ANALYSIS_PROMPT` (sem palavras como “inconsistência” caso o usuário tenha solicitado) e normaliza o JSON retornado.
   - Tratamento de erros: `AIUnavailable` (sem API key) e `AISummaryError` (campos ausentes, JSON inválido). O frontend exibe mensagens amigáveis.

### 5. Demografia IBGE
- `summarize_coverage_demographics` processa os tiles acima de 25 dBµV/m, cruza com municípios e injeta `snapshot['coverage_ibge']` (nome, UF, população, renda, área coberta).
- `_estimate_population_impact` revisita os receptores válidos, faz consultas complementares ao IBGE (com cache em `snapshot['ibge_registry']`) e calcula o total estimado de habitantes cobertos.

## Execução Local
1. Criar/ativar o ambiente (`python3 -m venv venv && source venv/bin/activate`).
2. Instalar dependências (`pip install -r requirements.txt`). Certifique-se de ter as libs de sistema (GDAL não é usada; matplotlib funciona via Agg).
3. Definir variáveis `.flaskenv` ou `export FLASK_APP=app.py`. Rodar `flask run --reload`.
4. Para features IA, exportar `GEMINI_API_KEY` e (opcionalmente) `GEMINI_MODEL`.
5. Os dados de elevação (SRTM) devem existir em `SRTM/`; scripts em `app_core/data_acquisition` ajudam a baixar blocos faltantes.

## Próximos Passos Prioritários
1. **Report Context Crash:** garantir que `build_analysis_preview` use apenas chaves existentes (substituir qualquer referência a `contour_plot_bytes` por `contour_plot_preview` e validar quando o contorno não foi gerado).
2. **Tamanho da requisição Gemini:** reduzir `link_payload` ou resumir histórico (limitar `coverageHistory`, compactar metadados) para permanecer dentro do limite de 1 048 576 tokens.
3. **Persistência do projeto ativo:** auditar os seletores do painel e do mapa para sempre chamar `persistProjectSlug` ao trocar de projeto e sincronizar com `localStorage`. Garante que `/mapa`, `/cobertura` e `/relatorios` usem o mesmo slug.
4. **Perfis e IBGE completos:** conferir se cada RX traz `profile_info_lines` (caso contrário, derivar de `profile_meta` com `_profile_info_from_meta`) e se o PDF/preview listam a demografia de todos os receptores destacados.
5. **Limpeza de logs e fallbacks:** como o Open‑Meteo foi removido, confirmar se `_lookup_municipality_details` usa apenas OSM/Nominatim e se há fallback silencioso para evitar `geocoding.open_meteo.empty` no futuro.

Mantenha este arquivo atualizado conforme novas integrações ou fluxos forem introduzidos.
