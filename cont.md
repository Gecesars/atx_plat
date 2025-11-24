# ATX Coverage – Situação Atual (22/11/2025)

## 1. Intervenções já feitas nesta sessão
- **Persistência por projeto:** `app_core/routes/ui.py` foi ajustado para que `/salvar-dados`, `/carregar-dados` e `/tx-location` usem `Project.settings` como fonte primária. Ao informar `projectSlug`, todos os parâmetros de TX/RX (lat/lon, potência, ganhos, P.452 etc.) são lidos/escritos apenas no JSON do projeto, deixando os atributos globais do usuário como fallback.
- **Payload inicial limpo:** `_blank_project_payload`, `_is_project_settings_empty` e `_apply_project_settings` garantem que projetos novos recebam dados totalmente zerados até que o usuário salve algo. O frontend não deve mais herdar mancha ou parâmetros do último projeto.
- **Geocoder offline:** migrei o reverse geocode da API OSM para `reverse_geocoder`. O código já está preparado para usar o dataset local (`docs/CD2022_...xlsx` + `data/ibge_population_income.json`), bastando que o pacote Python esteja instalado no mesmo virtualenv.
- **Sanitização de IDs e exportação KML:** relatórios e KMLs foram atualizados para usar data URIs e normalizar UUIDs antes de consultar o banco, evitando falhas do tipo “badly formed hexadecimal”.
- **Tests:** mantidas asserções em `tests/test_coverage_ibge.py` para cobrir o novo pipeline de tiles + IBGE.

## 2. Problemas que permanecem
1. **Município do TX não aparece ao mover o marcador.** A cada chamada ao `/tx-location` aparece o log `geocode.offline_unavailable`, indicando que o módulo `reverse_geocoder` ainda não está disponível no processo (mesmo após instalação). Sem ele, `_lookup_municipality` retorna `None`.
   - **Impacto:** o toast e os dados persistidos ficam sem município/UF/AOI.
   - **Trabalho restante:** garantir que o pacote esteja instalado no mesmo virtualenv do `python app3.py`, reiniciar o servidor e validar que `_lookup_municipality_details` não registra o warning.
2. **Erro 500 ao salvar cobertura por projeto após perda de conexão.** O Postgres fechou a conexão SSL durante um insert de ~800 MB (asset MapBiomas), deixando a session em estado “pending rollback”. Qualquer operação subsequente (incluindo `/salvar-dados`) falha até que o processo seja reiniciado ou `db.session.rollback()` seja chamado manualmente.
   - **Impacto:** operações parecem quebradas e os dados não são persistidos até reiniciar o servidor.
   - **Trabalho restante:** lidar com inserts grandes (usar streaming/chunks ou storage externo) ou implementar tratamento automático de `OperationalError` para forçar rollback antes de prosseguir.
3. **Open-Meteo ocasionalmente time out.** `/clima-recomendado` ainda depende da API externa e gera 502 em timeouts (log: `Falha ao consultar Open-Meteo`). Não é regressão, mas permanece como risco.

## 3. Estrutura do projeto (resumo)
- **app3.py / app_core/__init__.py** – inicializam a aplicação Flask, carregam variáveis de ambiente, configuram SQLAlchemy, login e Blueprints.
- **app_core/routes/ui.py** – rotas principais (home, mapa, calcular cobertura, salvar/carregar dados, tx-location, export KML, clima, etc.). Contém lógica de salvamento de parâmetros no `Project.settings` e serialização das manchas de cobertura.
- **app_core/routes/projects.py** – CRUD de projetos (listar, criar, visualizar).
- **app_core/analytics/coverage_ibge.py** – reconstrução do overlay demográfico usando tiles + IBGE offline.
- **app_core/integrations/ibge.py** – leitura dos arquivos XLSX em `docs/` para montar `data/ibge_population_income.json` e expor lookups locais + reverse geocode offline.
- **app_core/models.py** – modelos SQLAlchemy (Project, Asset, ProjectCoverage, etc.).
- **static/js/pages/** – scripts do frontend (`mapa.js`, `cobertura.js`, etc.), que consomem `/carregar-dados`, `/salvar-dados`, `/tx-location`.
- **templates/** – páginas Jinja (home, mapa, calcular_cobertura, projetos, etc.).
- **data/** – artefatos derivados (ex.: `ibge_population_income.json`).
- **docs/** – documentação (Arquitetura, planilhas IBGE, etc.).
- **venv/** – virtualenv Python 3.13 com dependências (Flask, SQLAlchemy, reverse_geocoder, etc.).

## 4. Próximos passos sugeridos
1. **Resolver geocode offline:** verificar instalação do `reverse_geocoder` (mesmo `pip` do server), reiniciar `python app3.py` e confirmar se o warning desaparece. Se persistir, logar o resultado de `ibge_api.reverse_geocode_offline` num shell interativo dentro do venv.
2. **Tratar sessão pendente:** após falhas de insert grandes, chamar explicitamente `db.session.rollback()` antes de responder ou reiniciar o processo para evitar “PendingRollbackError”.
3. **Monitorar inserts gigantes:** avaliar dividir o upload dos tiles (DEM/LULC) em assets menores ou mover para storage externo caso o Postgres continue derrubando a conexão.

---
_Documento gerado automaticamente em `cont.md` para registrar o estado atual e os pontos pendentes._***
