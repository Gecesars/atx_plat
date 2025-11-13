from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from weasyprint import HTML  # type: ignore
except Exception:  # pragma: no cover
    HTML = None

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from ..engine.coverage import summarize_coverage
from ..anatel_basic import build_basic_form


class RegulatoryReportGenerator:
    def __init__(self) -> None:
        template_path = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=select_autoescape(['html'])
        )

    def build_context(self, project, report, payload, validations, derived_metrics):
        context = {
            'project': project,
            'report': report,
            'station': payload.get('estacao', {}),
            'system': payload.get('sistema_irradiante', {}),
            'decea': derived_metrics.get('decea', {}),
            'rni': derived_metrics.get('rni', {}),
            'erp': derived_metrics.get('servico', {}).get('erp', derived_metrics.get('rni', {})),
            'patterns': payload.get('sistema_irradiante', {}).get('pattern_metrics', {}),
            'sarc_links': payload.get('sarc', []),
            'sarc_budget': derived_metrics.get('sarc', {}),
            'validations': [v.to_dict() for v in validations],
            'coverage': summarize_coverage(payload),
            'generated_at': datetime.utcnow(),
            'anatel_basic_form': build_basic_form(project),
        }
        if not context['erp']:
            context['erp'] = derived_metrics.get('rni', {})
        return context

    def render_html(self, context: Dict[str, Any]) -> str:
        template = self.env.get_template('relatorio_base.html')
        return template.render(**context)

    def _render_with_reportlab(self, html: str, output_path: Path) -> None:
        c = canvas.Canvas(str(output_path), pagesize=A4)
        textobject = c.beginText(40, A4[1] - 40)
        for line in html.splitlines():
            textobject.textLine(line[:110])
        c.drawText(textobject)
        c.showPage()
        c.save()

    def generate_pdf(self, html: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if HTML:
            HTML(string=html, base_url=str(Path(current_app.root_path))).write_pdf(str(output_path))
        else:  # pragma: no cover
            self._render_with_reportlab(html, output_path)

    def build_zip(self, pdf_path: Path, attachments: Iterable[Path], output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = output_dir / 'mosaico_submit.zip'
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(pdf_path, arcname='relatorio.pdf')
            for attachment in attachments:
                if attachment and attachment.exists():
                    bundle.write(attachment, arcname=attachment.name)
        return zip_path
