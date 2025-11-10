from __future__ import annotations

import base64
import json
import re
from typing import Any, Dict

import google.generativeai as genai
from flask import current_app


class AIUnavailable(RuntimeError):
    """Raised when the Gemini client cannot be used."""


class AISummaryError(RuntimeError):
    """Raised when the summary request fails for any reason."""


ANALYSIS_PROMPT = """Você é um engenheiro especialista em radiodifusão TV e FM.
 Não invente dados: se algo não existir, explique a limitação explicitamente e escreva "Dados indisponíveis". Nunca retorne informações ambiguas ou incompletas.
   Nunca mencione que é um modelo ou utilize os termos "IA" ou "inteligência artificial".
     Responda EXCLUSIVAMENTE em JSON válido no formato: {{ "overview": "...", "coverage": "...", "profile": "...", "pattern_horizontal": "...", "pattern_vertical": "...", "recommendations": ["...", "..."], "conclusion": "...", "link_analyses": [ {{"label": "...", "analysis": "..."}} ] }}

Contexto:

    Projeto: {project_name} ({project_slug})

    Serviço: {service} / Classe {service_class}

    Região: {location}

    Engine: {engine}

    Clima: {climate} / caso não seja passado busque o clima para location

    Notas do projeto: {project_notes}

    Pico a pico do diagrama horizontal: {horizontal_peak_to_peak_db} dB

    Receptores avaliados (resumo): {link_summary}

    Receptores detalhados (JSON): {link_payload} - Potência do Transmissor (Entrada): {tx_power_w} W - Ganho da Antena (Entrada): {antenna_gain_dbi} dBi - Perdas (Entrada): {losses_db} dB

Parâmetros principais:

    ERP estimada: {erp_dbm} dBm

    Raio planejado: {radius_km} km

    Frequência: {frequency_mhz} MHz

    Polarização: {polarization}

    Campo no centro: {field_center} dBµV/m

    Potência RX: {rx_power} dBm

    Perda combinada: {loss_center} dB

    Ganho efetivo: {gain_center} dB

Requisitos:

    overview: Inicie a string OBRIGATORIAMENTE com o histórico de cálculo da ERP, formatado exatamente assim (substitua X, Y, Z, A, B pelos valores calculados): "Cálculo ERP: [P_tx: 10*log10({tx_power_w}) = X dBW] + [G_ant: {antenna_gain_dbi}dBi - 2.15 = Y dBd] - [Perdas: {losses_db} dB] = [ERP: Z dBW / A dBm / B kW]." Após este texto de cálculo, insira um caractere de nova linha (use \n) e continue com o resumo executivo de até 7 frases.

    coverage: análise da mancha/cobertura.

    profile: análise do perfil de enlace.

    pattern_horizontal: comentários sobre direcionalidade azimutal. 1. Utilize EXCLUSIVAMENTE os dados da legenda do diagrama (parâmetro de entrada {horizontal_peak_to_peak_db} dB). Ignore quaisquer outros valores ou estimativas visuais. 2. Reporte a variação máxima (ripple) do diagrama, que é a metade do pico-a-pico (Cálculo: Variação = {horizontal_peak_to_peak_db} / 2 dB). 3. Use este valor de variação (+/- X dB) para classificar o sistema (ex: quasi-omnidirecional se variação < 1.5 dB; direcional se > 3dB). 4. Comente se esta direcionalidade está alinhada às {project_notes}.

    pattern_vertical: comentários sobre tilt/elevação/ nulos e lobulos.

    recommendations: lista com 3 ou mais recomendações objetivas.

    conclusion: parecer final considerando as notas do projeto e a omnidirecionalidade (conforme calculado em pattern_horizontal).

    link_analyses: para cada receptor listado no JSON acima, forneça análise específica indicando distância, campo, potência, coerência com a mancha/perfil e recomendações pontuais se necessário.

    Ao comentar os diagramas horizontal/vertical, cite explicitamente o pico a pico (dB) e se o sistema é omni ou direcional.

    Utilize o resumo de receptores para avaliar cada enlace no campo profile/conclusion, apontando discrepâncias de campo/potência. Caso alguma imagem não esteja disponível, informe explicitamente que a análise ficou limitada. As imagens (mancha, perfil e diagramas) serão fornecidas como anexos inline; use-as nos campos indicados. """


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.S)


def _extract_json_text(raw_text: str) -> str:
    raw_text = (raw_text or "").strip()
    if not raw_text:
        raise AISummaryError("Resposta vazia do modelo Gemini.")
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.S | re.I)
    if fence_match:
        return fence_match.group(1)
    match = _JSON_BLOCK_RE.search(raw_text)
    if match:
        return match.group(0)
    return raw_text


def build_ai_summary(
    project,
    snapshot: Dict[str, Any],
    metrics: Dict[str, Any],
    images: Dict[str, bytes] | None = None,
    links_payload: list[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise AIUnavailable("GEMINI_API_KEY não configurada.")
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    links_json = json.dumps(links_payload or [], ensure_ascii=False, indent=2)

    prompt = ANALYSIS_PROMPT.format(
        project_name=project.name,
        project_slug=project.slug,
        service=metrics.get("service") or (project.settings or {}).get("serviceType") or "FM",
        service_class=metrics.get("service_class") or (project.settings or {}).get("serviceClass") or "—",
        location=metrics.get("location") or snapshot.get("tx_location_name") or "—",
        erp_dbm=metrics.get("erp_dbm") or "—",
        radius_km=metrics.get("radius_km") or "—",
        frequency_mhz=metrics.get("frequency_mhz") or "—",
        polarization=metrics.get("polarization") or "—",
        field_center=metrics.get("field_center") or "—",
        rx_power=metrics.get("rx_power") or "—",
        loss_center=metrics.get("loss_center") or "—",
        gain_center=metrics.get("gain_center") or "—",
        engine=snapshot.get("engine") or "—",
        climate=metrics.get("climate") or "Não informado",
        project_notes=metrics.get("project_notes") or "Sem notas registradas.",
        horizontal_peak_to_peak_db=metrics.get("horizontal_peak_to_peak_db") or "—",
        link_summary=metrics.get("link_summary") or "Nenhum receptor cadastrado.",
        link_payload=links_json,
    )

    parts: list[dict[str, Any]] = [{"text": prompt}]
    if images:
        for label, blob in images.items():
            if not blob:
                continue
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": base64.b64encode(blob).decode('utf-8'),
                }
            })
            parts.append({
                "text": f"A imagem acima representa '{label}'. Considere-a ao preencher os campos apropriados."
            })

    response = model.generate_content(parts)
    text = _extract_json_text(getattr(response, "text", ""))

    try:
        summary = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AISummaryError("Formato de resposta inválido do modelo.") from exc

    required = [
        "overview",
        "coverage",
        "profile",
        "pattern_horizontal",
        "pattern_vertical",
        "recommendations",
        "conclusion",
        "link_analyses",
    ]
    for key in required:
        if key not in summary:
            raise AISummaryError(f"Campo '{key}' ausente na resposta do modelo.")
    recs = summary.get("recommendations")
    if isinstance(recs, str):
        recs = [item.strip() for item in recs.split("\n") if item.strip()]
    if not isinstance(recs, list):
        raise AISummaryError("Campo 'recommendations' deveria ser uma lista.")
    summary["recommendations"] = recs[:2] if recs else []
    link_analyses = summary.get("link_analyses") or []
    if isinstance(link_analyses, dict):
        link_analyses = [link_analyses]
    normalized_links = []
    if isinstance(link_analyses, list):
        for item in link_analyses:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            analysis = item.get("analysis") or item.get("texto") or item.get("comentario")
            if not label or not analysis:
                continue
            normalized_links.append({"label": str(label), "analysis": str(analysis)})
    summary["link_analyses"] = normalized_links
    return summary
