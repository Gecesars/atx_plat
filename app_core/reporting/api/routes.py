from __future__ import annotations

from flask import jsonify, request, url_for
from flask_login import login_required, current_user

from app_core.utils import project_by_slug_or_404

from ..service import generate_analysis_report, AnalysisReportError, build_analysis_preview
from . import bp


@bp.route('/analysis', methods=['POST'])
@login_required
def analysis_report():
    payload = request.get_json() or {}
    slug = payload.get('project') or payload.get('projectSlug')
    if not slug:
        return jsonify({'error': 'Informe o slug do projeto.'}), 400
    project = project_by_slug_or_404(slug, current_user.uuid)
    try:
        overrides = payload.get('overrides') or {}
        report = generate_analysis_report(project, overrides=overrides)
    except AnalysisReportError as exc:
        return jsonify({'error': str(exc)}), 400
    download_url = None
    if report.pdf_asset:
        download_url = url_for('projects.asset_preview', slug=project.slug, asset_id=report.pdf_asset.id)
    return jsonify({
        'report_id': str(report.id),
        'project': project.slug,
        'title': report.title,
        'download_url': download_url,
    }), 201


@bp.route('/analysis/context', methods=['GET'])
@login_required
def analysis_context():
    slug = request.args.get('project') or request.args.get('projectSlug')
    if not slug:
        return jsonify({'error': 'Informe o slug do projeto.'}), 400
    project = project_by_slug_or_404(slug, current_user.uuid)
    try:
        context = build_analysis_preview(project)
    except AnalysisReportError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify(context), 200
