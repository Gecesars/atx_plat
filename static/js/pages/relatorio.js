(function () {
    const app = document.getElementById('reportEditorApp');
    if (!app) return;

    const contextUrl = app.dataset.contextUrl;
    const projectSlug = app.dataset.project;
    const spinner = document.getElementById('reportLoading');
    const form = document.getElementById('reportForm');
    const coverageImg = document.getElementById('coveragePreviewImg');
    const colorbarImg = document.getElementById('colorbarPreviewImg');
    const diagramHorizontal = document.getElementById('diagramHorizontalImg');
    const diagramVertical = document.getElementById('diagramVerticalImg');
    const profileImg = document.getElementById('profilePreviewImg');
    const receiversTable = document.getElementById('receiverSummaryBody');
    const recommendationsContainer = document.getElementById('recommendationsList');
    const statusBanner = document.getElementById('reportStatusBanner');
    const generateBtn = document.getElementById('generatePdfBtn');
    const linkSummaryBlock = document.getElementById('linkSummaryBlock');

    const fields = {
        headerColor: document.getElementById('inputHeaderColor'),
        projectNotes: document.getElementById('inputProjectNotes'),
        overview: document.getElementById('inputOverview'),
        coverage: document.getElementById('inputCoverage'),
        profile: document.getElementById('inputProfile'),
        patternH: document.getElementById('inputPatternH'),
        patternV: document.getElementById('inputPatternV'),
        conclusion: document.getElementById('inputConclusion'),
    };

    const state = {
        aiSections: {},
        recommendations: [],
        headerColor: '#0d47a1',
        projectNotes: '',
        contextLoaded: false,
    };

    const notify = (message, variant = 'info') => {
        if (window.showToast) {
            window.showToast(message, variant);
        } else {
            alert(message);
        }
    };

    const renderRecommendations = () => {
        recommendationsContainer.innerHTML = '';
        const recs = state.recommendations.length ? state.recommendations : ['', ''];
        recs.forEach((rec, index) => {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
            input.value = rec || '';
            input.dataset.index = index;
            input.placeholder = `Recomendação ${index + 1}`;
            input.addEventListener('input', (e) => {
                state.recommendations[Number(e.target.dataset.index)] = e.target.value;
            });
            recommendationsContainer.appendChild(input);
        });
    };

    const renderReceiverSummary = (rows = []) => {
        receiversTable.innerHTML = '';
        if (!rows.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.className = 'text-center text-muted';
            cell.textContent = 'Nenhum receptor qualificado.';
            row.appendChild(cell);
            receiversTable.appendChild(row);
            return;
        }
        rows.forEach((entry) => {
            const row = document.createElement('tr');
            ['label', 'municipality', 'distance_km', 'power_dbm', 'population'].forEach((key) => {
                const cell = document.createElement('td');
                let value = entry[key];
                if (key === 'distance_km' && value != null) value = `${Number(value).toFixed(1)} km`;
                if (key === 'power_dbm' && value != null) value = `${Number(value).toFixed(1)} dBm`;
                if (key === 'population' && value) value = value.toLocaleString('pt-BR');
                cell.textContent = value ?? '—';
                row.appendChild(cell);
            });
            receiversTable.appendChild(row);
        });
    };

    const applyContext = (data) => {
        state.contextLoaded = true;
        state.headerColor = data.header_color || '#0d47a1';
        state.projectNotes = data.notes || '';
        state.aiSections = data.ai_sections || {};
        state.recommendations = Array.isArray(state.aiSections.recommendations)
            ? state.aiSections.recommendations.slice()
            : [];

        fields.headerColor.value = state.headerColor;
        fields.projectNotes.value = state.projectNotes;
        fields.overview.value = state.aiSections.overview || '';
        fields.coverage.value = state.aiSections.coverage || '';
        fields.profile.value = state.aiSections.profile || '';
        fields.patternH.value = state.aiSections.pattern_horizontal || '';
        fields.patternV.value = state.aiSections.pattern_vertical || '';
        fields.conclusion.value = state.aiSections.conclusion || '';

        if (coverageImg && data.coverage?.heatmap_url) {
            coverageImg.src = data.coverage.heatmap_url;
        }
        if (colorbarImg && data.coverage?.colorbar_url) {
            colorbarImg.src = data.coverage.colorbar_url;
            colorbarImg.classList.remove('d-none');
        }
        if (diagramHorizontal && data.diagram_images?.diagrama_horizontal) {
            diagramHorizontal.src = data.diagram_images.diagrama_horizontal;
        }
        if (diagramVertical && data.diagram_images?.diagrama_vertical) {
            diagramVertical.src = data.diagram_images.diagrama_vertical;
        }
        if (profileImg && data.diagram_images?.perfil) {
            profileImg.src = data.diagram_images.perfil;
        }

        renderRecommendations();
        renderReceiverSummary(data.receiver_summary);
        if (linkSummaryBlock) {
            linkSummaryBlock.textContent = data.link_summary || 'Nenhum receptor cadastrado.';
        }
        if (statusBanner) statusBanner.classList.add('d-none');
        app.classList.remove('d-none');
    };

    const gatherOverrides = () => {
        const overrides = {
            header_color: fields.headerColor.value,
            project_notes: fields.projectNotes.value,
            ai_sections: {
                overview: fields.overview.value,
                coverage: fields.coverage.value,
                profile: fields.profile.value,
                pattern_horizontal: fields.patternH.value,
                pattern_vertical: fields.patternV.value,
                conclusion: fields.conclusion.value,
                recommendations: recommendationsContainer.querySelectorAll('input').length
                    ? Array.from(recommendationsContainer.querySelectorAll('input')).map((input) => input.value).filter(Boolean)
                    : [],
            },
        };
        return overrides;
    };

    const toggleLoading = (isLoading) => {
        if (isLoading) {
            spinner.classList.remove('d-none');
            generateBtn.disabled = true;
        } else {
            spinner.classList.add('d-none');
            generateBtn.disabled = false;
        }
    };

    const loadContext = async () => {
        try {
            const response = await fetch(contextUrl, { credentials: 'same-origin' });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Não foi possível carregar o relatório.');
            }
            const data = await response.json();
            applyContext(data);
        } catch (error) {
            if (statusBanner) {
                statusBanner.classList.remove('d-none');
                statusBanner.textContent = error.message || 'Falha ao carregar dados.';
            }
        } finally {
            spinner.classList.add('d-none');
        }
    };

    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            if (!state.contextLoaded) {
                notify('Aguarde o carregamento do contexto.', 'warning');
                return;
            }
            const overrides = gatherOverrides();
            toggleLoading(true);
            try {
                const response = await fetch('/api/reports/analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        project: projectSlug,
                        overrides,
                    }),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Falha ao gerar o relatório.');
                }
                notify('Relatório gerado com sucesso.', 'success');
                if (data.download_url) {
                    window.open(data.download_url, '_blank');
                }
            } catch (error) {
                notify(error.message || 'Erro durante a geração do relatório.', 'danger');
            } finally {
                toggleLoading(false);
            }
        });
    }

    loadContext();
})();
