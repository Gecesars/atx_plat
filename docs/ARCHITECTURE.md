# ATX Coverage – Arquitetura e Fluxos (v2)

## Visão Geral

A aplicação ATX Coverage foi reorganizada para separar claramente backend, camada visual e assets. O backend Flask roda sob `gunicorn` (gerenciado por systemd) e expõe APIs para cadastro de usuários, controle de padrões de antena, geração de mapas de cobertura em dBµV/m e perfis profissionais. O frontend utiliza um layout comum, CSS/JS modulados por página e integrações diretas com Google Maps.

## Backend

### Fábrica da aplicação e serviço
- **`app_core/__init__.py`**: faz `load_dotenv`, lê variáveis críticas (secret key, banco, Google Maps, diretórios), inicializa `SQLAlchemy`, `LoginManager`, `Flask-Migrate` e `CORS`, registra o blueprint `app_core.routes.ui` e injeta `current_year` nos templates.
- **`app3.py`**: mantém compatibilidade com Procfile/Heroku e define limites de threads BLAS antes de executar a aplicação.
- **`/etc/systemd/system/atxcover.service`**: executa `gunicorn` a partir do virtualenv `.venv`, lê `.env` via `EnvironmentFile`, usa timeout ampliado (180s) e se reinicia automaticamente se algo falhar.

### Blueprint `app_core.routes.ui`
- **Autenticação & shell**: rotas públicas (`inicio`, `index`, `register`) e protegidas (`home`, `logout`) com Flask-Login.
- **Antena**:
  - Upload e parsing de arquivos `.pat` por `parse_pat` (E/Emax horizontal/vertical).
  - Geração/salvamento de diagramas com commit no modelo `User`.
- **Cobertura (`/calculate-coverage`)**:
  - Ajusta o centro usando regressões (`adjust_center`) e consulta a topografia SRTM (`pycraf.pathprof.height_map_data`).
  - Calcula perdas por `atten_map_fast` e separa o ganho da antena em duas componentes: horizontal (E/Emax rotacionado de acordo com a direção) e vertical (E/Emax na linha do horizonte com tilt aplicado).
  - Converte potência recebida para campo elétrico (`dBµV/m`), aplica autoescala por percentis, mascara fora do raio e retorna imagem base64, colorbar, limites, dicionário de pontos, escala e `gain_components` (base, horizontal, vertical, padrões lineares).
- **Perfil profissional (`/gerar_img_perfil`)**:
  - Reutiliza padrões horizontal/vertical e tilt para gerar gráfico emissivo: terreno sombreado, curvatura, 1ª zona de Fresnel, linha direta e anotação (ERP, ΔG, campo RX, perdas ITU). Inclui mini gráfico do padrão horizontal em dB.
- **Dados do usuário**: rotas para salvar/carregar parâmetros (`/salvar-dados`, `/carregar-dados`), atualizar tilt (`/update-tilt`), obter diagramas (`/carregar_imgs`) e gerar relatórios (`/gerar-relatorio`).
- **Helpers compartilhados**: conversão de dB⇄campo, autoescala, máscara circular, cálculos de Fresnel, ajustes de centro, etc.

## Frontend

### Layout e assets
- `templates/layouts/base.html` define cabeçalho, navegação, toasts e slots para CSS/JS.
- CSS global em `static/css/main.css` e específicos em `static/css/pages/*.css`.
- JS modular em `static/js/main.js` e `static/js/pages/*.js` (ES6, estado encapsulado, fallback para compatibilidade onde necessário).

### Páginas remodeladas
- **Landing/Login/Registro/Home**: converteram para o novo layout com validação moderna.
- **Antena** (`templates/antena.html`, `static/js/pages/antenna.js`): sidebar fixa, upload `.pat`, sliders de direção/tilt, preview em tempo real e funções globais expostas (`salvarDiagrama`, `sendDirectionAndFile`, `applyTilt`).
- **Calcular Cobertura** (`templates/calcular_cobertura.html`, `static/js/pages/cobertura.js`): formulário segmentado, campo de tilt, modais compatíveis com/sem Bootstrap e integração com `/calculate-coverage`.
- **Mapa Profissional** (`templates/mapa.html`, `static/css/pages/map.css`, `static/js/pages/mapa.js`):
  - Painel lateral com cartões (dados da TX, sliders, lista de RX, resumo de ganhos, ligação TX↔RX, colorbar).
  - Mapa Google com marcador TX arrastável, múltiplos pontos RX (lista interativa com foco/remover), polilinha TX↔RX, círculo do raio e overlay de cobertura com transparência ajustável.
  - Controle de azimute com normalização automática e renderização da linha pontilhada de boresight em tempo real, garantindo alinhamento com o diagrama aplicado à mancha.
  - Slider de opacidade, feedback visual, modal com perfil profissional.

## Fluxos

1. **Cobertura**
   - Formulário salva parâmetros em `/salvar-dados`.
   - `/calculate-coverage` recebe raio, limites, centro customizado ⇒ pycraf ⇒ campo elétrico (`dBµV/m`) com máscara circular ⇒ resposta JSON (imagem, colorbar, `gain_components`, escala, centro, raio). O frontend desenha overlay, círculo e atualiza resumos.
2. **Controle TX/RX**
   - TX arrastável atualiza painel e sugere recalcular cobertura; posição é salva ao chamar `/calculate-coverage`.
   - Cada clique adiciona RX à lista; distância, campo estimado (via dicionário retornado) e elevação (Google Elevation) são calculados. A lista permite focar, remover e gerar perfil.
3. **Perfil profissional**
   - `/gerar_img_perfil` gera gráfico com terreno sombreado, curvatura, Fresnel, linha direta, anotação e mini padrão horizontal. Resultado exibido no modal e armazenado no banco.

## Alterações Recentes
- Modularização do backend (`app_core`), uso de factory e serviço systemd ajustado.
- Conversão de todas as páginas para o layout base com assets organizados.
- Cobertura calculada em `dBµV/m` respeitando ganhos horizontal e vertical provenientes do arquivo `.pat` (incluindo tilt e direção).
- Nova experiência `/mapa`: painel profissional, TX arrastável, múltiplos RX, slider de opacidade, círculo de raio e overlay com transparência ajustável.
- Perfil do enlace redesenhado (terreno sombreado, Fresnel destacado, mini diagrama horizontal em dB e anotação rica).

## Próximos Passos
1. **Geração da Mancha**
   - Garantir que o centro passado ao pycraf corresponda exatamente ao ponto TX arrastado.
   - Ajustar dinamicamente a resolução (`map_resolution`) conforme o raio selecionado, evitando sobre/sub-amostragem.
   - Reavaliar o mecanismo de aplicação de ganho por pixel para considerar azimute/elevação com interpolação mais precisa usando os diagramas de antena.
   - Consolidar a máscara circular (aprimorar feathering e correspondência com o círculo exibido).
2. **Exportação KML/KMZ**
   - Implementar endpoint para exportar a mancha (polígonos graduais ou raster KMZ) e disponibilizar download.
3. **Performance**
   - Cachear resultados SRTM/pycraf (disco ou Redis) e considerar uso de fila assíncrona (RQ/Celery).
4. **Antena**
   - Expor métricas avançadas (HPBW, diretividade) e histórico de uploads, além de ajustes finos (normalização manual, espelhamento).

Este documento resume a arquitetura, as melhorias implantadas e o roteiro imediato para corrigir e evoluir a geração de cobertura georreferenciada.
