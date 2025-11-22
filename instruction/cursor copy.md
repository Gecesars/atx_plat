Você é um assistente de desenvolvimento de um sistema de engenharia de RF para cálculo de cobertura de TV/rádio e análise de potencial de audiência por município, usando dados oficiais do IBGE.

=====================================
1. CONTEXTO DO PROJETO
=====================================

Já existe um projeto em funcionamento com:

- Backend em Python (Flask), rodando em Linux/WSL, com integração a PostgreSQL.
- Uma página `mapa.html` que:
  - Mostra a mancha de cobertura (heatmap) em torno de um transmissor.
  - Permite criar links de perfil/enlace entre o transmissor e pontos do mapa.
  - Já consome dados gerados por uma função Python (ex.: `_compute_coverage_map(...)`) que retorna artefatos de cobertura (ex.: grade, escala, metadados) para renderização no front.
- Uma ferramenta `municipio_info.py` que:
  - Consulta o IBGE (API de localidades e APIs tipo SIDRA/PNAD Contínua) para obter informações territoriais de municípios e, futuramente, dados de população ativa, renda, etc.
  - Usa o documento “API IBGE – População Ativa e Renda.pdf” como referência para escolher as tabelas/variáveis corretas na API do IBGE.
- Uma página `relatorio.html` que será usada como editor de relatório técnico.
- Um fluxo de geração de PDF profissional a partir de um relatório HTML (ex.: WeasyPrint, wkhtmltopdf ou similar).

Seu trabalho é:
1. Aprimorar o cálculo de cobertura de RF em `mapa.html`, refinando o modelo para uma grade de “tiles” com valor médio em dBµV/m.
2. Integrar isso com os dados do IBGE para estimar população potencialmente atendida (idade > 18 anos) em cada município com nível de campo acima de um limiar (25 dBµV/m).
3. Gerar dados estruturados para alimentar `relatorio.html`, permitindo edição manual pelo usuário.
4. Implementar a geração de um PDF final com um relatório profissional a partir do conteúdo de `relatorio.html`.

=====================================
2. OBJETIVO PRINCIPAL
=====================================

Criar um pipeline completo:

TX + Modelo de propagação → Mancha de cobertura (campo em dBµV/m) → Discretização em tiles → Agregação por município → Consulta ao IBGE (população > 18) → Cálculo de audiência potencial → Relatório técnico (HTML editável) → PDF profissional.

=====================================
3. CÁLCULO DA MANCHA DE COBERTURA EM `mapa.html`
=====================================

Você deve:

1. Localizar o backend que gera a mancha de cobertura usada em `mapa.html` (funções como `_compute_coverage_map` ou equivalente).
2. Garantir que o backend:
   - Receba parâmetros do transmissor (coordenadas, frequência, ERP, diagrama de irradiação, altura, etc.).
   - Aplique o modelo de propagação já utilizado no projeto (pode ser modelo simplificado ou algo mais avançado já existente).
   - Produza um campo elétrico em **dBµV/m** sobre uma área de interesse (raio definido pelo usuário ou padrão) ao redor do transmissor.
3. Representar a mancha de cobertura em uma grade regular (raster ou pseudo-raster) com resolução configurável, por exemplo:
   - Grade em lat/lon ou coordenadas projetadas (UTM), com passo fixo (ex.: 250 m, 500 m, 1 km).
4. Expor ao front-end (`mapa.html`) um objeto JSON contendo:
   - Metadados (centro, raio, resolução, unidade = dBµV/m).
   - Uma matriz ou lista de pontos com:
     - Coordenadas (lat, lon).
     - Valor de campo estimado (dBµV/m).
   - Escala de cores (mín, máx, intervalos) para renderização do heatmap.

A implementação deve ser numérica e determinística (sem IA nesse passo), apenas cálculo e organização dos dados.

=====================================
4. DIVISÃO EM TILES COM NÍVEL MÉDIO EM dBµV/m
=====================================

A partir da mancha de cobertura calculada acima, você deve:

1. Definir um esquema de tiles:
   - Pode ser uma grade quadrada (ex.: 1 km × 1 km) ou similar, coerente com a resolução do cálculo.
2. Para cada tile:
   - Coletar todos os pontos da grade de campo que caem dentro desse tile.
   - Calcular o valor médio em dBµV/m dentro daquele tile (média aritmética dos valores em dBµV/m já é aceitável aqui).
   - Armazenar:
     - ID do tile.
     - Geometria (polígono ou bounding box).
     - Valor médio de campo (dBµV/m).
3. Gerar uma estrutura de dados (JSON) com a lista de tiles, a ser usada tanto:
   - Para visualização no `mapa.html` (por exemplo, tiles em cores diferentes de acordo com o nível médio).
   - Quanto para a lógica de interseção com municípios e cálculo de audiência potencial.

Importante:
- Os tiles devem ser consistentes entre o backend e o front-end, permitindo clicar em um tile e ver seus dados.
- Você deve organizar essa lógica no backend (Python), mantendo o front apenas como consumidor dos dados.

=====================================
5. INTEGRAÇÃO COM MUNICÍPIOS E LIMIAR DE COBERTURA
=====================================

Agora, conecte a grade de tiles aos municípios:

1. Para cada tile:
   - Se o valor médio de campo em dBµV/m for **maior que 25 dBµV/m**, considerar esse tile como “valendo cobertura”.
2. Obtenha a lista de municípios que intersectam a área de cobertura:
   - Você pode:
     - Utilizar um arquivo de malha municipal (shapefile/GeoJSON) já disponível no projeto, OU
     - Utilizar o sistema de municípios já usado por `municipio_info.py`, adaptando/estendendo conforme necessário.
3. Para cada município:
   - Calcular:
     - Quantidade de tiles com cobertura > 25 dBµV/m dentro do município.
     - Uma métrica de “percentual de área do município coberta” (aproximada pelo número/área dos tiles cobertos vs. total do município).
4. Você deve estruturar os resultados por município, incluindo:
   - Código IBGE do município.
   - Nome do município.
   - UF.
   - Percentual de área coberta (aproximado).
   - Nível médio de campo em dBµV/m (média dos tiles do município, por exemplo).
   - Flag indicando se o município entra na análise de audiência (>=25 dBµV/m em algum tile).

=====================================
6. CONSULTA AO IBGE – POPULAÇÃO > 18 ANOS
=====================================

Objetivo: para todos os municípios com nível de cobertura relevante (tiles > 25 dBµV/m), você deve buscar no IBGE a população com idade acima de 18 anos, separada por sexo.

Regras:

1. Usar as APIs do IBGE conforme documentadas no arquivo “API IBGE_ População Ativa e Renda.pdf” (já fornecido no repositório).
   - Ler esse PDF, identificar:
     - qual tabela SIDRA/PNAD Contínua usar,
     - quais variáveis correspondem a população por faixa etária,
     - como filtrar para ≥18 anos e por sexo.
2. Para cada município com cobertura significativa:
   - A partir do código IBGE do município (7 dígitos), montar as requisições à API do IBGE para obter:
     - População total maior que 18 anos.
     - População masculina > 18.
     - População feminina > 18.
   - Tratar erros de API:
     - Respostas 500/503 devem ser logadas.
     - Implementar retry simples e fallback.
     - Se não for possível obter os dados, registrar essa condição no relatório com mensagem clara.
3. Criar uma camada de cache em disco (JSON) ou em banco para evitar chamadas repetidas:
   - Por exemplo, uma tabela `ibge_municipio_populacao` com:
     - municipio_id (código IBGE)
     - ano ou período de referência
     - pop_total_maior_18
     - pop_masc_maior_18
     - pop_fem_maior_18
     - data_hora_atualizacao
4. Integrar esse dado de população ao resultado de cobertura por município:
   - Para cada município com cobertura >25 dBµV/m:
     - Anexar as colunas de população >18.
     - Calcular uma estimativa de “telespectadores potenciais” considerando que toda a população >18 do município dentro da área coberta é potencial audiência (mesmo que seja uma aproximação).

=====================================
7. ESTRUTURA DE DADOS PARA O RELATÓRIO
=====================================

Ao final do cálculo de cobertura + IBGE, o backend deve gerar uma estrutura consolidada (por exemplo, um dicionário/JSON) contendo:

1. Metadados do projeto:
   - Nome do projeto.
   - Local do transmissor (coordenadas, município, UF).
   - Frequência, ERP, altura de antena, etc.
2. Dados da cobertura:
   - Raio analisado.
   - Modelo de propagação.
   - Mapa de tiles com nível médio em dBµV/m.
   - Estatísticas gerais: área total coberta acima de 25 dBµV/m, máximo/mínimo/média de campo, etc.
3. Dados por município:
   Para cada município com cobertura relevante:
   - Código IBGE, nome, UF.
   - Percentual de área coberta (ou índice proporcional por tiles).
   - Nível médio de campo (dBµV/m).
   - População total >18 anos.
   - População >18 por sexo (masculino, feminino).
   - Estimativa de telespectadores potenciais.
4. Resumo agregado:
   - Soma da população >18 anos em todos os municípios cobertos.
   - Número de municípios com cobertura acima de 25 dBµV/m.
   - Quais municípios concentram maior audiência potencial.

Essa estrutura deve ser serializável em JSON para:
- ser enviada ao front-end (`relatorio.html`) e
- ser persistida no banco.

=====================================
8. EDIÇÃO DO RELATÓRIO EM `relatorio.html`
=====================================

Você deve:

1. Criar/ajustar o endpoint backend que alimenta `relatorio.html` com a estrutura de dados descrita acima.
2. Em `relatorio.html`, montar uma interface que:
   - Liste os dados principais em tabelas organizadas (geral + por município).
   - Mostre gráficos simples (opcional, se já houver biblioteca) para:
     - distribuição da audiência potencial por município,
     - mapa simplificado ou tabela ordenada por população >18 coberta.
   - Permita ao usuário:
     - Editar textos descritivos (introdução, metodologia, conclusões).
     - Ajustar alguns campos textuais (por exemplo: nome da emissora, observações de engenharia, notas sobre limitações do modelo).
3. Manter a separação:
   - Dados numéricos de cobertura/IBGE vêm do backend.
   - Textos descritivos podem ser editados livremente no front e salvos em banco.

O objetivo é que esse HTML seja a base para o PDF final.

=====================================
9. GERAÇÃO DO PDF PROFISSIONAL
=====================================

Por fim, você deve:

1. Implementar uma rota no backend que:
   - Carregue o conteúdo atual do relatório (dados + textos editados).
   - Renderize esse conteúdo em um template HTML específico para PDF (por exemplo, `relatorio_pdf.html`), com layout profissional:
     - Página de rosto com título do projeto, dados principais do transmissor e área de cobertura.
     - Páginas seguintes com:
       - tabelas de municípios e suas populações >18,
       - estatísticas de cobertura,
       - eventuais gráficos, se disponível.
   - Converta esse HTML para PDF usando a ferramenta já adotada no projeto (WeasyPrint, wkhtmltopdf, etc.).
2. O PDF gerado deve:
   - Ser adequado para envio a órgãos reguladores e clientes.
   - Não conter marcas d’água “gerado automaticamente”.
   - Ter cabeçalho/rodapé padronizados (se o projeto já define isso).
3. Fornecer um link ou botão em `relatorio.html` para:
   - “Gerar PDF” → que chama essa rota e faz o download do arquivo.

=====================================
10. ESTILO DE CÓDIGO E CUIDADOS
=====================================

Ao modificar o código, siga estas diretrizes:

- Use Python moderno (3.10+), tipagem opcional (`typing`) onde fizer sentido.
- Código limpo e organizado:
  - funções pequenas, bem nomeadas,
  - comentários explicando trechos críticos (especialmente o cálculo de cobertura e agregação por tiles/município).
- Trate erros de rede com o IBGE (timeouts, 500, 503) com:
  - tentativas de retry,
  - logs claros,
  - mensagens amigáveis no relatório quando o dado não estiver disponível.
- Não quebre funcionalidades existentes de `mapa.html` (perfil/enlace, interações já implementadas).
- Se necessário, crie testes simples (unitários ou de integração) para verificar:
  - a integridade do JSON gerado para o mapa,
  - a correção da agregação por município,
  - a leitura correta da população >18 a partir da API do IBGE (usando mocks quando for o caso).

=====================================
11. O QUE VOCÊ DEVE ENTREGAR
=====================================

1. Código Python atualizado (backend) para:
   - cálculo da mancha de cobertura,
   - geração de tiles com nível médio em dBµV/m,
   - agregação por município,
   - consulta ao IBGE para população >18 (homens e mulheres),
   - estruturação dos dados para o relatório.
2. Ajustes em `mapa.html` para exibir a nova lógica (tiles/escala, se necessário).
3. Backend + frontend para `relatorio.html`, permitindo edição de um relatório completo.
4. Rota e template para geração do PDF profissional a partir do relatório.
5. Pequena documentação em texto (README ou seção de docs) explicando:
   - fluxo completo,
   - endpoints principais,
   - onde estão as funções críticas do cálculo e da integração IBGE.

A partir deste contexto e requisitos, analise o código existente, proponha e implemente todas as alterações necessárias para que o sistema funcione de ponta a ponta conforme descrito.
