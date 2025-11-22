

# **Relatório Técnico Exaustivo: Arquitetura, Engenharia e Regulação do Ecossistema Spectrum-E na Gestão do Espectro da Anatel**

## **1\. Introdução e Definição do Escopo**

A gestão do espectro eletromagnético, um recurso natural finito e estratégico, exige ferramentas de alta precisão que integrem engenharia de radiofrequência, sistemas de informação geográfica (GIS) e complexos arcabouços regulatórios. Este relatório técnico tem como objetivo fornecer uma análise exaustiva sobre a plataforma de software identificada na consulta inicial como "Spectron \-E", cuja denominação correta e técnica é **Spectrum-E**. Este sistema constitui a espinha dorsal tecnológica da Agência Nacional de Telecomunicações (Anatel) no Brasil, materializada publicamente através do sistema **Mosaico**.  
A confusão terminológica inicial — onde o termo "Spectron" pode ser associado a componentes automotivos, kits eletrônicos da década de 1980 ou plugins de áudio — deve ser imediatamente dissipada.1 No contexto da engenharia de telecomunicações e da regulação federal brasileira, estamos tratando exclusivamente do **Spectrum-E**, uma solução *web-based* de gestão de espectro desenvolvida pela **Spectrum Center** (anteriormente ligada à ATDI).  
Este documento destina-se a engenheiros de telecomunicações, reguladores, consultores jurídicos e gestores de rede que necessitam de uma compreensão profunda não apenas de "como operar" o software, mas da lógica algorítmica, legal e física que rege suas operações. A análise abrange desde a cisão corporativa que deu origem à desenvolvedora atual, passa pelos modelos matemáticos de propagação recomendados pela União Internacional de Telecomunicações (UIT), e culmina em um guia operacional detalhado para o licenciamento de estações no Brasil.  
---

## **2\. A Identidade Corporativa e a Evolução do Desenvolvedor**

Para compreender a filosofia de design do Spectrum-E, é imperativo analisar sua genealogia corporativa. O software não é um produto estático, mas o resultado de décadas de evolução na engenharia de espectro, marcado por uma reestruturação corporativa significativa que redefiniu seu suporte e desenvolvimento.

### **2.1. De ATDI para Spectrum Center: A Cisão Estratégica**

Historicamente, o mercado de software de gestão de espectro foi dominado por poucas entidades globais, sendo a ATDI (*Advanced Topographic Development & Images*) uma das mais proeminentes, conhecida por produtos como o ICS Telecom. Durante muitos anos, a Anatel utilizou ferramentas associadas a este ecossistema. No entanto, a ferramenta atual, Spectrum-E, é o produto insígnia da **Spectrum Center**.  
A Spectrum Center surgiu da unificação e subsequente independência das operações da ATDI nos Estados Unidos, Reino Unido e Brasil. Esta nova entidade, separada da matriz francesa original, estabeleceu-se como uma empresa independente, focada especificamente em serviços governamentais e soluções baseadas na nuvem.4

#### **Estrutura da Spectrum Center**

A Spectrum Center, LLC, opera sob uma classificação de "Woman-owned Small Business" (WOSB) nos Estados Unidos, detendo contratos significativos com o governo norte-americano (GSA Professional Services Schedule).4 Esta distinção é crucial pois sinaliza um foco em requisitos de segurança e conformidade governamental, características herdadas pela implementação na Anatel. A presença da **Spectrum Center Brasil** em Brasília (Setor SCN) 6 garante que o desenvolvimento do software não seja apenas uma tradução de uma ferramenta estrangeira, mas uma adaptação profunda às idiossincrasias do regulamento brasileiro.  
A transição de identidade é evidenciada nos manuais e interfaces: onde antigamente se viam referências à ATDI, hoje a documentação técnica e os portais de acesso (como o Mosaico) são sustentados pela tecnologia e suporte da Spectrum Center.7 O software Spectrum-E representa, portanto, uma ruptura com os modelos de licenciamento "desktop" tradicionais (como o Spectrum XXI ou versões antigas do HTZ Warfare), abraçando uma arquitetura puramente SaaS (*Software as a Service*).

### **2.2. A Arquitetura SaaS e o Modelo "Mosaico"**

A decisão da Anatel de adotar o Spectrum-E foi impulsionada pela necessidade de migrar de sistemas fragmentados e locais para uma plataforma unificada e acessível via web. Diferente de softwares de engenharia que exigem *dongles* de hardware (hardkeys) e estações de trabalho de alto desempenho local, o Spectrum-E processa cálculos complexos de propagação em servidores remotos (nuvem ou servidores da Agência).  
Esta arquitetura permitiu a criação do **Mosaico**, que é, em essência, uma implementação "White Label" (marca branca) e customizada do Spectrum-E para o regulador brasileiro.9 O Mosaico substituiu sistemas legados como o STEL (Sistema de Telecomunicações) e o SITARWEB, centralizando o banco de dados técnico e permitindo que milhares de usuários externos (provedores, emissoras de TV, radioamadores) submetam projetos simultaneamente sem a necessidade de adquirir licenças de software proprietário dispendiosas.11  
---

## **3\. O Motor de Cálculos: Fundamentos Matemáticos e Modelagem de Propagação**

O coração do Spectrum-E é o seu motor de cálculos eletromagnéticos. A precisão do licenciamento depende inteiramente da fidelidade com que este motor simula o comportamento das ondas de rádio no mundo real. O software implementa uma biblioteca rigorosa de Recomendações da UIT (ITU-R), permitindo análises determinísticas e empíricas.  
A compreensão destes modelos é vital para o engenheiro: saber qual modelo o software está utilizando explica por que uma licença é deferida ou negada com base em critérios de cobertura ou interferência.

### **3.1. Modelos de Propagação Terrestre e Difração**

O Spectrum-E não utiliza uma fórmula única. Ele seleciona o algoritmo com base na frequência, distância e tipo de serviço.

#### **3.1.1. Recomendação ITU-R P.525 (Espaço Livre)**

O ponto de partida para qualquer análise é a perda no espaço livre (*Free Space Path Loss* \- FSPL). O Spectrum-E utiliza este modelo como linha de base para cálculos de linha de visada (LOS). A equação fundamental implementada é:

$$L\_{bf} \= 32,4 \+ 20 \\log\_{10}(f) \+ 20 \\log\_{10}(d)$$  
Onde $f$ é a frequência em MHz e $d$ é a distância em quilômetros.6 Embora simples, este modelo é crítico para a validação inicial de enlaces de micro-ondas curtos e desobstruídos.

#### **3.1.2. Recomendação ITU-R P.526 e o Método de Bullington**

Para terrenos obstruídos, o software precisa calcular a perda adicional por difração. O Spectrum-E implementa a recomendação P.526, utilizando frequentemente o método de **Bullington**.  
Este método simplifica a complexidade de múltiplos obstáculos (vários picos de montanhas entre transmissor e receptor) substituindo-os por um único obstáculo equivalente "fio de navalha" (*knife-edge*). O ponto de interseção das linhas de visada do transmissor e do receptor define o pico deste obstáculo virtual. O software calcula o parâmetro de difração $\\nu$ (nu) de Fresnel-Kirchhoff para determinar a atenuação adicional em decibéis.6

#### **3.1.3. A Especificidade Brasileira: O Modelo Deygout-Assis**

Um *insight* técnico de segunda ordem, fundamental para quem opera no Brasil, é a implementação do modelo **Deygout-Assis**. Diferente do Bullington padrão, o método de Deygout avalia individualmente os gumes principais e secundários. A variante "Assis", desenvolvida pelo engenheiro brasileiro Mauro S. Assis e incorporada às normas da Anatel, refina o tratamento estatístico das obstruções para o relevo brasileiro.12

* **Aplicação Obrigatória:** O módulo "SCR Radiodifusão" do Spectrum-E, usado para o planejamento de TV Digital e FM no Brasil, é configurado para priorizar ou exigir o uso do Deygout-Assis. Engenheiros que tentam replicar os resultados da Anatel usando outros softwares (como o Radio Mobile gratuito) frequentemente encontram divergências porque não utilizam este algoritmo específico.12

### **3.2. Modelos Estatísticos e de Interferência**

Para serviços móveis e análises de interferência, o determinismo puro é insuficiente devido às variações temporais da atmosfera.

#### **3.2.1. ITU-R P.1812 (Ponto-Área)**

Para serviços terrestres em VHF e UHF (como LTE privado, 4G, 5G em bandas baixas), o Spectrum-E utiliza a ITU-R P.1812.6 Este é um método de predição de caminho específico que considera não apenas o perfil do terreno, mas estatísticas de localização (porcentagem de locais) e tempo (porcentagem de tempo).

* **Relevância:** É o modelo usado para determinar a "mancha de cobertura" e as zonas de interferência em borda de célula. Ele leva em conta efeitos de espalhamento troposférico e dutos anômalos que podem causar interferência a centenas de quilômetros de distância.

#### **3.2.2. ITU-R P.452 (Interferência e Espalhamento)**

Para avaliar a coexistência entre estações (por exemplo, uma estação 5G e uma estação de recepção de satélite TVRO), o software emprega a ITU-R P.452. Este modelo é especializado em calcular a perda de transmissão para situações de interferência, focando em mecanismos de propagação de "céu claro" e espalhamento hidrometeorológico (chuva).6

#### **3.2.3. ITU-R P.530 (Enlaces Ponto-a-Ponto)**

No módulo de licenciamento de enlaces de rádio (backhaul), o Spectrum-E aplica a ITU-R P.530. O foco aqui não é apenas a perda média, mas a probabilidade de desvanecimento (*fading*). O software calcula a **indisponibilidade** do enlace baseada na intensidade de chuva da região (tabelas ITU-R P.837 integradas) e na ocorrência de multipath, garantindo que o projeto atenda aos requisitos de "cinco noves" (99,999%) de confiabilidade.6

### **3.3. Geo-Processamento e Dados Cartográficos (GIS)**

Nenhum modelo matemático funciona sem dados precisos do terreno. O Spectrum-E integra um motor GIS avançado.

* **MDT e MDS:** O sistema diferencia o Modelo Digital de Terreno (solo nu) do Modelo Digital de Superfície (que inclui vegetação e prédios). Para frequências acima de 1 GHz, o uso do MDS é crítico.  
* **Resolução:** O "Worldwide Project Builder" do Spectrum-E permite baixar dados globais SRTM (\~30 metros). No entanto, suporta resoluções de até 1 metro (Lidar) para projetos urbanos densos (Small Cells).6  
* **Clutter:** O software utiliza bases de dados de *clutter* (uso do solo) para aplicar atenuações adicionais baseadas no ambiente (Urbano Denso, Suburbano, Floresta, Água).

---

## **4\. O Arcabouço Regulatório: A Lógica de Negócios (BRE) e os Atos da Anatel**

O diferencial do Spectrum-E em relação a uma ferramenta de engenharia genérica é a sua integração com o arcabouço legal. O sistema possui um **Business Rule Engine (BRE)** — Motor de Regras de Negócios — que contém mais de 300 regras pré-programadas baseadas nos regulamentos da Anatel.14 O software atua como um "fiscal digital", impedindo a submissão de projetos que violem a lei.

### **4.1. Ato nº 11.20 e Ato nº 915: Canalização e Compatibilidade**

Os requisitos técnicos de canalização e os limites de emissão são definidos por atos como o Ato nº 915 (atualizado em 2024\) e o Ato nº 1120 (Compatibilidade Eletromagnética).15

#### **Tabela de Implementação Regulatória no Software**

| Norma Anatel | Função no Spectrum-E/Mosaico | Parâmetro Controlado |
| :---- | :---- | :---- |
| **Ato nº 915/2024** | Define o "Grid" de Frequências | O sistema bloqueia a escolha de frequências centrais que não estejam na tabela oficial de canalização. Impõe o espaçamento correto (ex: 28 MHz, 56 MHz). |
| **Ato nº 1120/2018** | Limites de Espúrios e EMC | Verifica se o equipamento selecionado possui certificação que atenda aos limites de emissão fora da faixa e emissão de espúrios. |
| **Resolução nº 719** | Regulamento Geral de Licenciamento | Define as etapas do fluxo de trabalho (Workflow) no e-Licensing, exigindo responsável técnico (ART) e documentos legais. |
| **Ato nº 458** | Exposição a Campos (EMF) | O software calcula, baseado na E.I.R.P., a distância de conformidade para exposição humana. Se a estação estiver em área densa com potência alta, o sistema sinaliza a necessidade de laudo radiométrico.18 |

### **4.2. Ato nº 14.448: Radiação Restrita e Dispensa de Licenciamento**

Equipamentos de Radiação Restrita (como Wi-Fi, rádios de espalhamento espectral em 2.4 GHz e 5.8 GHz) operam sob o Ato nº 14.448.20

* **Tratamento no Mosaico:** Embora muitos desses equipamentos sejam "dispensados de licenciamento", a Anatel exige o cadastro no banco de dados para fins de controle de interferência. O Spectrum-E possui um módulo simplificado para isso. O software verifica se a potência e a densidade espectral de potência informadas estão abaixo dos limiares estabelecidos no Ato (ex: limites específicos para DSSS ou OFDM). Se o usuário tentar cadastrar um rádio com potência superior ao permitido para a classe "Radiação Restrita", o BRE bloqueia o cadastro simplificado e força o usuário para o fluxo de licenciamento completo (SLP).21

### **4.3. Certificação e Homologação (SGCH)**

O Spectrum-E é integrado ao banco de dados do Sistema de Gestão de Certificação e Homologação (SGCH). Ao selecionar um transmissor ou antena, o usuário deve escolher a partir de uma lista de equipamentos homologados. Se o equipamento não tiver um Certificado de Homologação válido (ou se estiver suspenso), o BRE impede a continuidade do processo. Isso garante que apenas hardware validado tecnicamente (testado conforme Ato nº 6506\) entre em operação na rede nacional.23  
---

## **5\. Ecossistema Mosaico: O Portal da Anatel**

O sistema **Mosaico** é a interface pública do Spectrum-E. Ele representa a modernização da gestão do espectro no Brasil, permitindo autoatendimento.

### **5.1. Módulos do Sistema Mosaico**

O portal é dividido em funcionalidades específicas que atendem a diferentes perfis de outorgados 11:

1. **Licenciamento de Estações (e-Licensing):** Para cadastro permanente de estações de serviços como SCM, SLP, STFC e SMP.  
2. **Uso Temporário de Espectro (UTE):** Módulo ágil para eventos (shows, corridas, grandes coberturas jornalísticas). Permite a coordenação de frequências por curtos períodos.25  
3. **Radiodifusão (SCR):** Módulo complexo que gerencia o "Plano Básico" de canais de TV e Rádio. Permite simular a viabilidade de alteração de características técnicas (aumento de potência, mudança de local) verificando a proteção aos canais vizinhos conforme os critérios do Deygout-Assis.6  
4. **SNOA (Sistema de Negociação de Ofertas de Atacado):** Embora focado em negócios, integra-se à base de dados técnica para verificar a infraestrutura disponível (torres, dutos).

### **5.2. Integração com o SEI e Gov.br**

O fluxo de trabalho no Mosaico não é isolado. Ele inicia-se com a autenticação via **Gov.br**, garantindo a identidade do responsável legal ou técnico. Ao final do processo de engenharia no Spectrum-E, o sistema gera automaticamente um processo administrativo no **SEI (Sistema Eletrônico de Informações)**. Todos os documentos técnicos (formulários, ART, laudos) gerados ou anexados no Mosaico são migrados para este processo SEI, criando um registro legal auditável da solicitação.26  
---

## **6\. Guia Operacional Detalhado: Procedimentos e Parâmetros**

Este capítulo serve como um guia prático para engenheiros que necessitam operar o sistema, sintetizando informações dispersas em manuais de usuário e tutoriais.12

### **6.1. Credenciamento e Acesso Inicial**

Antes de qualquer análise técnica, o usuário deve vencer a barreira administrativa.

1. **Cadastro no SEI:** O usuário deve ser um "Usuário Externo" cadastrado no SEI da Anatel.  
2. **Vínculo CNPJ/CPF:** É necessário vincular o CPF do engenheiro ou representante ao CNPJ da empresa operadora. Isso pode ser feito via procuração eletrônica no próprio sistema.  
3. **Acesso:** O login é feito em https://sistemas.anatel.gov.br/se utilizando as credenciais do Gov.br ou chave de acesso específica.28  
4. **Recuperação de Senha:** Caso o usuário esqueça a senha, o link "Esqueci minha senha" envia um token para o e-mail cadastrado no perfil do usuário (User Profile). O sistema exige senhas alfanuméricas de no mínimo 6 caracteres.29

### **6.2. Fluxo de Licenciamento Passo-a-Passo (Exemplo SLP/SCM)**

Para cadastrar uma nova estação de Serviço Limitado Privado ou Comunicação Multimídia:

#### **Passo 1: Seleção do Serviço e Natureza**

No painel ("Dashboard"), o usuário seleciona "Nova Solicitação" ou "Licenciamento de Estações". Deve-se escolher o serviço correto (ex: 045 \- SCM). Erros aqui são fatais para o processo, pois as regras de negócio (BRE) mudam conforme o serviço.26

#### **Passo 2: Definição Geográfica e Técnica**

O formulário web do Spectrum-E exige a entrada dos seguintes dados críticos 30:

* **Identificação da Estação:** Nome, Endereço completo.  
* **Coordenadas (Lat/Long):** Devem ser inseridas em Graus Decimais ou GMS (Graus, Minutos, Segundos). *Atenção:* O sistema valida se a coordenada cai dentro do município declarado. Uma divergência de metros que coloque a estação no município vizinho gera erro de validação.  
* **Frequência de Transmissão e Recepção:** Seleção dos canais de acordo com o Ato nº 915\.  
* **Designação de Emissão:** Código ITU (ex: 11K0F3E para voz FM estreita, 20M0G7W para dados banda larga). Este código define a largura de banda ocupada e é essencial para cálculos de interferência.  
* **Equipamentos:** Seleção do Transmissor e Antena a partir da base de dados homologada.  
  * *Parâmetros de Antena:* Ganho (dBi), Azimute (graus em relação ao Norte Verdadeiro), Tilt Elétrico e Mecânico, Altura do Centro de Radiação (em metros acima do solo \- AGL).

#### **Passo 3: Validação e Submissão**

Ao preencher os dados, o usuário clica no botão "Validar". O BRE executa centenas de verificações:

* A frequência é permitida para este serviço nesta região?  
* A potência (ERP) excede o limite da classe?  
* A antena está homologada?  
* Existe conflito de bloqueio geográfico?

Se houver erros, o sistema exibe uma lista de pendências em vermelho. Somente após a correção (validação "verde") o botão "Salvar/Submeter" fica disponível. Após a submissão, o sistema gera o boleto da Taxa de Fiscalização de Instalação (TFI) e o Preço Público pelo Direito de Uso de Radiofrequência (PPDUR).22

### **6.3. Importação em Lote (Bulk Upload)**

Para grandes redes (ex: centenas de estações VSAT ou links de um provedor regional), o Spectrum-E permite o carregamento em lote via arquivos CSV ou planilhas Excel padronizadas. O layout destas planilhas é estrito; qualquer desvio na formatação das colunas ou nos códigos de dados resulta na rejeição total do arquivo.32  
---

## **7\. Análises Técnicas Avançadas e Cenários Complexos**

O Spectrum-E é capaz de realizar simulações que vão muito além do licenciamento básico, abordando problemas complexos da engenharia moderna.

### **7.1. Análise de Coexistência e Interferência (C/I)**

O módulo de Análise Técnica permite estudos de interferência cocanal e de canal adjacente.

* **Matriz de Interferência:** O sistema calcula a relação C/I (Portadora/Interferência) em cada ponto da área de serviço. Utilizando as curvas de proteção dos receptores (definidas nas normas da ITU e nos Atos da Anatel), o software gera mapas de calor ("Heatmaps") mostrando onde o serviço será degradado por estações vizinhas.6  
* **LTE vs. TV Digital:** Uma aplicação crítica no Brasil foi a limpeza da faixa de 700 MHz. O Spectrum-E foi usado para simular a interferência das estações base LTE (4G) nos receptores de TV domésticos, definindo onde seria necessário instalar filtros de mitigação.33

### **7.2. Impacto de Parques Eólicos**

Com a expansão da energia eólica, o Spectrum-E incorporou funcionalidades para analisar o impacto de turbinas eólicas em sistemas de telecomunicações. As pás das turbinas, muitas vezes feitas de compósitos que refletem ou espalham sinais de RF, podem causar "fantasmas" em radares meteorológicos e bloquear links de micro-ondas. O software modela a turbina como um objeto tridimensional dinâmico, calculando a zona de Fresnel obstruída e o efeito Doppler potencial.6

### **7.3. Integração Satelital e SGP4**

Para a coordenação de estações terrenas, o Spectrum-E integra modelos de mecânica orbital SGP4 (*Simplified General Perturbations*). Isso permite que o sistema calcule a posição exata de satélites não-geoestacionários (NGSO, como Starlink ou O3b) em qualquer momento, verificando a possibilidade de interferência em linha de visada com enlaces terrestres ou outras estações satelitais.6  
---

## **8\. Conclusão e Visão Estratégica**

A implementação do software **Spectrum-E** (via sistema **Mosaico**) representou um salto quântico na maturidade regulatória da Anatel. Ao substituir a análise manual baseada em papel ou softwares desconexos por uma plataforma SaaS integrada, a Agência ganhou em escala, transparência e rigor técnico.  
Para o profissional do setor, o domínio desta ferramenta não é opcional. O Spectrum-E não é apenas uma interface de entrada de dados; é a codificação digital da legislação de espectro. A compreensão dos modelos de propagação subjacentes (como a necessidade do **Deygout-Assis** para radiodifusão ou a **ITU-R P.530** para micro-ondas) e das regras de negócio (BRE) é o que distingue um projeto deferido rapidamente de um processo travado em exigências técnicas.  
À medida que o Brasil avança para a implementação da TV 3.0 e redes 6G, a complexidade das análises de coexistência só aumentará. A capacidade do Spectrum-E de integrar dados de monitoramento em tempo real (TDOA/AOA) e simulações de alta resolução (Lidar/1m) sugere que o futuro da gestão de espectro será dinâmico e automatizado, com o software atuando como o cérebro central deste ecossistema invisível, porém vital.

#### **Referências citadas**

1. Easy to build projects for everyone \- World Radio History, acessado em novembro 21, 2025, [https://www.worldradiohistory.com/UK/Everyday-Electronics/80s/Everyday-Electronics-1981-12.pdf](https://www.worldradiohistory.com/UK/Everyday-Electronics/80s/Everyday-Electronics-1981-12.pdf)  
2. 2019 Fuel Pump PDF \- Scribd, acessado em novembro 21, 2025, [https://www.scribd.com/document/486116316/2019-FUEL-PUMP-pdf](https://www.scribd.com/document/486116316/2019-FUEL-PUMP-pdf)  
3. iZotope Spectron \- Sweetwater, acessado em novembro 21, 2025, [https://www.sweetwater.com/store/detail/Spectron-e--izotope-spectron](https://www.sweetwater.com/store/detail/Spectron-e--izotope-spectron)  
4. Government Services | Spectrum Center, acessado em novembro 21, 2025, [https://public.spectrum.center/se/public/government-services](https://public.spectrum.center/se/public/government-services)  
5. Spectrum Center Launch, acessado em novembro 21, 2025, [https://public.spectrum.center/se/public/spectrum-center-launch](https://public.spectrum.center/se/public/spectrum-center-launch)  
6. Technical Analysis: Propagation Models, Functionalities | Spectrum ..., acessado em novembro 21, 2025, [https://public.spectrum.center/se/public/technical-analysis](https://public.spectrum.center/se/public/technical-analysis)  
7. Introducing Spectrum-E© \- YouTube, acessado em novembro 21, 2025, [https://www.youtube.com/watch?v=s3RrrW0jxmU](https://www.youtube.com/watch?v=s3RrrW0jxmU)  
8. Spectrum Center \- YouTube, acessado em novembro 21, 2025, [https://www.youtube.com/c/SpectrumCenter](https://www.youtube.com/c/SpectrumCenter)  
9. SpectrumAvailability for the Deployment ofTV 3.0 \- SET, acessado em novembro 21, 2025, [https://www.set.org.br/ijbe/ed8/artigo2.pdf](https://www.set.org.br/ijbe/ed8/artigo2.pdf)  
10. DISSERTAÇÃO DE MESTRADO ACADÊMICO SPECTRUM, acessado em novembro 21, 2025, [https://repositorio.unb.br/bitstream/10482/45820/1/2022\_ThiagoAguiarSoares.pdf](https://repositorio.unb.br/bitstream/10482/45820/1/2022_ThiagoAguiarSoares.pdf)  
11. Anatel, acessado em novembro 21, 2025, [https://eventos.telesintese.com.br/wp-content/uploads/2018/03/AfonsoAnatel.pdf](https://eventos.telesintese.com.br/wp-content/uploads/2018/03/AfonsoAnatel.pdf)  
12. Spectrum E User Manual PT | PDF | Rede de computadores \- Scribd, acessado em novembro 21, 2025, [https://pt.scribd.com/document/759014261/Spectrum-E-User-Manual-PT](https://pt.scribd.com/document/759014261/Spectrum-E-User-Manual-PT)  
13. Pricing | Spectrum Center, acessado em novembro 21, 2025, [https://public.spectrum.center/se/public/pricing](https://public.spectrum.center/se/public/pricing)  
14. E-Licensing | Spectrum Center, acessado em novembro 21, 2025, [https://public.spectrum.center/se/public/e-licensing](https://public.spectrum.center/se/public/e-licensing)  
15. Ato nº 1120, de 19 de fevereiro de 2018 \- Agência Nacional de Telecomunicações, acessado em novembro 21, 2025, [https://www.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2018/1181-ato-1120](https://www.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2018/1181-ato-1120)  
16. Ato nº 915, de 01 de fevereiro de 2024 \- Anatel, acessado em novembro 21, 2025, [https://informacoes.anatel.gov.br/legislacao/atos-de-requisitos-tecnicos-de-gestao-do-espectro/2024/1920-ato-915](https://informacoes.anatel.gov.br/legislacao/atos-de-requisitos-tecnicos-de-gestao-do-espectro/2024/1920-ato-915)  
17. AGÊNCIA NACIONAL DE TELECOMUNICAÇÕES ATO Nº 915, DE 01 DE FEVEREIRO DE 2024 O SUPERINTENDENTE DE OUTORGA E RECURSOS À PREST \- Utcal, acessado em novembro 21, 2025, [https://www.utcal.com.br/repositorio/Recursos-Tecnicos/documentos/Atos/ATO-915.pdf](https://www.utcal.com.br/repositorio/Recursos-Tecnicos/documentos/Atos/ATO-915.pdf)  
18. Ato nº 458, de 24 de janeiro de 2019 (REVOGADO) \- Anatel, acessado em novembro 21, 2025, [https://www.anatel.gov.br/legislacao/atos-de-requisitos-tecnicos-de-gestao-do-espectro/2019/1237-ato-458](https://www.anatel.gov.br/legislacao/atos-de-requisitos-tecnicos-de-gestao-do-espectro/2019/1237-ato-458)  
19. Anatel abre consulta para novas recomendações a limites de exposição a campos eletromagnéticos \- TELETIME News, acessado em novembro 21, 2025, [https://teletime.com.br/06/10/2022/anatel-abre-consulta-para-novas-recomendacoes-a-limites-de-exposicao-a-campos-eletromagneticos/](https://teletime.com.br/06/10/2022/anatel-abre-consulta-para-novas-recomendacoes-a-limites-de-exposicao-a-campos-eletromagneticos/)  
20. Ato nº 14448, de 04 de dezembro de 2017 \- Anatel, acessado em novembro 21, 2025, [https://informacoes.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2017/1139-ato-14448](https://informacoes.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2017/1139-ato-14448)  
21. equipamentos de radiação restrita: características e limites normativos de \- ABES, acessado em novembro 21, 2025, [https://abes-dn.org.br/anaiseletronicos/32cbesa/443\_tema\_xi.pdf](https://abes-dn.org.br/anaiseletronicos/32cbesa/443_tema_xi.pdf)  
22. Cadastramento de Estação Anatel SCM via Mosaico (radiação restrita STEL) Dispensa de Licenciamento | Canal Gilson Telecom, acessado em novembro 21, 2025, [https://canal.gilsontele.com/videos/cadastramento-de-estacao-anatel-scm-via-mosaico-radiacao-restrita-stel-dispensa-de-licenciamento/](https://canal.gilsontele.com/videos/cadastramento-de-estacao-anatel-scm-via-mosaico-radiacao-restrita-stel-dispensa-de-licenciamento/)  
23. Ato nº 6506, de 27 de agosto de 2018 (REVOGADO) \- Anatel, acessado em novembro 21, 2025, [https://www.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2018/1205-ato-6506](https://www.anatel.gov.br/legislacao/atos-de-certificacao-de-produtos/2018/1205-ato-6506)  
24. Anatel \- Resoluções \- Agência Nacional de Telecomunicações, acessado em novembro 21, 2025, [https://www.anatel.gov.br/legislacao/resolucoes?catid=0\&id=95](https://www.anatel.gov.br/legislacao/resolucoes?catid=0&id=95)  
25. ATDI to Deliver Spectrum Management Solutions for World Games \- PR Newswire, acessado em novembro 21, 2025, [https://www.prnewswire.com/news-releases/atdi-to-deliver-spectrum-management-solutions-for-world-games-198767621.html](https://www.prnewswire.com/news-releases/atdi-to-deliver-spectrum-management-solutions-for-world-games-198767621.html)  
26. sistema mosaico \- Agência Nacional de Telecomunicações, acessado em novembro 21, 2025, [https://www.anatel.gov.br/Portal/verificaDocumentos/documento.asp?numeroPublicacao=343193\&pub=original\&filtro=1\&documentoPath=343193.pdf](https://www.anatel.gov.br/Portal/verificaDocumentos/documento.asp?numeroPublicacao=343193&pub=original&filtro=1&documentoPath=343193.pdf)  
27. Manual ANATEL: Coleta de Dados TV Assinatura | PDF | Rede de computadores \- Scribd, acessado em novembro 21, 2025, [https://pt.scribd.com/document/653467654/SEAC-Manual-Coleta-Acessos-TVpA](https://pt.scribd.com/document/653467654/SEAC-Manual-Coleta-Acessos-TVpA)  
28. Manual-Licenciamento-Mosaico 2022-05-17 v3 \- 1 | PDF | Antena (rádio) \- Scribd, acessado em novembro 21, 2025, [https://pt.scribd.com/document/652441377/Manual-Licenciamento-Mosaico-2022-05-17-v3-1](https://pt.scribd.com/document/652441377/Manual-Licenciamento-Mosaico-2022-05-17-v3-1)  
29. Spectrum-E© e-Licensing Module, acessado em novembro 21, 2025, [https://www.trc.vg/wp-content/uploads/2021/05/TRC\_Spectrum-E\_e\_Licensing\_TypeApproval\_UserManual\_v0.1\_ENG.pdf](https://www.trc.vg/wp-content/uploads/2021/05/TRC_Spectrum-E_e_Licensing_TypeApproval_UserManual_v0.1_ENG.pdf)  
30. External User Registration Sending a request for access \- NTRC Dominica, acessado em novembro 21, 2025, [https://ntrcdominica.dm/wp-content/uploads/2024/09/DRAFT-Spectrum-E-Amateur-Radio-Application-System-Guide.pdf](https://ntrcdominica.dm/wp-content/uploads/2024/09/DRAFT-Spectrum-E-Amateur-Radio-Application-System-Guide.pdf)  
31. SIP Trunking Configuration Guide for Microsoft Teams Direct Routing Using Ribbon SBC 2000 \- Spectrum Enterprise, acessado em novembro 21, 2025, [https://enterprise.spectrum.com/content/dam/spectrum/enterprise/en/pdfs/services/voip/sip/Spectrum%20Enterprise%20SIP%20trunks%20with%20Ribbon2KV8.0.3\_MicrosoftTeams\_Configuration%20Guide%20v1.2.pdf](https://enterprise.spectrum.com/content/dam/spectrum/enterprise/en/pdfs/services/voip/sip/Spectrum%20Enterprise%20SIP%20trunks%20with%20Ribbon2KV8.0.3_MicrosoftTeams_Configuration%20Guide%20v1.2.pdf)  
32. Manual Licenciamento Mosaico em Bloco v1 | PDF | Informática, acessado em novembro 21, 2025, [https://www.scribd.com/document/859642369/manual-Licenciamento-Mosaico-em-Bloco-v1](https://www.scribd.com/document/859642369/manual-Licenciamento-Mosaico-em-Bloco-v1)  
33. BIF Response to TRAI CP on Auction of Spectrum in frequency bands identified for IMT/5G Preamble \- Telecom Regulatory Authority of India, acessado em novembro 21, 2025, [https://www.trai.gov.in/sites/default/files/2024-11/BIF\_11012022.pdf](https://www.trai.gov.in/sites/default/files/2024-11/BIF_11012022.pdf)