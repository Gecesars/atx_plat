import React, { useState, useMemo } from 'react';

// --- Ícones SVG Inline (para garantir renderização sem dependências) ---

const MenuIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-6 w-6"
  >
    <line x1="3" y1="12" x2="21" y2="12"></line>
    <line x1="3" y1="6" x2="21" y2="6"></line>
    <line x1="3" y1="18" x2="21" y2="18"></line>
  </svg>
);

const XIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-6 w-6"
  >
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const CheckCircleIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5 mr-2 text-blue-500"
  >
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);

const AlertTriangleIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5 mr-2 text-yellow-500"
  >
    <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

const BookOpenIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-4 w-4 mr-2"
  >
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
  </svg>
);

// --- Tipos TypeScript ---
type SectionId =
  | 'intro'
  | 'part1'
  | 'part2'
  | 'part3'
  | 'part4'
  | 'part5'
  | 'part6'
  | 'part7'
  | 'conclusion';

interface NavItem {
  id: SectionId;
  title: string;
  subtitle: string;
}

// --- Componente de Bloco de Código (para exemplos) ---
const CodeBlock: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <pre className="bg-gray-800 text-white p-4 rounded-lg overflow-x-auto text-sm my-4">
    <code>{children}</code>
  </pre>
);

// --- Componente de Alerta/Nota ---
const InfoBox: React.FC<{
  children: React.ReactNode;
  type: 'info' | 'warning';
}> = ({ children, type }) => {
  const isWarning = type === 'warning';
  return (
    <div
      className={`flex items-start p-4 my-4 rounded-lg ${
        isWarning
          ? 'bg-yellow-50 border-yellow-300'
          : 'bg-blue-50 border-blue-300'
      } border-l-4`}
    >
      {isWarning ? <AlertTriangleIcon /> : <CheckCircleIcon />}
      <div className="ml-3 text-sm text-gray-700">{children}</div>
    </div>
  );
};

// --- Componente Visualizador de Conector (da nossa criação anterior) ---
interface ConnectorVisualProps {
  colors: string[];
  segments: number;
  arrayId: string;
}

const ConnectorVisual: React.FC<ConnectorVisualProps> = ({
  colors,
  segments,
  arrayId,
}) => {
  const segmentAngle = 360 / segments;
  const segmentPaths = useMemo(() => {
    const paths: string[] = [];
    const largeRadius = 45;
    const smallRadius = 25;
    const gap = segments > 1 ? 2 : 0; // Ângulo de folga

    for (let i = 0; i < segments; i++) {
      const startAngle = i * segmentAngle;
      const endAngle = (i + 1) * segmentAngle - gap;

      const startAngleRad = (startAngle - 90) * (Math.PI / 180);
      const endAngleRad = (endAngle - 90) * (Math.PI / 180);

      const x1 = 50 + largeRadius * Math.cos(startAngleRad);
      const y1 = 50 + largeRadius * Math.sin(startAngleRad);
      const x2 = 50 + largeRadius * Math.cos(endAngleRad);
      const y2 = 50 + largeRadius * Math.sin(endAngleRad);

      const x3 = 50 + smallRadius * Math.cos(endAngleRad);
      const y3 = 50 + smallRadius * Math.sin(endAngleRad);
      const x4 = 50 + smallRadius * Math.cos(startAngleRad);
      const y4 = 50 + smallRadius * Math.sin(startAngleRad);

      const largeArc = segmentAngle - gap > 180 ? 1 : 0;

      const d = [
        `M ${x1} ${y1}`, // Mover para o ponto externo inicial
        `A ${largeRadius} ${largeRadius} 0 ${largeArc} 1 ${x2} ${y2}`, // Arco externo
        `L ${x3} ${y3}`, // Linha para o ponto interno final
        `A ${smallRadius} ${smallRadius} 0 ${largeArc} 0 ${x4} ${y4}`, // Arco interno
        'Z', // Fechar o caminho
      ].join(' ');
      paths.push(d);
    }
    return paths;
  }, [segments, segmentAngle]);

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <svg viewBox="0 0 100 100" className="w-24 h-24">
        {/* Camada de fundo (cinza) */}
        <circle cx="50" cy="50" r="45" fill="#e0e0e0" />
        {/* Segmentos de cor */}
        {segmentPaths.map((d, i) => (
          <path
            key={i}
            d={d}
            fill={colors[i % colors.length]}
            stroke="#fff"
            strokeWidth="0.5"
          />
        ))}
        {/* Círculo central (metal) */}
        <circle cx="50" cy="50" r="23" fill="#f0f0f0" />
        <circle cx="50" cy="50" r="20" fill="#d0d0d0" stroke="#b0b0b0" strokeWidth="1" />
        {/* Pino central */}
        <circle cx="50" cy="50" r="5" fill="#f0f0f0" stroke="#b0b0b0" strokeWidth="1" />
      </svg>
      <span className="mt-2 text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
        {arrayId}
      </span>
    </div>
  );
};

// --- Seções do Tutorial como Componentes ---

const SectionWrapper: React.FC<{
  title: string;
  children: React.ReactNode;
}> = ({ title, children }) => (
  <article className="prose prose-lg max-w-none prose-blue">
    <h1 className="text-3xl font-bold text-gray-800 border-b-2 border-blue-500 pb-2">
      {title}
    </h1>
    {children}
  </article>
);

const Introduction: React.FC = () => (
  <SectionWrapper title="Introdução: O que é AISG e por que ele é crucial?">
    <p className="text-xl leading-relaxed text-gray-600">
      A <strong>eftx broadcast & Telecom</strong>, sua parceira estratégica em
      infraestrutura de telecomunicações, apresenta este guia definitivo.
      Vamos desmistificar o ecossistema que silenciosamente revolucionou a forma
      como as redes móveis são gerenciadas.
    </p>
    <p>
      O <strong>AISG (Antenna Interface Standards Group)</strong> é um consórcio
      global que foi estabelecido para resolver um problema caótico e caro: a
      total falta de padronização no controlo de dispositivos instalados no topo
      da torre (como antenas e amplificadores).
    </p>
    <p>
      Em termos simples, o AISG é o "idioma" universal, o "cabeamento"
      padronizado e a "etiqueta" visual que permitem que uma Estação Rádio Base
      (BTS) controle remotamente os dispositivos na sua linha de antena (ALDs -
      Antenna Line Devices).
    </p>

    <h3>O Problema Histórico: "Vendor Lock-In"</h3>
    <p>
      Antes do AISG, cada fabricante (ex: Ericsson, Nokia) tinha o seu próprio
      sistema proprietário. Se uma operadora usava uma BTS da Nokia, ela só podia
      usar antenas e amplificadores (TMAs) compatíveis com o controlo da Nokia.
      Isto criava um "aprisionamento tecnológico", eliminava a competição e
      aumentava os custos.
    </p>
    <InfoBox type="warning">
      <strong>Exemplo de Custo (Pré-AISG):</strong> Uma operadora precisava
      trocar um amplificador (TMA) de um concorrente, mas era forçada a usar o da
      mesma marca da BTS, que era 30% mais caro, simplesmente por uma
      incompatibilidade de controlo.
    </InfoBox>

    <h3>Os Três Pilares do Valor do AISG</h3>
    <p>
      A importância do AISG hoje, um padrão que a <strong>eftx</strong> domina e
      implementa diariamente, assenta em três pilares:
    </p>
    <ol>
      <li>
        <strong>Interoperabilidade (Redução de CAPEX):</strong> O pilar fundador.
        Permite que uma operadora construa um site usando uma BTS da Ericsson, um
        TMA da RFS e uma antena da Commscope. Todos comunicam através do mesmo
        cabo. Isso fomenta a competição e reduz o custo de aquisição de
        equipamentos (CAPEX).
      </li>
      <li>
        <strong>Otimização Remota (Redução de OPEX):</strong> A vantagem
        operacional. Permite que engenheiros de RF, a partir do NOC, ajustem
        parâmetros vitais da rede.
        <br />
        <strong>Exemplo:</strong> Um engenheiro nota interferência entre a Célula
        A e B. Ele envia um comando AISG e ajusta o tilt da Célula A de 2 para 4
        graus. Em 30 segundos, o problema é mitigado. Sem o AISG, isso exigiria
        uma visita de técnicos à torre, custando milhares de euros e levando
        dias.
      </li>
      <li>
        <strong>Redução de Erros de Instalação (Qualidade):</strong> O padrão de
        cores AISG-APC é uma "etiqueta" visual.
        <br />
        <strong>Exemplo:</strong> Um técnico no topo da torre liga o cabo da
        "Banda Baixa" na porta com o anel <strong>VERMELHO</strong>, e o da
        "Banda Média" na porta <strong>AZUL</strong>. A chance de uma ligação
        cruzada (cross-connection) que derrubaria a performance do site cai
        para perto de zero.
      </li>
    </ol>
  </SectionWrapper>
);

const Part1Tilt: React.FC = () => (
  <SectionWrapper title='Parte 1: O "Tilt" e a Otimização da Cobertura de RF'>
    <p>
      O "Tilt" (inclinação) é o ajuste do ângulo vertical do feixe de
      transmissão da antena. É a ferramenta mais poderosa de um engenheiro de RF
      para controlar a cobertura e gerir a interferência.
    </p>
    <ul>
      <li>
        <strong>Aumentar o Tilt (apontar para baixo):</strong> "Encolhe" a
        célula. Usado para focar capacidade (ex: estádios) ou reduzir
        interferência em células vizinhas.
      </li>
      <li>
        <strong>Diminuir o Tilt (apontar para o horizonte):</strong> "Estica" a
        célula. Usado para cobertura rural (range).
      </li>
    </ul>

    <h3>Tilt Fixo (Mecânico vs. Elétrico Fixo)</h3>
    <p>
      Este é o método antigo, manual. O <strong>Tilt Mecânico</strong> inclina
      toda a estrutura física da antena, o que distorce o feixe de RF. O{' '}
      <strong>Tilt Elétrico Fixo (FET)</strong> é ajustado de fábrica e preserva
      o feixe, mas é fixo.
    </p>
    <InfoBox type="warning">
      <strong>O Problema do Tilt Fixo:</strong> Para alterar o tilt de 4 para 6
      graus, um técnico precisa subir na torre (no caso mecânico) ou a antena
      precisa ser inteiramente trocada (no caso FET). Ambos são caros e lentos.
    </InfoBox>

    <h3>Tilt Dinâmico (RET) - Onde o AISG Brilha</h3>
    <p>
      É aqui que a magia acontece. O <strong>RET (Remote Electrical Tilt)</strong>{' '}
      é a funcionalidade central do AISG.
    </p>
    <ul>
      <li>
        <strong>Como funciona:</strong> Dentro da antena existe uma
        "subunidade" RET - um pequeno motor de precisão ligado ao sistema de
        fases da antena.
      </li>
      <li>
        <strong>O Papel do AISG:</strong> O padrão AISG define como a BTS envia
        comandos para esse motor. O cabo AISG leva energia (10-30V DC) e os
        dados de controlo (via RS-485).
      </li>
    </ul>
    <p>
      O engenheiro pode enviar um comando e ajustar o tilt de 0 a 12 graus em
      incrementos de 0.1 grau, remotamente, permitindo otimizações de rede em
      tempo real.
    </p>
    <CodeBlock>
      {`// Exemplo de comando lógico enviado pela BTS:
{
  "targetDevice": "RET_Banda_Baixa_ID_3",
  "command": "SET_TILT",
  "value": 6.5,
  "unit": "degrees"
}
// O RET executa e responde:
{
  "device": "RET_Banda_Baixa_ID_3",
  "status": "SUCCESS",
  "currentTilt": 6.5
}`}
    </CodeBlock>
  </SectionWrapper>
);

const Part2PhysicalLayer: React.FC = () => (
  <SectionWrapper title="Parte 2: A Camada Física - Protocolo, Cabos e Conectores">
    <p>
      Para o AISG funcionar, ele precisa de uma conexão física robusta, capaz de
      sobreviver décadas no ambiente hostil do topo de uma torre.
    </p>

    <h3>O Conector: M16 / C485</h3>
    <p>
      O padrão especifica o conector **M16 circular de 8 pinos** (IEC 60130-9).
      Ele possui uma rosca de travamento que garante resistência à vibração e
      estanqueidade (IP67/IP68). O padrão C485 posterior apenas define
      tolerâncias mecânicas mais rigorosas para garantir a interoperabilidade
      entre marcas.
    </p>

    <h3>Pinagem do Conector AISG (Macho/Fêmea de 8 Pinos)</h3>
    <p>
      A pinagem é o coração da interoperabilidade. A <strong>eftx</strong>{' '}
      utiliza e fornece cabos que seguem estritamente esta norma:
    </p>
    <div className="overflow-x-auto">
      <table className="w-full text-left table-auto">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-2">Pino</th>
            <th className="px-4 py-2">Função Primária (v2.0 / v3.0)</th>
            <th className="px-4 py-2">Explicação da Função</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border px-4 py-2">**1**</td>
            <td className="border px-4 py-2">+12V DC (Opcional)</td>
            <td className="border px-4 py-2">Alimentação opcional (raramente usada)</td>
          </tr>
          <tr>
            <td className="border px-4 py-2">**3**</td>
            <td className="border px-4 py-2">**RS-485 B**</td>
            <td className="border px-4 py-2">Linha "B" (negativa) do par de dados</td>
          </tr>
          <tr>
            <td className="border px-4 py-2">**5**</td>
            <td className="border px-4 py-2">**RS-485 A**</td>
            <td className="border px-4 py-2">Linha "A" (positiva) do par de dados</td>
          </tr>
          <tr>
            <td className="border px-4 py-2">**6**</td>
            <td className="border px-4 py-2">**Alimentação 10-30V DC (Principal)**</td>
            <td className="border px-4 py-2">Alimentação DC principal para os ALDs</td>
          </tr>
          <tr>
            <td className="border px-4 py-2">**7**</td>
            <td className="border px-4 py-2">**Retorno DC (Terra)**</td>
            <td className="border px-4 py-2">O retorno (GND) para a alimentação DC</td>
          </tr>
        </tbody>
      </table>
    </div>
    <InfoBox type="info">
      <strong>Par Trançado é Chave:</strong> Os dados fluem pelos Pinos 3 e 5,
      que formam um par trançado. Isso é essencial para o RS-485, pois cancela o
      ruído eletromagnético (EMI) no longo cabo da torre, garantindo uma
      comunicação fiável.
    </InfoBox>

    <h3>Protocolo e Métodos de Transmissão (9.6 kbps)</h3>
    <p>
      O AISG envia dados usando o protocolo HDLC a 9.6 kbps. Existem duas formas
      de enviar esse sinal:
    </p>
    <ol>
      <li>
        <strong>Cabo AISG Dedicado:</strong>
        <br />O método padrão. Um cabo AISG separado é passado.
        <br />
        <strong>Vantagem:</strong> Fácil de diagnosticar (plano de controlo e RF
        separados).
        <br />
        <strong>Desvantagem:</strong> Mais um cabo na torre (custo, peso, carga
        de vento).
      </li>
      <li>
        <strong>Modulação no Cabo de RF (Método OOK):</strong>
        <br />O sinal AISG/DC é "injetado" no próprio cabo de RF principal.
        <br />
        <strong>Dispositivo Chave:</strong> O "Bias-T" (Injetor) combina os
        sinais na base e os separa na antena.
        <br />
        <strong>Protocolo:</strong> Usa OOK (On-Off Keying) numa portadora de
        2.176 MHz, que "pega carona" no cabo de RF.
        <br />
        <strong>Exemplo de Uso (OOK):</strong> Numa modernização de um site
        antigo que só tem o cabo de RF grosso, este método é perfeito. A
        <strong>eftx</strong> pode instalar Bias-Ts e uma antena compatível,
        ativando o controlo RET sem a necessidade caríssima de passar um novo
        cabo AISG pela torre.
      </li>
    </ol>
  </SectionWrapper>
);

const Part3ALDs: React.FC = () => (
  <SectionWrapper title="Parte 3: Outros Dispositivos (ALDs) Controlados pelo AISG">
    <p>
      O AISG não serve apenas para o "Tilt" (RET). Ele é um barramento de
      controlo para *qualquer* dispositivo na linha de antena.
    </p>
    <h3>TMA (Tower Mounted Amplifier) / LNA (Low Noise Amplifier)</h3>
    <p>
      É um amplificador instalado no topo da torre, o mais perto possível da
      antena.
    </p>
    <InfoBox type="info">
      <strong>O Problema que o TMA Resolve:</strong> O sinal do seu telemóvel
      (uplink) é muito fraco. Ele perde metade da sua potência (-3 dB) no cabo
      longo da torre. O TMA (Amplificador de Baixo Ruído) amplifica esse sinal
      fraco *antes* que ele desça o cabo, melhorando drasticamente a
      sensibilidade de receção (NF) da BTS.
    </InfoBox>
    <p>
      <strong>Papel do AISG no TMA:</strong>
    </p>
    <ul>
      <li>
        <strong>Controlo de Ganho:</strong> A BTS comanda o ganho do TMA (ex: +12
        dB).
      </li>
      <li>
        <strong>Modo Bypass:</strong> Em caso de falha, a BTS comanda o TMA para se
        desligar e não interromper o serviço.
      </li>
      <li>
        <strong>Monitoramento (Alarmes):</strong> O TMA usa o AISG para reportar
        alarmes críticos como "VSWR Alto" (problema no cabo/antena) ou "Alarme
        de Corrente".
      </li>
    </ul>

    <h3>ALS (Antenna Location and Orientation Sensor)</h3>
    <p>
      Um dispositivo avançado (muitas vezes integrado na antena) com GPS,
      bússola digital e acelerómetros.
    </p>
    <InfoBox type="info">
      <strong>Exemplo Prático (ALS):</strong> Uma operadora é auditada pela
      agência reguladora (ANATEL). A agência questiona se o azimute do Setor 2
      está correto (projeto diz 30 graus). Em vez de enviar uma equipa, o
      engenheiro envia um comando AISG para a subunidade ALS da antena. O ALS
      responde: 'Azimute Atual: 29.8 graus, Inclinação Mecânica: 1.5 graus'. O
      engenheiro anexa este log e prova a conformidade em minutos.
    </InfoBox>
  </SectionWrapper>
);

const Part4ColorCoding: React.FC = () => {
  // Dados para os conectores
  const singleBand = [
    { id: 'R1', colors: ['#D92120'], segments: 1 },
    { id: 'R2', colors: ['#D92120'], segments: 3 },
    { id: 'R3', colors: ['#D92120'], segments: 6 },
    { id: 'R4', colors: ['#D92120'], segments: 12 },
    { id: 'G1', colors: ['#00874F'], segments: 1 },
    { id: 'G2', colors: ['#00874F'], segments: 3 },
    { id: 'B1', colors: ['#0057A7'], segments: 1 },
    { id: 'B2', colors: ['#0057A7'], segments: 3 },
    { id: 'Y1', colors: ['#FECC00'], segments: 1 },
    { id: 'Y2', colors: ['#FECC00'], segments: 3 },
    { id: 'P1', colors: ['#9A4E9E'], segments: 1 },
    { id: 'O1', colors: ['#F58220'], segments: 1 },
  ];

  const duplexed = [
    {
      id: 'R1/B1',
      colors: ['#D92120', '#0057A7'],
      segments: 6,
    },
    {
      id: 'R1/Y1',
      colors: ['#D92120', '#FECC00'],
      segments: 6,
    },
  ];

  const triplexed = [
    {
      id: 'R1/B1/Y1',
      colors: ['#D92120', '#0057A7', '#FECC00'],
      segments: 6,
    },
    {
      id: 'R1/G1/B1',
      colors: ['#D92120', '#00874F', '#0057A7'],
      segments: 6,
    },
  ];

  return (
    <SectionWrapper title="Parte 4: Interpretando a Antena - O Padrão de Cores (AISG-APC)">
      <p>
        Esta é a parte visual do padrão, fundamental para o instalador. A{' '}
        <strong>eftx</strong> enfatiza o treino nesta área para garantir
        instalações com "zero erro".
      </p>
      <InfoBox type="warning">
        <strong>O Problema:</strong> Um instalador liga o cabo da Rádio 1
        (Banda Baixa) na porta da Banda Alta (Y1). É um erro catastrófico que
        causa péssima performance, interferência e exige uma nova e cara subida
        à torre.
      </InfoBox>
      <p>
        A solução é o padrão **AISG-APC (Antenna Port Colour Coding)**, que
        cria uma "cola" visual à prova de falhas.
      </p>

      <h3>1. Decodificando as Cores (Bandas de Frequência)</h3>
      <p>
        A cor do anel indica a faixa de frequência. A regra é: a cor é definida
        pela <strong>frequência mais alta (Upper Band Edge)</strong> da porta.
      </p>
      <ul className="list-disc pl-5">
        <li>
          <span className="font-bold text-[#D92120]">VERMELHO (Red):</span>{' '}
          380 - 1000 MHz (Bandas Baixas: 700, 850, 900 MHz)
        </li>
        <li>
          <span className="font-bold text-[#00874F]">VERDE (Green):</span>{' '}
          1001 - 1700 MHz (Banda L: 1400, 1500 MHz)
        </li>
        <li>
          <span className="font-bold text-[#0057A7]">AZUL (Blue):</span> 1701 -
          2300 MHz (Bandas Médias: 1800, 1900, 2100 MHz)
        </li>
        <li>
          <span className="font-bold text-[#FECC00]">AMARELO (Yellow):</span>{' '}
          2301 - 3000 MHz (Bandas Altas: 2300, 2600 MHz)
        </li>
        <li>
          <span className="font-bold text-[#9A4E9E]">ROXO (Purple):</span>{' '}
          3001 - 5000 MHz (Banda C 5G: 3500 MHz)
        </li>
        <li>
          <span className="font-bold text-[#F58220]">LARANJA (Orange):</span>{' '}
          5001 - 6000 MHz (Wi-Fi / LAA: 5 GHz)
        </li>
      </ul>

      <h3>2. Decodificando os "Array IDs" (R1, R2, R1/B1)</h3>
      <p>
        Este é o texto impresso ao lado da porta. A <strong>Letra</strong> é
        a inicial da cor (Banda). O <strong>Número</strong> é o
        identificador do <strong>array</strong> (conjunto de elementos)
        naquela banda.
      </p>
      <p>
        Quando uma antena tem múltiplos arrays na mesma banda (ex: para MIMO
        4x4), os padrões visuais mudam:
      </p>
      <ul className="list-disc pl-5">
        <li>
          <strong>Array 1 (ex: R1):</strong> Anel de cor <strong>Sólido</strong>
        </li>
        <li>
          <strong>Array 2 (ex: R2):</strong> Anel de cor{' '}
          <strong>Segmentado (3 traços)</strong>
        </li>
        <li>
          <strong>Array 3 (ex: R3):</strong> Anel de cor{' '}
          <strong>Segmentado (6 traços)</strong>
        </li>
        <li>
          <strong>Array 4 (ex: R4):</strong> Anel de cor{' '}
          <strong>Segmentado (12 traços)</strong>
        </li>
      </ul>

      {/* --- Visualização Interativa --- */}
      <div className="bg-gray-900 text-white p-6 rounded-lg my-6">
        <h4 className="text-xl font-bold text-white mb-4">
          Galeria de Conectores (Exemplos)
        </h4>
        <p className="text-gray-300 mb-4">
          Veja como o padrão se aplica visualmente.
        </p>

        <h5 className="text-lg font-semibold text-white mt-6 mb-2">
          Single-Band (Arrays Múltiplos)
        </h5>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {singleBand.map((c) => (
            <ConnectorVisual
              key={c.id}
              colors={c.colors}
              segments={c.segments}
              arrayId={c.id}
            />
          ))}
        </div>

        <h5 className="text-lg font-semibold text-white mt-6 mb-2">
          Multiplexadas (Dual-Band)
        </h5>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {duplexed.map((c) => (
            <ConnectorVisual
              key={c.id}
              colors={c.colors}
              segments={c.segments}
              arrayId={c.id}
            />
          ))}
        </div>

        <h5 className="text-lg font-semibold text-white mt-6 mb-2">
          Multiplexadas (Tri-Band)
        </h5>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {triplexed.map((c) => (
            <ConnectorVisual
              key={c.id}
              colors={c.colors}
              segments={c.segments}
              arrayId={c.id}
            />
          ))}
        </div>
      </div>
      {/* --- Fim da Visualização --- */}
    </SectionWrapper>
  );
};

const Part5Evolution: React.FC = () => (
  <SectionWrapper title="Parte 5: A Evolução - AISG v2.0 vs. AISG v3.0">
    <p>
      O padrão evoluiu drasticamente para resolver novos desafios, principalmente
      o 5G e o **compartilhamento de infraestrutura (site sharing)**.
    </p>

    <h3>AISG v2.0 (Legado)</h3>
    <ul>
      <li>
        <strong>Arquitetura:</strong> *Single-Master* (Mestre Único).
      </li>
      <li>
        <strong>O Problema:</strong> Se duas operadoras (ex: TIM e VIVO)
        decidem partilhar a mesma antena, apenas UMA pode controlar os
        dispositivos. A segunda operadora que se liga ao barramento causa um
        conflito. Isto impedia o compartilhamento eficiente de infraestrutura.
      </li>
    </ul>

    <h3>AISG v3.0 (O Padrão Moderno)</h3>
    <p>
      O v3.0 (lançado em 2018) é uma reengenharia completa para resolver isto. A
      <strong>eftx</strong> recomenda fortemente a especificação de hardware
      v3.0 em todas as novas implementações.
    </p>
    <ul>
      <li>
        <strong>Arquitetura:</strong> *Multi-Primary* (Múltiplos Mestres).
      </li>
      <li>
        <strong>A Solução:</strong> Uma antena v3.0 (chamada de **MALD**) atua
        como um "gateway" inteligente.
      </li>
    </ul>

    <InfoBox type="info">
      <strong>Exemplo Prático (Site Sharing v3.0):</strong>
      <ol className="list-decimal list-inside">
        <li>
          A antena MALD tem 4 portas AISG físicas.
        </li>
        <li>
          A TIM (Primário 1) liga-se à porta 1. A antena dá-lhe acesso para
          controlar apenas os seus RETs (R1 e B1).
        </li>
        <li>
          A VIVO (Primário 2) liga-se à porta 2. A antena dá-lhe acesso para
          controlar apenas os seus RETs (R2 e Y1).
        </li>
      </ol>
      Ambas operam de forma independente, na mesma antena, ao mesmo tempo.
    </InfoBox>

    <p>
      <strong>Outras Melhorias Críticas do v3.0:</strong>
    </p>
    <ul>
      <li>
        <strong>Site Mapping (Mapeamento do Site):</strong> Permite à BTS
        descobrir *automaticamente* qual RET controla qual porta de RF.
      </li>
      <li>
        <strong>Exemplo (Site Mapping):</strong> A BTS v3.0 pergunta à antena:
        'Qual a associação do RET ID 1?'. A antena responde: 'RET ID 1 (R1) está
        associado às portas de RF 1 e 2'. Se o instalador ligou os cabos nas
        portas 1 e 3, a BTS gera um alarme de **Erro de Cabeamento**
        imediatamente.
      </li>
      <li>
        <strong>Função Ping & ALS:**</strong> Padroniza a verificação de cabos de
        RF (Ping) e os sensores de orientação (ALS).
      </li>
    </ul>
  </SectionWrapper>
);

const Part6AdvancedTopics: React.FC = () => (
  <SectionWrapper title="Parte 6: Tópicos Avançados - PIM e Antenas Ativas">
    <h3>PIM (Intermodulação Passiva)</h3>
    <p>
      O PIM é um inimigo invisível e um dos problemas mais difíceis de
      diagnosticar. É uma interferência (ruído) gerada em componentes passivos
      (conectores, cabos) que deveriam ser lineares.
    </p>
    <InfoBox type="warning">
      <strong>Exemplo Numérico de PIM (Grave):</strong>
      <ul className="list-disc list-inside">
        <li>
          Uma operadora transmite em **870 MHz (f1)** e **890 MHz (f2)**.
        </li>
        <li>Um conector frouxo causa PIM.</li>
        <li>
          Cálculo do PIM (IM3): (2 \* 870) - 890 = **850 MHz**.
        </li>
        <li>
          <strong>O Problema:</strong> 850 MHz cai *perigosamente perto* (ou
          dentro) da banda de *receção* (Uplink).
        </li>
        <li>
          <strong>Resultado:</strong> A BTS fica "surda". Ela não consegue
          "ouvir" os sinais fracos dos telemóveis. A cobertura encolhe e as
          chamadas caem.
        </li>
      </ul>
      A <strong>eftx</strong> possui equipamento especializado (Certificadores
      PIM) para testar e garantir que a sua infraestrutura está livre deste
      problema.
    </InfoBox>

    <h3>O Papel do AISG em Antenas Ativas (AAS / Massive MIMO)</h3>
    <p>
      Esta é a diferença mais importante para entender o 5G.
    </p>
    <ul>
      <li>
        <strong>Antena Passiva (Tradicional):</strong> É "burra". O Rádio (RRU)
        fica separado. O AISG controla o RET.
      </li>
      <li>
        <strong>Antena Ativa (AAS - 5G):</strong> É "inteligente". O Rádio e a
        Antena são integrados numa única caixa.
      </li>
    </ul>
    <p>
      Numa Antena Ativa (AAS), o controlo é dividido. **Não confunda AISG com
      eCPRI!**
    </p>
    <ol>
      <li>
        <strong>Beamforming (Rápido):</strong> É a "magia" do 5G, direcionando
        feixes para utilizadores em microssegundos.
        <br />
        <strong>Protocolo Usado:</strong>{' '}
        <strong className="text-blue-600">eCPRI</strong> (baseado em Fibra
        Ótica). Transporta dados do utilizador e comandos de beamforming.
        <br />
        <span className="text-red-600 font-semibold">
          O AISG (9.6 kbps) é milhões de vezes lento demais para isto.
        </span>
      </li>
      <li>
        <strong>Controlo Físico (Lento):</strong>
        <br />
        <strong>Protocolo Usado:</strong>{' '}
        <strong className="text-blue-600">AISG</strong> (muitas vezes
        encapsulado na fibra eCPRI).
        <br />
        <strong>Função:</strong> O AISG ainda é usado para funções de gestão
        "lentas":
        <br />
        - Controlar o **Tilt Elétrico Geral** do painel (o ajuste "grosso").
        <br />
        - Ler o sensor **ALS** (azimute, inclinação mecânica, GPS).
        <br />- Reportar alarmes de hardware (temperatura, falhas).
      </li>
    </ol>
  </SectionWrapper>
);

const Part7Specification: React.FC = () => (
  <SectionWrapper title="Parte 7: Como Especificar e Comprar (O Checklist da eftx)">
    <p>
      Quando a <strong>eftx broadcast & Telecom</strong> prepara uma
      especificação para um cliente, nós garantimos que todos os pontos críticos
      são cobertos.
    </p>

    <h3>Checklist para Antena</h3>
    <ul>
      <li>
        <strong>Item:</strong> "Deve ser compatível com{' '}
        <strong>AISG v3.0</strong> e suportar <strong>Multi-Primary</strong>."
        <br />
        <em>
          Justificação: Essencial para permitir o futuro compartilhamento do
          site (site sharing).
        </em>
      </li>
      <li>
        <strong>Item:</strong> "Deve possuir{' '}
        <strong>3 RETs internos independentes</strong>, um por banda."
        <br />
        <em>
          Justificação: Garante que o tilt de cada banda (Baixa, Média, Alta)
          pode ser otimizado separadamente.
        </em>
      </li>
      <li>
        <strong>Item:</strong> "As portas de RF devem ser codificadas conforme o
        padrão <strong>AISG-APC v3.2.1</strong>."
        <br />
        <em>
          Justificação: Reduz a zero os erros de instalação dos cabos de RF.
        </em>
      </li>
      <li>
        <strong>Item:</strong> "Performance 'Low-PIM' certificada,{' '}
        <strong>-153 dBc @ 2x43 dBm</strong> (2x20W)."
        <br />
        <em>
          Justificação: Garante que a antena não gerará auto-interferência,
          protegendo o desempenho do uplink.
        </em>
      </li>
    </ul>

    <h3>Checklist para Cabos</h3>
    <ul>
      <li>
        <strong>Item:</strong> "Cabos de controlo AISG, 10 metros, padrão M16
        8-pinos, com 1 conector Macho e 1 Fêmea, padrão IP68, blindado e com
        proteção UV."
        <br />
        <em>
          Justificação: Especifica o comprimento, conectores para cascata,
          proteção contra água (IP68), ruído (blindado) e degradação solar (UV).
        </em>
      </li>
    </ul>
  </SectionWrapper>
);

const Conclusion: React.FC = () => (
  <SectionWrapper title="Conclusão: O AISG como Ferramenta de Eficiência">
    <p>
      O padrão AISG evoluiu de um simples controlador de "tilt" para uma
      plataforma de automação e compartilhamento de infraestrutura pronta para o
      5G.
    </p>
    <p>
      Dominar esse padrão é essencial, pois ele conecta o projeto da rede
      (Engenharia de RF), à execução física (Instalação) e à otimização
      contínua (Operação).
    </p>
    <div className="bg-blue-600 text-white p-8 rounded-lg my-8 text-center">
      <h3 className="text-2xl font-bold mb-4">
        Leve sua Rede ao Próximo Nível com a eftx
      </h3>
      <p className="text-lg mb-6">
        Dominar o AISG é dominar a eficiência. E na{' '}
        <strong>eftx broadcast & Telecom</strong>, eficiência é a nossa
        linguagem. Com décadas de experiência em campo, profundo conhecimento dos
        padrões e os mais modernos equipamentos de teste (PIM, RF e AISG), nós
        somos o seu parceiro ideal.
      </p>
      <p className="mb-6">
        Deixe a <strong>eftx</strong> ser sua guia na implementação, auditoria e
        otimização de sites. Garantimos instalações mais rápidas, redes mais
        limpas (Low-PIM) e performance máxima.
      </p>
      <a
        href="#"
        className="bg-white text-blue-600 font-bold py-3 px-8 rounded-full text-lg hover:bg-gray-100 transition duration-300"
      >
        Contate um Especialista da eftx Hoje
      </a>
    </div>
  </SectionWrapper>
);

// --- Navegação e Componentes Principais ---

const navItems: NavItem[] = [
  { id: 'intro', title: 'Introdução', subtitle: 'O que é AISG?' },
  { id: 'part1', title: 'Parte 1: Tilt e RET', subtitle: 'Otimização de Cobertura' },
  { id: 'part2', title: 'Parte 2: Camada Física', subtitle: 'Cabos e Conectores' },
  { id: 'part3', title: 'Parte 3: Outros ALDs', subtitle: 'TMAs e Sensores' },
  {
    id: 'part4',
    title: 'Parte 4: Padrão de Cores',
    subtitle: 'O Guia Visual (APC)',
  },
  {
    id: 'part5',
    title: 'Parte 5: Evolução',
    subtitle: 'AISG v2.0 vs v3.0',
  },
  {
    id: 'part6',
    title: 'Parte 6: Tópicos Avançados',
    subtitle: 'PIM e Antenas Ativas',
  },
  {
    id: 'part7',
    title: 'Parte 7: Como Especificar',
    subtitle: 'O Checklist da eftx',
  },
  { id: 'conclusion', title: 'Conclusão', subtitle: 'Fale com a eftx' },
];

const Sidebar: React.FC<{
  currentSection: SectionId;
  onNavigate: (id: SectionId) => void;
  isOpen: boolean;
}> = ({ currentSection, onNavigate, isOpen }) => (
  <nav
    className={`fixed top-0 left-0 h-full bg-gray-800 text-white w-72 z-20 transform transition-transform duration-300 ease-in-out ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    } lg:translate-x-0 lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] overflow-y-auto`}
  >
    <div className="p-5 border-b border-gray-700">
      <h2 className="text-lg font-semibold">Menu do Tutorial</h2>
    </div>
    <ul>
      {navItems.map((item) => (
        <li key={item.id} className="border-b border-gray-700">
          <button
            onClick={() => onNavigate(item.id)}
            className={`w-full text-left p-4 hover:bg-gray-700 focus:outline-none ${
              currentSection === item.id ? 'bg-blue-600' : ''
            }`}
          >
            <span className="flex items-center text-sm font-semibold">
              <BookOpenIcon />
              {item.title}
            </span>
            <span className="text-xs text-gray-400 pl-6">
              {item.subtitle}
            </span>
          </button>
        </li>
      ))}
    </ul>
  </nav>
);

const Header: React.FC<{ onMenuClick: () => void }> = ({ onMenuClick }) => (
  <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-30 flex items-center justify-between px-4 lg:px-6">
    <div className="flex items-center">
      <button
        onClick={onMenuClick}
        className="text-gray-600 p-2 rounded-md hover:bg-gray-100 lg:hidden"
        aria-label="Abrir menu"
      >
        <MenuIcon />
      </button>
      <div className="ml-2 flex items-center">
        <span className="text-xl font-bold text-blue-600">
          eftx
        </span>
        <span className="text-xl font-light text-gray-700 ml-2">
          broadcast & Telecom
        </span>
      </div>
    </div>
    <div className="text-sm font-medium text-gray-800">
      Guia Definitivo do Ecossistema AISG
    </div>
  </header>
);

const Footer: React.FC = () => (
  <footer className="w-full bg-gray-800 text-gray-400 p-6 text-center text-sm">
    © {new Date().getFullYear()} <strong>eftx broadcast & Telecom</strong>.
    Todos os direitos reservados. Este guia é para fins educacionais.
  </footer>
);

// --- Componente Principal da Aplicação ---
export default function App() {
  const [currentSection, setCurrentSection] = useState<SectionId>('intro');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleNavigate = (id: SectionId) => {
    setCurrentSection(id);
    setIsSidebarOpen(false); // Fecha a sidebar em navegação móvel
    window.scrollTo(0, 0); // Rola para o topo
  };

  const renderSection = () => {
    switch (currentSection) {
      case 'intro':
        return <Introduction />;
      case 'part1':
        return <Part1Tilt />;
      case 'part2':
        return <Part2PhysicalLayer />;
      case 'part3':
        return <Part3ALDs />;
      case 'part4':
        return <Part4ColorCoding />;
      case 'part5':
        return <Part5Evolution />;
      case 'part6':
        return <Part6AdvancedTopics />;
      case 'part7':
        return <Part7Specification />;
      case 'conclusion':
        return <Conclusion />;
      default:
        return <Introduction />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)} />

      {/* Overlay para fechar a sidebar em mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black opacity-50 z-10 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}

      <div className="flex pt-16">
        <Sidebar
          currentSection={currentSection}
          onNavigate={handleNavigate}
          isOpen={isSidebarOpen}
        />
        <main className="flex-1 p-6 md:p-10 lg:p-12 overflow-y-auto">
          {renderSection()}
        </main>
      </div>

      <Footer />
    </div>
  );
}
