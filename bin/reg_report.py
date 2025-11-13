#!/usr/bin/env python3
"""CLI para geração de Relatório Técnico ANATEL."""

import argparse
import json
from pathlib import Path

from app3 import app
from extensions import db  # noqa: F401
from app_core.models import Project
from app_core.regulatory.service import generate_regulatory_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera relatório ANATEL a partir de um JSON.")
    parser.add_argument('--project', required=True, help='Slug do projeto associado.')
    parser.add_argument('--input', required=True, help='Arquivo JSON com dados regulatórios.')
    args = parser.parse_args()

    data_path = Path(args.input)
    if not data_path.exists():
        raise SystemExit(f"Arquivo {args.input} não encontrado.")
    payload = json.loads(data_path.read_text())

    with app.app_context():
        project = Project.query.filter_by(slug=args.project).first()
        if not project:
            raise SystemExit(f"Projeto {args.project} não localizado.")
        report = generate_regulatory_report(project, payload)
        print(f"Relatório gerado: {report.output_pdf_path} (status {report.status.value})")


if __name__ == '__main__':
    main()
