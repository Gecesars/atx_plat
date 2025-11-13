from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from extensions import db
from app_core.storage import ensure_project_path_exists, storage_root
from app_core.utils import slugify
from app_core.models import Project

from .models import (
    RegulatoryAttachment,
    RegulatoryAttachmentType,
    RegulatoryPillar,
    RegulatoryReport,
    RegulatoryReportStatus,
    RegulatoryValidation,
    RegulatoryValidationStatus,
)
from .report.generator import RegulatoryReportGenerator
from .validators import PipelineOutcome, ValidationResult
from .validators.decea_validator import DECEAValidator
from .validators.rni_validator import RNIValidator
from .validators.servico_validator import ServiceValidator
from .validators.sarc_validator import SARCValidator
from .anatel_basic import build_basic_form
from .attachments import build_auto_attachments


class RegulatoryPipeline:
    def __init__(self) -> None:
        self.validators = [
            DECEAValidator(),
            RNIValidator(),
            ServiceValidator(),
            SARCValidator(),
        ]

    def run(self, payload: Dict[str, Any]) -> PipelineOutcome:
        results: List[ValidationResult] = []
        metrics: Dict[str, Any] = {}
        flags: List[str] = []
        for validator in self.validators:
            result = validator.validate(payload)
            results.append(result)
            metrics[validator.pillar] = result.metrics
            flags.append(result.status)
        if any(flag == "blocked" for flag in flags):
            overall = "blocked"
        elif any(flag == "attention" for flag in flags):
            overall = "attention"
        else:
            overall = "approved"
        return PipelineOutcome(overall, results, metrics)


def _pick(settings: Dict[str, Any], keys: Tuple[str, ...], fallback=None):
    for key in keys:
        if key in settings and settings[key] not in (None, ''):
            return settings[key]
    return fallback


def build_default_payload(project: Project) -> Dict[str, Any]:
    settings = project.settings or {}
    user = project.user
    coverage = settings.get("lastCoverage") or {}

    lat = _pick(settings, ("latitude",), getattr(user, "latitude", None))
    lon = _pick(settings, ("longitude",), getattr(user, "longitude", None))
    torre = _pick(settings, ("towerHeight", "altura_torre"), getattr(user, "tower_height", None))

    station = {
        "servico": settings.get("serviceType") or getattr(user, "servico", "FM"),
        "classe": settings.get("serviceClass") or settings.get("classe") or "B1",
        "canal": settings.get("canal") or settings.get("channel") or settings.get("frequency") or getattr(user, "frequencia", None),
        "frequencia": settings.get("frequency") or getattr(user, "frequencia", None),
        "descricao": project.description,
    }

    system = {
        "potencia_w": _pick(settings, ("transmissionPower", "potencia_w"), getattr(user, "transmission_power", 1.0)),
        "ganho_tx_dbi": _pick(settings, ("antennaGain",), getattr(user, "antenna_gain", 0.0)),
        "perdas_db": _pick(settings, ("Total_loss", "total_loss"), getattr(user, "total_loss", 0.0)),
        "polarizacao": settings.get("polarization") or getattr(user, "polarization", "horizontal"),
        "modelo": settings.get("antennaModel") or settings.get("antenna_model"),
        "altura_torre": torre,
        "azimute": _pick(settings, ("antennaDirection",), getattr(user, "antenna_direction", 0.0)),
        "tilt": _pick(settings, ("antennaTilt",), getattr(user, "antenna_tilt", 0.0)),
        "frequencia_mhz": settings.get("frequency") or getattr(user, "frequencia", 100.0),
        "pattern_metrics": settings.get("patternMetrics"),
    }

    pilar_decea = {
        "coordenadas": {"lat": lat, "lon": lon},
        "altura": torre,
        "pbzpa": settings.get("pbzpa") or {},
        "condicionantes": settings.get("deceaConditions") or [],
    }

    pilar_rni = {
        "classificacao": settings.get("rniScenario") or "ocupacional",
        "distancia_m": settings.get("rniDistance") or 5,
        "responsavel_tecnico": settings.get("rniResponsible") or getattr(user, "username", None),
        "frequencia_mhz": system["frequencia_mhz"],
    }

    attachments = settings.get("regulatoryAttachments")
    if not attachments:
        attachments = build_auto_attachments(project, station, system, coverage, pilar_decea, pilar_rni)

    return {
        "estacao": station,
        "sistema_irradiante": system,
        "pilar_decea": pilar_decea,
        "pilar_rni": pilar_rni,
        "sarc": settings.get("sarcLinks") or [],
        "attachments": attachments,
        "lastCoverage": coverage,
    }


def _attachment_type(value: str) -> RegulatoryAttachmentType:
    try:
        return RegulatoryAttachmentType(value)
    except ValueError:
        return RegulatoryAttachmentType.custom


def _persist_attachment(report: RegulatoryReport, attachment_data: Dict[str, Any], report_dir: Path) -> Path:
    attachments_dir = report_dir / 'attachments'
    attachments_dir.mkdir(parents=True, exist_ok=True)
    raw_name = attachment_data.get('name') or f"attachment-{datetime.utcnow().timestamp():.0f}.pdf"
    filename = slugify(Path(raw_name).stem) + Path(raw_name).suffix
    file_path = attachments_dir / filename

    if attachment_data.get('content'):
        data = base64.b64decode(attachment_data['content'])
        file_path.write_bytes(data)
    elif attachment_data.get('path'):
        source = Path(attachment_data['path'])
        if source.exists():
            file_path.write_bytes(source.read_bytes())
        else:
            file_path.write_text('Arquivo não encontrado na origem informada.')
    else:
        file_path.write_text('Placeholder gerado automaticamente.')

    attachment = RegulatoryAttachment(
        report_id=report.id,
        type=_attachment_type(attachment_data.get('type', 'custom')),
        path=str(file_path.relative_to(storage_root())),
        description=attachment_data.get('description'),
        mime_type=attachment_data.get('mime_type'),
    )
    db.session.add(attachment)
    return file_path


def generate_regulatory_report(project: Project, payload: Dict[str, Any], *, name: str | None = None) -> RegulatoryReport:
    pipeline = RegulatoryPipeline()
    outcome = pipeline.run(payload)

    report_name = name or payload.get('nome') or f"Relatório {project.name}"
    report_slug = slugify(report_name + f"-{datetime.utcnow():%Y%m%d%H%M}")
    report = RegulatoryReport(
        project_id=project.id,
        name=report_name,
        slug=report_slug,
        payload=payload,
        status=RegulatoryReportStatus.pending,
        validation_summary={
            'overall': outcome.overall_status,
            'generated_at': datetime.utcnow().isoformat(),
        },
    )
    db.session.add(report)
    db.session.flush()

    for result in outcome.results:
        status_key = result.status if result.status in RegulatoryValidationStatus.__members__ else 'attention'
        validation = RegulatoryValidation(
            report_id=report.id,
            pillar=RegulatoryPillar(result.pillar),
            status=RegulatoryValidationStatus[status_key],
            messages=result.messages,
            metrics=result.metrics,
        )
        db.session.add(validation)

    attachments_payload = payload.get('attachments') or []
    report_dir = ensure_project_path_exists(project, 'regulatory', report_slug)
    saved_attachments: List[Path] = []
    for attachment in attachments_payload:
        saved_attachments.append(_persist_attachment(report, attachment, report_dir))

    generator = RegulatoryReportGenerator()
    context = generator.build_context(project, report, payload, outcome.results, outcome.metrics)
    html = generator.render_html(context)

    pdf_path = report_dir / 'relatorio.pdf'
    generator.generate_pdf(html, pdf_path)

    zip_path = generator.build_zip(pdf_path, saved_attachments, report_dir)

    report.mark_generated(
        str(pdf_path.relative_to(storage_root())),
        str(zip_path.relative_to(storage_root())),
    )

    if outcome.overall_status == 'blocked':
        report.status = RegulatoryReportStatus.failed
    elif outcome.overall_status == 'attention':
        report.status = RegulatoryReportStatus.validated
    else:
        report.status = RegulatoryReportStatus.generated

    db.session.commit()
    return report
