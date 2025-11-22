# Registro de Modificações (Codex)

## 2025-02-14
- Criado `app_core/db_types.py` com o tipo `GUID` para suportar UUIDs em PostgreSQL e SQLite de forma transparente.
- Adicionado `app_core/models.py` com os modelos `Project`, `Asset`, `CoverageJob`, `Report` e `DatasetSource`, incluindo enums, relacionamentos e mixin de timestamps para dar suporte à arquitetura multi-tenant descrita em `codex.md`.
- Atualizado `user.py` para incluir coluna `uuid`, campos de controle (`is_active`, `is_email_confirmed`, `created_at`, `updated_at`), normalização de e-mail e relacionamento com projetos.
- Ajustado `app_core/__init__.py` para carregar os novos modelos durante a inicialização da app.
- Criada migração `f9e8fceb5a1b_multi_tenant_schema.py`, adicionando as novas colunas na tabela `users` e criando as tabelas `projects`, `assets`, `coverage_jobs`, `reports` e `dataset_sources`, com enums e constraints apropriadas.
- Atualizado `migrations/versions/b9c63a12ffc1_.py` para realizar o cast explícito ao converter `antenna_pattern` para `bytea` no PostgreSQL.
- Implementados utilitários `app_core/utils.py`, `app_core/storage.py` e `app_core/email_utils.py` para lidar com slug/lookup de projetos, gerenciamento de storage multi-tenant e fluxo de envio/validação de e-mails com tokens temporizados.
- Ajustado `app_core/db_types.py` para manter GUID como `CHAR(36)` em todos os dialetos, garantindo compatibilidade com o schema existente.
- Ampliado `app_core/__init__.py` para configurar feature flags, e-mail, `STORAGE_ROOT` e registrar os novos blueprints (`projects`, `projects_api`).
- Enriquecido `app_core/routes/ui.py` com confirmação de e-mail, redefinição de senha, criação automática de projeto padrão, checagem de conta ativa e injeção da lista de projetos no painel inicial.
- Criado blueprint `app_core/routes/projects.py` com rotas HTML (`/projects`) e API (`/api/projects`) para CRUD de projetos multi-tenant, incluindo limpeza de storage.
- Novas views/templates para projetos (`templates/projects/*.html`), fluxos de autenticação (`templates/auth/*.html`) e e-mails (`templates/email/*.html|txt`).
- Atualizado layout, home e formulários de login/registro para refletir confirmação de e-mail, acesso a projetos e novos fluxos.
- Adicionada migração incremental `fd0aa8e4b52b_add_updated_timestamps.py` para incluir `updated_at` nas tabelas `assets`, `coverage_jobs`, `reports` e `dataset_sources`.
- Desabilitado login de contas não confirmadas por padrão (`ALLOW_UNCONFIRMED=false`) e configurado envio real de e-mails (`MAIL_SUPPRESS_SEND=false`) no `.env`, alinhado com o fluxo de confirmação obrigatória.
- Adicionado campo `settings` em `Project` (migração `a52f5abf3e5d_add_project_settings.py`) para persistir parâmetros de cobertura por projeto.
- Reestruturadas as páginas de projetos e cobertura: CTA direto "Planejar cobertura", cabeçalho com seleção de projeto ativo, escolha de motor (P.1546/ITM/Pycraf/RT3D) e painel profissional de parâmetros.
- Atualizados endpoints `/salvar-dados` e `/carregar-dados` para aceitar `project` e sincronizar configurações multi-tenant, armazenando snapshots em `Project.settings`.
- Refatorado `static/js/pages/cobertura.js` para fluxo moderno (notificações, carregamento por projeto, seleção de métodos, remoção de modais redundantes) e integração com o novo schema.
- Corrigido carregamento da página de cobertura para projetos sem settings anteriores (fallback seguro no template `calcular_cobertura.html`).
- Implementado `_persist_coverage_artifacts` para salvar mancha/artefatos em disco, registrar `Asset` e `CoverageJob`, e atualizar `Project.settings['lastCoverage']` (exposto em listagens e detalhes de projetos).
- Página "Calcular cobertura" agora possui painel de parâmetros (raio, escala), tooltips explicativos, status/preview da última mancha e ação "Gerar cobertura" que dispara `/calculate-coverage` e recarrega o contexto do projeto.
- Adicionada rota `projects.asset_preview` para servir artefatos armazenados; listagem e detalhe de projetos exibem miniaturas e resumos da última cobertura.
- Reestruturada `templates/dados_salvos.html` para integrar com o layout base, mostrar parâmetros principais, cards das manchas recentes e artefatos legados.

## 2025-11-04
- Ajustada a rota `/mapa` em `app_core/routes/ui.py` para aceitar slug de projeto ativo, reaproveitar a lista de projetos disponíveis, redirecionar quando a localização da TX não estiver definida e reutilizar as coordenadas iniciais.
- `_persist_coverage_artifacts` agora persiste receptores, bounds, escala, componentes de perda/ganho e dicionários de sinal no JSON e em `Project.settings['lastCoverage']`, além de expor os assets de resumo/cor barra no retorno de `/calculate-coverage` (inclusive armazenando `receivers`).
- `static/js/pages/mapa.js` foi refatorado para restaurar automaticamente a última mancha (overlay, colorbar, métricas), reidratar marcadores RX, recalcular resumos, sincronizar sliders/inputs, confirmar reprocessamento apenas quando há cobertura anterior e enviar os receptores ao backend.
- `templates/mapa.html` passou a incluir atributos `data-*` com slug e coordenadas iniciais do projeto, permitindo ao script do mapa carregar o contexto correto mesmo ao abrir a página diretamente.
- Ajustado botão "Abrir mapa de cobertura" em `templates/calcular_cobertura.html` e `static/js/pages/cobertura.js` para encaminhar o slug do projeto ativo, garantindo que a página de mapa carregue sempre o contexto correto.
- Respeitamos o slug ao restaurar manchas: `_persist_coverage_artifacts` grava `project_slug` no summary/lastCoverage, `calculate_coverage` devolve o slug e o front (`static/js/pages/mapa.js`) usa esse valor ao buscar assets, evitando recuperar overlays de outros projetos.
- Inicialização do mapa reflete parâmetros do projeto: `static/js/pages/mapa.js` busca latitude/longitude de `Project.settings` (ou da última mancha) antes de criar o mapa e de posicionar a TX, evitando reutilizar coordenadas antigas da conta.
- Rota `/mapa` passa a selecionar automaticamente o projeto com cobertura mais recente quando nenhum slug é informado, evitando abrir sempre o primeiro projeto da lista.
- `_latest_coverage_snapshot` centraliza a recuperação da última cobertura diretamente do banco (CoverageJob/Asset) e é usado por `/carregar-dados`, `/calculate-coverage` e `visualizar_dados_salvos`, eliminando as dependências de arquivos legados.
- Botões da página de planejamento agora reportam feedback imediato: `/salvar-dados` envia mensagens ao `notify`, e “Abrir mapa de cobertura” encaminha direto para `/mapa?project=<slug>` tanto via link quanto via fallback JS (cobertura.js, calcular_cobertura.html).

## 2025-11-05
- Reescrevemos `app_core/data_acquisition.py` para centralizar a aquisição multi-engine: downloads SRTM/MapBiomas/OSM agora retornam `Asset`/`DatasetSource`, registram metadados (tiles, ano, bbox) e expõem `ensure_datasets_for_engine`, incluindo atualização das rotas do projeto (`download_osm_buildings` passa a persistir em `assets/building_footprints`).
- `calculate_coverage` (em `app_core/routes/ui.py`) dispara a preparação de datasets antes de cada engine, reaproveitando a nova API, e `_run_itm_engine` deixou o FSPL aproximado para usar perfis `pycraf` (com perdas Bullington, estatística ITM, perfis resumidos e feedback estruturado por receptor).
- Ajustamos `_persist_coverage_artifacts`/`_persist_itm_artifacts` para versionar as fontes usadas (`datasets`), e substituímos o mapeamento de clutter por `_resolve_clutter_zones`, suportando rótulos amigáveis (`urbano`, `suburbano`, etc.).
- `templates/calcular_cobertura.html` e `static/js/pages/cobertura.js` ganharam campos dinâmicos por motor (ex.: ano de land cover para Pycraf/RT3D) e toasts automáticos que resumem a aquisição de DEM/LULC/edificações ao final da execução.
- Suíte `tests/test_data_acquisition.py` adicionada cobrindo `ensure_datasets_for_engine` (Pycraf/RT3D) e `_run_itm_engine`, com mocks das chamadas HTTP/pycraf para validar metadados e integração com o banco.
- Testes executados com `python -m unittest tests.test_data_acquisition` (avisa apenas warnings de terceiros/SQLite, mas finaliza com sucesso).
- Página “Calcular cobertura” ganhou modal de receptores (Google Maps) permitindo capturar pontos RX interativamente, arrastar/editar altura e sincronizar com o textarea ITM; botões de limpeza/aplicação se integram ao fluxo existente e o front mostra toasts sobre datasets carregados.
- Ajustamos `/gerar_img_perfil` para receber o `projectSlug`, garantir DEM dedicado por projeto (via `ensure_srtm_for_bbox`) e usar `SrtmConf` apontando para `storage/<user>/<slug>/assets/dem`, evitando conflitos de tiles duplicados ao gerar perfis TX→RX. O fetch em `static/js/pages/mapa.js` agora inclui o slug do projeto ativo.
- O front de mapas (`static/js/pages/mapa.js`) passou a compartilhar um helper único `getActiveProjectSlug()` usado tanto na geração do perfil quanto na de cobertura; o payload de `/gerar_img_perfil` agora recusa a ação caso o slug esteja indefinido, garantindo que o backend sempre saiba qual repositório DEM utilizar.
- `/tx-location` aceita `projectSlug`, replica as coordenadas em `project.settings`, atualiza município/elevação e marca `lastCoverage.stale=true`, garantindo rastreabilidade por projeto.
- A página “Calcular cobertura” salva automaticamente as coordenadas escolhidas no modal (mapa e inserção manual) assim que o usuário confirma o ponto, chamando `/tx-location` com o projeto ativo.
- O mapa de cobertura (`static/js/pages/mapa.js`) agora persiste a nova posição da TX ao arrastar o marcador, limpa a mancha atual e impede restaurar coberturas quando as coordenadas foram alteradas ou marcadas como `stale`, exibindo um aviso para gerar uma nova mancha.

## 2025-11-07
- Atualizei `app_core/data_acquisition.py` para rehidratar e registrar assets SRTM/MapBiomas já existentes, normalizei o ano válido da coleção e expus `ensure_geodata_availability`, garantindo downloads idempotentes e metadados completos.
- `calculate_coverage` passou a invocar automaticamente essa rotina antes de qualquer engine, anexando ao JSON de resposta os tiles e o ano de LULC usados; o frontend (`static/js/pages/cobertura.js`) agora exibe alertas rápidos sempre que as bases forem confirmadas.
- `/gerar_img_perfil` passou a receber o slug do projeto, prepara os DEMs tanto para TX quanto RX reaproveitando o cache e mantém o restante do cálculo inalterado.
- A página do mapa ganhou feedback visual dedicado: incluí `profileSpinner` em `templates/mapa.html`, utilizei o helper `getActiveProjectSlug()` no JS e, ao gerar o perfil, o botão é desabilitado enquanto o spinner acompanha a requisição.
- Trocamos o download DEM para o servidor viewpano (mesmo usado pelo pycraf), armazenando os `.hgt` por projeto (`storage/<uuid>/<slug>/assets/dem`) e registrando a origem/tiles nos metadados; o mesmo fluxo já garante MapBiomas como fonte de land cover.
- `calculate_coverage` e `/gerar_img_perfil` agora usam o diretório DEM específico do projeto ao configurar o `SrtmConf`, evitando que tiles escapem para `./SRTM` e garantindo isolamento multi-tenant.
- O diretório `../SRTM` virou cache compartilhado dos tiles viewpano: `download_srtm_tile` baixa uma única vez, os `Asset` referenciam esse caminho relativo e todos os cálculos (mapa, perfil, ajustes de elevação) apontam para o mesmo repositório, eliminando downloads duplicados.
- Os perfis e heatmaps passaram a abrir `SrtmConf` em modo `download='none'` com fallback para `'missing'`, o que evita round-trips desnecessários ao viewpano sempre que o tile já estiver em cache e reduz o tempo de geração do perfil de enlace.
- A UI do mapa recebeu legendas ricas: cada RX tem label/tooltip com nível e altitude, o TX mostra município/potência/elevação/altura em um cartão flutuante e o backend persiste essas métricas em `lastCoverage`.
- Arrastar a TX ou inserir coordenadas em “Calcular cobertura” dispara `/tx-location`, que atualiza município/elevação no usuário e no projeto; o front-end aplica os novos valores imediatamente para manter os painéis e legendas sincronizados.
- Quando a cobertura é salva, capturamos `tx_parameters` (potência, perdas, alturas) e os rótulos completos dos receptores (nível, altitude, nome). Esses dados são serializados no summary JSON e carregados de volta na interface para que a legenda mostre o último estudo mesmo após recarregar a página.
- `_lookup_municipality` agora tenta primeiro o geocoder da Open‑Meteo e, em caso de erro/404, cai automaticamente para o Nominatim/OSM, garantindo que o cartão da TX continue mostrando o município mesmo em coordenadas remotas.
- Ao gerar o perfil do enlace usamos a Google Elevation API sempre que `GOOGLE_MAPS_API_KEY` estiver configurada, com a quantidade de amostras proporcional ao comprimento do enlace; se a API falhar voltamos para o perfil SRTM padrão, registrando o fallback para o usuário.


## 2025-11-08
- Adicionada `ensure_rt3d_scene` em `app_core/data_acquisition.py`, que gera e cacheia a malha urbana (Photorealistic 3D Tiles quando disponível, fallback OSM/Overpass) e registra o asset `building_footprints` por projeto.- Cobertura RT3D ganhou overlay próprio (qualidade/difração) e o mapa exibe o painel 'Cenário urbano RT3D' com visualização interativa das edificações, além de permitir alternar/atualizar a malha urbana diretamente pela UI.

- `_compute_coverage_map` e `_apply_rt3d_penalty` agora consomem a malha para aplicar oclusões, ganhos por reflexão e diagnóstico de multipercurso; `_persist_coverage_artifacts` guarda `rt3d_scene/rt3d_diagnostics` no summary e em `Project.settings['lastCoverage']`.
- `/calculate-coverage` devolve `rt3dScene`/`rt3dDiagnostics`, enquanto `static/js/pages/cobertura.js` persiste os novos parâmetros RT3D e exibe notificações de carregamento de DEM/LULC/Buildings.
- `templates/mapa.html`, `static/css/pages/map.css` e `static/js/pages/mapa.js` ganharam o painel “Cenário urbano RT3D”, renderização da malha (círculos coloridos proporcionalmente à altura), toggle/refresh da camada e integração automática ao restaurar a última cobertura.
- Motor RT3D agora pula o raster P.452 completo: gera um grid próprio baseado em FSPL, aplica o solver determinístico e entrega apenas o overlay de qualidade (com fallback para campo clássico), reduzindo o tempo de processamento e exibindo uma visualização realmente ray traced.
- No fluxo RT3D agora pulamos totalmente a grade P.452: `_compute_coverage_map` desvia para `_compute_rt3d_only_map`, que monta um grid rápido baseado em FSPL, aplica as penalidades determinísticas e envia apenas o overlay “Qualidade RT3D [dB]” (além de salvar esse preview no storage).
- Interface RT3D melhorada: quando o motor é selecionado, o painel “Cenário urbano RT3D” mostra estatísticas atualizadas, toggles para malha/raios, e o mapa desenha até 250 raios coloridos (LOS/reflexão/difração/profile) diretamente sobre a malha urbana.

## 2025-11-08
- Reescrevi a rota `home` em `app_core/routes/ui.py` para montar um relatório executivo do projeto ativo: seleção por slug, agregação dos parâmetros salvos/usuário/última cobertura, normalização de receptores, métricas de perdas & ganhos, artefatos disponíveis e atalhos de ação (planner, mapa, relatório).
- Atualizei completamente `templates/home.html`, criando a “capa” do projeto com hero card, métricas técnicas agrupadas, prévia da mancha, tabelas de receptores/datasets, galeria de artefatos e bloco de notas integrado, além do seletor dinâmico de projetos.
- Substituí `static/css/pages/home.css` por um pacote de estilos focado em cards profissionais, badges, grids de artefatos e painéis escuros para métricas, alinhando a identidade visual do dashboard.
- Implementado o módulo regulatório ANATEL/MCom: novos modelos/tabelas (`regulatory_reports`, `regulatory_attachments`, `regulatory_validations`), pipeline de validação (DECEA/RNI/Serviço/SARC), importadores HRP/equipamentos, motores ERP/RNI/SARC e gerador de PDF/ZIP com templates HTML. API REST (`/api/regulator`) e CLI (`bin/reg_report.py`) permitem criar relatórios que são persistidos no storage multi-tenant.
- Acrescentei o checklist “Básico de Radiodifusão/ANATEL”: `app_core/regulatory/anatel_basic.py` consolida os 19 itens do caderno (conceituação, outorga, RF, FISTEL etc.) com dados do projeto/usuário e marca campos pendentes; ele alimenta a nova página do relatório (`relatorio_p5_anatel.html`), o endpoint `GET /api/regulator/projects/<slug>/basic-form` e o botão “Checklist ANATEL” exibido no dashboard. Os placeholders de anexos agora podem ser substituídos pelos documentos oficiais, alinhados ao guia do Gov.br.
- Sincronizei os fluxos de estudo/relatórios em dois caminhos: 1) Relatório de Análise – novo serviço `app_core/reporting/service.py` gera PDFs com o snapshot da mancha (parâmetros, métricas, imagem) e grava o asset+registro na tabela `reports`; exposto via `POST /api/reports/analysis` (blueprint `app_core/reporting/api`). 2) Relatório ANATEL – reaproveita o módulo regulatório com anexos automáticos (ART/DECEA/RNI/HRP/Laudo) gerados a partir do PDF oficial (ver `app_core/regulatory/attachments.py`). A Home ganhou botões dedicados, com feedback e links diretos para os downloads.
- Aperfeiçoei o relatório inteligente: layout multi-página fixo (visão geral, cobertura e parecer com anexos), posicionamento consistente para mancha/colorbar/imagens e spinner dedicado no botão “Baixar Relatório PDF”. Se o Gemini falhar ou não retornar texto, levantamos `AnalysisReportError` e cancelamos o download, garantindo que todo PDF entregue contenha o parecer técnico assistido.
- O parecer do modelo agora vem em JSON estruturado (overview, cobertura, perfil, padrões H/V e recomendações). Cada imagem do relatório recebeu o respectivo texto explicativo logo abaixo e a seção final lista as recomendações. Isso eliminou sobreposições, deixou o layout alinhado e garante que o PDF só seja emitido quando o retorno do Gemini estiver íntegro.
- Transformei o relatório simples em uma versão “inteligente”: `app_core/reporting/service.py` agora aplica um layout profissional (cabeçalho, blocos de métricas, imagens da mancha, colorbar e anexos como perfil/diagramas) e injeta um resumo técnico produzido pelo Gemini (`app_core/reporting/ai.py`) – o texto descreve a cobertura e gera recomendações com base nos dados do projeto. A rota `/api/reports/analysis` continua igual, mas o PDF resultante passa a incorporar tanto o conteúdo visual quanto o parecer gerado pelo modelo.
- A rota `/gerar-relatorio` foi alinhada ao novo fluxo: quando há projeto selecionado (ou o mais recente do usuário), ela chama `generate_analysis_report` e entrega o mesmo PDF inteligente via download direto; se nenhum projeto tiver mancha salva, gera um PDF-resumo de usuário como fallback. Assim, o link na UI sempre baixa o relatório com o parecer do Gemini e todos os artefatos da mancha.


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


