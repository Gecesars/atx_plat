const OVERLAY_DEFAULT_OPACITY = 0.85;

const state = {
    map: null,
    txMarker: null,
    txData: null,
    txCoords: null,
    rxEntries: [],
    selectedRxIndex: null,
    linkLine: null,
    directionLine: null,
    coverageOverlay: null,
    radiusCircle: null,
    coverageData: null,
    overlayOpacity: OVERLAY_DEFAULT_OPACITY,
    elevationService: null,
    pendingTiltTimeout: null,
    pendingDirectionTimeout: null,
    coverageUnit: 'dbuv',
    rxInfoWindow: null,
};

let profileLoading = false;

function formatNumber(value, suffix = '') {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '-';
    }
    return `${Number(value).toFixed(2)}${suffix}`;
}

function formatDb(value) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '-';
    }
    return `${Number(value).toFixed(2)} dB`;
}

function normalizeAzimuth(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) {
        return 0;
    }
    return ((num % 360) + 360) % 360;
}

function formatAzimuth(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return '-';
    }
    return `${normalizeAzimuth(value).toFixed(1)}°`;
}

function formatWithUnit(value, unit) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return '-';
    }
    return `${Number(value).toFixed(2)} ${unit}`;
}

function parseNullableNumber(raw) {
    if (raw === undefined || raw === null) {
        return null;
    }
    const text = String(raw).trim();
    if (!text) {
        return null;
    }
    const asNumber = Number(text);
    return Number.isFinite(asNumber) ? asNumber : null;
}

function formatLegendValue(value, suffix = '') {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '-';
    }
    return `${Number(value).toFixed(2)}${suffix}`;
}

function updateTxLegend(data) {
    const legend = document.getElementById('txLegend');
    if (!legend || !data) {
        return;
    }
    const municipality = data.txLocationName
        || data.tx_location_name
        || data.municipality
        || '-';
    const power = data.transmissionPower ?? data.transmission_power;
    const tower = data.towerHeight ?? data.tower_height;
    const elevation = data.txElevation ?? data.tx_site_elevation;

    legend.innerHTML = `
        <div class="tx-legend-title">Transmissor</div>
        <div class="tx-legend-line"><span>Município</span><strong>${municipality}</strong></div>
        <div class="tx-legend-line"><span>Potência</span><strong>${formatLegendValue(power, ' W')}</strong></div>
        <div class="tx-legend-line"><span>Terreno</span><strong>${formatLegendValue(elevation, ' m')}</strong></div>
        <div class="tx-legend-line"><span>Altura torre</span><strong>${formatLegendValue(tower, ' m')}</strong></div>
    `;
    legend.hidden = false;
}

function persistTxLocation(latLng) {
    const payload = {
        latitude: Number(latLng.lat().toFixed(6)),
        longitude: Number(latLng.lng().toFixed(6)),
    };
    const projectSlug = getActiveProjectSlug();
    if (projectSlug) {
        payload.projectSlug = projectSlug;
    }
    return fetch('/tx-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then((response) => response.json().then((json) => {
            if (!response.ok) {
                throw new Error(json.error || 'Falha ao salvar a localização da TX.');
            }
            return json;
        }))
        .then((data) => {
            if (!state.txData) {
                state.txData = {};
            }
            state.txData.latitude = payload.latitude;
            state.txData.longitude = payload.longitude;
            if (data.municipality) {
                state.txData.txLocationName = data.municipality;
            }
            if (data.elevation !== undefined && data.elevation !== null) {
                state.txData.txElevation = data.elevation;
            }
            updateTxSummary(state.txData);
            showToast('Localização da TX atualizada.', false);
            return data;
        })
        .catch((error) => {
            console.error(error);
            showToast(error.message || 'Não foi possível salvar a nova posição da TX.', true);
            throw error;
        });
}

function getRxLabel(index) {
    return `RX ${index + 1}`;
}

function openRxLegend(entry) {
    if (!state.rxInfoWindow || !entry) {
        return;
    }
    const index = state.rxEntries.indexOf(entry);
    if (index < 0) {
        return;
    }
    const summary = entry.summary || {};
    const municipalityLine = summary.municipality ? `<div>Município: ${summary.municipality}</div>` : '';
    const content = `
        <div class="rx-legend">
            <strong>${entry.label || getRxLabel(index)}</strong>
            <div>Nível: ${summary.field || '-'}</div>
            <div>Altitude: ${summary.elevation || '-'}</div>
            ${municipalityLine}
        </div>
    `;
    state.rxInfoWindow.setContent(content);
    state.rxInfoWindow.open({
        map: state.map,
        anchor: entry.marker,
    });
}

function getActiveProjectSlug() {
    if (window.coverageProjectSlug) {
        return window.coverageProjectSlug;
    }
    const container = document.getElementById('coverageMapContainer');
    if (container && container.dataset.project) {
        return container.dataset.project;
    }
    return null;
}

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result;
            if (typeof result === 'string') {
                const base64 = result.includes(',') ? result.split(',')[1] : result;
                resolve(base64);
            } else {
                reject(new Error('Falha ao converter imagem.'));
            }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });
}

function updateRadiusLabel() {
    const radiusInput = document.getElementById('radiusInput');
    const radiusValue = document.getElementById('radiusValue');
    radiusValue.textContent = `${radiusInput.value} km`;
    refreshDirectionGuide();
}

function updateTiltLabel(value) {
    document.getElementById('tiltValue').textContent = `${Number(value).toFixed(1)}°`;
}

function updateDirectionLabel(value) {
    const display = document.getElementById('directionValue');
    if (!display) {
        return;
    }
    display.textContent = `${normalizeAzimuth(value).toFixed(1)}°`;
}

function clearDirectionLine() {
    if (state.directionLine) {
        state.directionLine.setMap(null);
        state.directionLine = null;
    }
}

function getActiveRadiusKm() {
    const lastRadius = state.coverageData?.requested_radius_km || state.coverageData?.radius || null;
    if (Number.isFinite(lastRadius)) {
        return Number(lastRadius);
    }
    const radiusInput = document.getElementById('radiusInput');
    if (radiusInput) {
        const sliderValue = Number(radiusInput.value);
        if (Number.isFinite(sliderValue) && sliderValue > 0) {
            return sliderValue;
        }
    }
    return 10;
}

function updateDirectionGuide(direction) {
    if (!state.map || !state.txCoords) {
        return;
    }
    const heading = normalizeAzimuth(direction);
    const radiusKm = Math.max(getActiveRadiusKm(), 1);
    const lineLength = Math.max(radiusKm * 1000, 500);
    const endPoint = google.maps.geometry.spherical.computeOffset(state.txCoords, lineLength, heading);
    const path = [state.txCoords, endPoint];
    clearDirectionLine();
    state.directionLine = new google.maps.Polyline({
        map: state.map,
        path,
        strokeColor: '#ef6c00',
        strokeOpacity: 0.95,
        strokeWeight: 2,
        icons: [{
            icon: {
                path: 'M 0,-1 0,1',
                strokeOpacity: 1,
                scale: 3,
            },
            offset: '0',
            repeat: '12px',
        }],
    });
}

function refreshDirectionGuide() {
    const direction = state.txData?.antennaDirection;
    if (direction === undefined || direction === null) {
        clearDirectionLine();
        return;
    }
    updateDirectionGuide(direction);
}

function updateTxSummary(data) {
    document.getElementById('txLat').textContent = formatNumber(data.latitude, '°');
    document.getElementById('txLng').textContent = formatNumber(data.longitude, '°');
    document.getElementById('txFreq').textContent = data.frequency ? `${Number(data.frequency).toFixed(2)} MHz` : '-';
    document.getElementById('txModel').textContent = data.propagationModel || '-';
    updateTiltLabel(data.antennaTilt || 0);
    document.getElementById('tiltControl').value = data.antennaTilt ?? 0;
    document.getElementById('txDirection').textContent =
        data.antennaDirection === undefined || data.antennaDirection === null
            ? '-'
            : formatAzimuth(data.antennaDirection);
    const directionControl = document.getElementById('directionControl');
    if (directionControl) {
        const directionValue = data.antennaDirection === undefined || data.antennaDirection === null
            ? 0
            : normalizeAzimuth(data.antennaDirection);
        directionControl.value = directionValue;
        updateDirectionLabel(directionValue);
    }

    const municipalityEl = document.getElementById('txMunicipio');
    if (municipalityEl) {
        municipalityEl.textContent = data.txLocationName
            || data.tx_location_name
            || data.municipality
            || '-';
    }

    const elevationEl = document.getElementById('txElevation');
    if (elevationEl) {
        const elevationValue = data.txElevation ?? data.tx_site_elevation;
        elevationEl.textContent = elevationValue !== undefined && elevationValue !== null
            ? formatNumber(elevationValue, ' m')
            : '-';
    }

    const climateInfoEl = document.getElementById('txClimateInfo');
    if (climateInfoEl) {
        const message = data.location_status || data.locationStatus;
        if (message) {
            climateInfoEl.textContent = message;
        } else if (data.climateUpdatedAt) {
            const updatedDate = new Date(data.climateUpdatedAt);
            climateInfoEl.textContent = `Clima atualizado em ${updatedDate.toLocaleString()}`;
        } else {
            climateInfoEl.textContent = 'Clima não ajustado para esta localização';
        }
    }

    updateTxLegend(data);
}

function updateGainSummary(gainComponents, scale) {
    if (!gainComponents) {
        document.getElementById('gainBase').textContent = '-';
        document.getElementById('gainHorizontal').textContent = '-';
        document.getElementById('gainVertical').textContent = '-';
        document.getElementById('fieldScale').textContent = '-';
        return;
    }
    document.getElementById('gainBase').textContent = formatDb(gainComponents.base_gain_dbi || 0);

    if (gainComponents.horizontal_adjustment_db_min !== undefined) {
        const min = formatDb(gainComponents.horizontal_adjustment_db_min);
        const max = formatDb(gainComponents.horizontal_adjustment_db_max);
        document.getElementById('gainHorizontal').textContent = `${min} / ${max}`;
    }

    document.getElementById('gainVertical').textContent = formatDb(gainComponents.vertical_adjustment_db);

    if (scale) {
        document.getElementById('fieldScale').textContent =
            `${formatNumber(scale.min)} – ${formatNumber(scale.max)} dBµV/m`;
    }
}

function updateCenterSummary(metrics) {
    const data = metrics || {};
    document.getElementById('centerLoss').textContent = formatWithUnit(data.combined_loss_center_db, 'dB');
    document.getElementById('centerPower').textContent = formatWithUnit(data.received_power_center_dbm, 'dBm');
    document.getElementById('centerField').textContent = formatWithUnit(data.field_center_dbuv_m, 'dBµV/m');
    document.getElementById('centerGain').textContent = formatWithUnit(data.effective_gain_center_db, 'dB');

    const pathInfo = document.getElementById('pathTypeInfo');
    if (pathInfo) {
        pathInfo.textContent = data.path_type ? `Classe de propagação no centro: ${data.path_type}` : '';
    }

    const distanceValue = data.distance_center_km ?? data.radius_km ?? null;
    document.getElementById('centerDistance').textContent = formatWithUnit(distanceValue, 'km');
    const summaryElement = document.getElementById('centerPath');
    if (summaryElement) {
        summaryElement.textContent = data.path_type || '-';
    }
}

function updateLossSummary(lossComponents) {
    const mapping = {
        L_b0p: 'loss-L_b0p',
        L_bd: 'loss-L_bd',
        L_bs: 'loss-L_bs',
        L_ba: 'loss-L_ba',
        L_b: 'loss-L_b',
        L_b_corr: 'loss-L_b_corr',
    };

    Object.entries(mapping).forEach(([key, elementId]) => {
        const element = document.getElementById(elementId);
        if (!element) {
            return;
        }
        const component = lossComponents ? lossComponents[key] : null;
        if (!component) {
            element.textContent = '-';
            return;
        }
        const centerText = component.center !== undefined && component.center !== null
            ? formatDb(component.center)
            : '-';
        if (component.min !== undefined && component.max !== undefined) {
            element.textContent = `${centerText} (${formatDb(component.min)} – ${formatDb(component.max)})`;
        } else {
            element.textContent = centerText;
        }
    });
}

function refreshReceiverSummaries() {
    if (!state.rxEntries.length || !state.txCoords) {
        updateLinkSummary({});
        return;
    }
    state.rxEntries.forEach((entry, idx) => {
        const position = entry.marker.getPosition();
        computeReceiverSummary(position).then((summary) => {
            entry.summary = summary;
            if (idx === state.selectedRxIndex) {
                updateLinkSummary(summary);
            }
            renderRxList();
        });
    });
}

function serializeReceivers() {
    return state.rxEntries
        .map((entry, index) => {
            const position = entry.marker.getPosition();
            const lat = Number(position.lat());
            const lng = Number(position.lng());
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                return null;
            }
            const summary = entry.summary || {};
            return {
                lat: Number(lat.toFixed(7)),
                lng: Number(lng.toFixed(7)),
                label: entry.label || getRxLabel(index),
                field: summary.field || null,
                elevation: summary.elevation || null,
                distance: summary.distance || null,
                bearing: summary.bearing || null,
                municipality: summary.municipality || null,
            };
        })
        .filter(Boolean);
}

function restoreReceivers(receivers) {
    clearReceivers();
    if (!Array.isArray(receivers) || !receivers.length || !state.map) {
        return;
    }
    receivers.forEach((receiver) => {
        const lat = parseNullableNumber(receiver.lat);
        const lng = parseNullableNumber(receiver.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            return;
        }
        const position = new google.maps.LatLng(lat, lng);
        const presetSummary = {
            field: receiver.field || null,
            elevation: receiver.elevation || null,
            distance: receiver.distance || null,
            bearing: receiver.bearing || null,
            municipality: receiver.municipality || null,
        };
        createRxMarker(position, {
            selectOnCreate: false,
            presetLabel: receiver.label || null,
            presetSummary,
        });
    });
    state.selectedRxIndex = null;
    updateLinkSummary({});
    renderRxList();
}

function showToast(message, isError = false) {
    const card = document.getElementById('mapTooltip');
    if (!card) return;
    card.innerHTML = `<h4>${isError ? 'Atenção' : 'Cobertura'}</h4><p>${message}</p>`;
    card.hidden = false;
    setTimeout(() => {
        card.hidden = true;
    }, 3600);
}

function setProfileLoading(isLoading) {
    profileLoading = Boolean(isLoading);
    const spinner = document.getElementById('profileSpinner');
    if (spinner) {
        spinner.hidden = !profileLoading;
    }
    const button = document.getElementById('btnGenerateProfile');
    if (button) {
        button.disabled = profileLoading || state.selectedRxIndex === null;
    }
}

function setCoverageLoading(isLoading) {
    const spinner = document.getElementById('coverageSpinner');
    if (spinner) {
        spinner.hidden = !isLoading;
    }
    const button = document.getElementById('btnGenerateCoverage');
    if (button) {
        button.disabled = isLoading;
    }
    const toggleElements = document.querySelectorAll('[data-disabled-during-coverage]');
    toggleElements.forEach((element) => {
        element.disabled = isLoading;
    });
}

function fetchMunicipality(latLng) {
    const lat = Number(latLng.lat());
    const lng = Number(latLng.lng());
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        return Promise.resolve(null);
    }
    const params = new URLSearchParams({ lat, lon: lng });
    return fetch(`/reverse-geocode?${params.toString()}`)
        .then((response) => response.json().then((json) => {
            if (!response.ok) {
                throw new Error(json.error || 'Falha ao buscar município.');
            }
            return json.municipality || null;
        }))
        .catch(() => null);
}

function ensureElevationService() {
    if (!state.elevationService) {
        state.elevationService = new google.maps.ElevationService();
    }
    return state.elevationService;
}

function restoreCoverageFromProject(data) {
    if (!data || !data.lastCoverage) {
        return;
    }
    const last = data.lastCoverage;
    if (last.center_metrics) {
        updateGainSummary(null, null);
        document.getElementById('centerLoss').textContent = formatDb(last.center_metrics.combined_loss_center_db);
        document.getElementById('centerPower').textContent = formatDb(last.center_metrics.received_power_center_dbm);
        document.getElementById('centerField').textContent = formatNumber(last.center_metrics.field_center_dbuv_m, ' dBµV/m');
    }

    const radiusInput = document.getElementById('radiusInput');
    if (radiusInput && last.radius_km) {
        radiusInput.value = last.radius_km;
        updateRadiusLabel();
    }

    if (last.center) {
        setTxCoords(new google.maps.LatLng(last.center.lat, last.center.lng), { pan: false });
    }

    if (last.asset_id) {
        applyCoverageOverlay({
            images: {
                dbuv: { image: last.preview, colorbar: null },
            },
            bounds: data.bounds,
            requested_radius_km: last.radius_km,
            center: data.center,
        });
    }
}

function clearCoverageOverlay() {
    if (state.coverageOverlay) {
        state.coverageOverlay.setMap(null);
        state.coverageOverlay = null;
    }
    if (state.radiusCircle) {
        state.radiusCircle.setMap(null);
        state.radiusCircle = null;
    }
}

function applyCoverageOverlay(response) {
    clearCoverageOverlay();

    const bounds = response.bounds;
    if (!bounds || !state.map) return;

    // Seleciona imagem e colorbar na unidade preferida
    let overlayImage = response.image || null;
    let colorbarImage = response.colorbar || null;

    if (!overlayImage && response.images) {
        const availableUnits = Object.keys(response.images);

        let preferredUnit = state.coverageUnit && response.images[state.coverageUnit]
            ? state.coverageUnit
            : null;

        if (!preferredUnit && response.scale?.default_unit && response.images[response.scale.default_unit]) {
            preferredUnit = response.scale.default_unit;
        }

        if (!preferredUnit) {
            preferredUnit = availableUnits[0];
        }

        const unitPayload = response.images[preferredUnit];
        if (unitPayload) {
            overlayImage = unitPayload.image;
            colorbarImage = unitPayload.colorbar;
            state.coverageUnit = preferredUnit;
        }
    }

    if (!overlayImage) {
        console.warn('Resposta sem imagem de cobertura disponível.', response);
        return;
    }

    // Bounds do overlay de calor
    const overlayBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(bounds.south, bounds.west),
        new google.maps.LatLng(bounds.north, bounds.east)
    );

    // Cria o GroundOverlay (heatmap)
    const overlay = new google.maps.GroundOverlay(
        `data:image/png;base64,${overlayImage}`,
        overlayBounds,
        { opacity: state.overlayOpacity }
    );
    overlay.setMap(state.map);
    state.coverageOverlay = overlay;

    // >>> NOVO: clique no overlay também cria RX <<<
    overlay.addListener('click', (event) => {
        if (!event || !event.latLng) return;
        if (!state.txCoords) return;
        createRxMarker(event.latLng);
    });

    // Colorbar lateral
    if (colorbarImage) {
        const card = document.getElementById('colorbarCard');
        const img = document.getElementById('colorbarImage');
        img.src = `data:image/png;base64,${colorbarImage}`;
        card.hidden = false;
    } else {
        const card = document.getElementById('colorbarCard');
        if (card) {
            card.hidden = true;
        }
    }

    // Desenha o círculo de raio (apenas visual)
    if (response.requested_radius_km && response.center) {
        const centerLatLng = new google.maps.LatLng(response.center.lat, response.center.lng);

        state.radiusCircle = new google.maps.Circle({
            map: state.map,
            center: centerLatLng,
            radius: response.requested_radius_km * 1000,
            strokeColor: '#0d6efd',
            strokeOpacity: 0.4,
            strokeWeight: 2,
            fillColor: '#0d6efd',
            fillOpacity: 0.1,
            clickable: false, // <<< não intercepta clique
        });
    }

    refreshDirectionGuide();
}

async function loadCoverageOverlay(lastCoverage) {
    if (!lastCoverage || !lastCoverage.asset_id) {
        throw new Error('Nenhuma mancha de cobertura disponível para este projeto.');
    }
    if (!window.coverageProjectSlug) {
        throw new Error('Projeto não informado para restaurar a cobertura.');
    }

    let slug = lastCoverage.project_slug
        || lastCoverage.projectSlug
        || window.coverageProjectSlug
        || null;
    if (!slug) {
        throw new Error('Projeto não definido para restaurar a cobertura.');
    }
    const summaryId = lastCoverage.json_asset_id;
    let summary = null;

    if (summaryId) {
        try {
            const summaryResponse = await fetch(
                `/projects/${encodeURIComponent(slug)}/assets/${encodeURIComponent(summaryId)}/preview`,
                { headers: { Accept: 'application/json' } },
            );
            if (summaryResponse.ok) {
                summary = await summaryResponse.json();
                if (!slug && summary?.project_slug) {
                    slug = summary.project_slug;
                }
            }
        } catch (error) {
            console.warn('Falha ao carregar resumo da cobertura.', error);
        }
    }
    if (!slug && summary?.project_slug) {
        slug = summary.project_slug;
    }

    const heatmapResponse = await fetch(
        `/projects/${encodeURIComponent(slug)}/assets/${encodeURIComponent(lastCoverage.asset_id)}/preview`
    );
    if (!heatmapResponse.ok) {
        throw new Error('Não foi possível carregar a imagem da cobertura.');
    }
    const heatmapBase64 = await blobToBase64(await heatmapResponse.blob());

    let colorbarBase64 = null;
    if (lastCoverage.colorbar_asset_id) {
        try {
            const colorbarResponse = await fetch(
                `/projects/${encodeURIComponent(slug)}/assets/${encodeURIComponent(lastCoverage.colorbar_asset_id)}/preview`
            );
            if (colorbarResponse.ok) {
                colorbarBase64 = await blobToBase64(await colorbarResponse.blob());
            }
        } catch (error) {
            console.warn('Falha ao carregar barra de cores da cobertura.', error);
        }
    }

    const coveragePayload = {
        images: {
            dbuv: {
                image: heatmapBase64,
                colorbar: colorbarBase64,
                label: summary?.scale?.label || 'Campo elétrico [dBµV/m]',
                unit: 'dBµV/m',
            },
        },
        bounds: summary?.bounds || lastCoverage.bounds,
        colorbar_bounds: summary?.colorbar_bounds || lastCoverage.colorbar_bounds,
        scale: summary?.scale || lastCoverage.scale,
        center: summary?.center || lastCoverage.center,
        requested_radius_km: summary?.requested_radius_km
            || lastCoverage.requested_radius_km
            || lastCoverage.radius_km,
        radius: lastCoverage.radius_km,
        gain_components: summary?.gain_components || lastCoverage.gain_components,
        loss_components: summary?.loss_components || lastCoverage.loss_components,
        center_metrics: summary?.center_metrics || lastCoverage.center_metrics,
        signal_level_dict: summary?.signal_level_dict,
        signal_level_dict_dbm: summary?.signal_level_dict_dbm,
        location_status: summary?.location_status || lastCoverage.location_status,
        receivers: lastCoverage.receivers || summary?.receivers || [],
    };

    const centerLat = parseNullableNumber(
        coveragePayload.center?.lat ?? coveragePayload.center?.latitude
    );
    const centerLng = parseNullableNumber(
        coveragePayload.center?.lng ?? coveragePayload.center?.longitude
    );
    if (Number.isFinite(centerLat) && Number.isFinite(centerLng)) {
        coveragePayload.center = { lat: centerLat, lng: centerLng };
    } else {
        coveragePayload.center = null;
    }

    const requestedRadius = parseNullableNumber(coveragePayload.requested_radius_km);
    const radiusKm = parseNullableNumber(coveragePayload.radius ?? lastCoverage.radius_km);
    coveragePayload.requested_radius_km = requestedRadius ?? radiusKm ?? null;
    coveragePayload.radius = radiusKm ?? requestedRadius ?? null;

    state.coverageData = {
        ...(state.coverageData || {}),
        ...lastCoverage,
        ...coveragePayload,
        summary,
    };
    state.coverageData.asset_id = lastCoverage.asset_id;
    state.coverageData.json_asset_id = lastCoverage.json_asset_id;
    state.coverageData.colorbar_asset_id = lastCoverage.colorbar_asset_id;
    state.coverageData.engine = lastCoverage.engine || state.coverageData.engine || 'p1546';
    state.coverageData.receivers = coveragePayload.receivers;
    state.coverageData.signal_level_dict = coveragePayload.signal_level_dict;
    state.coverageData.signal_level_dict_dbm = coveragePayload.signal_level_dict_dbm;
    state.coverageData.project_slug = slug;
    if (state.txData) {
        state.txData.location_status = coveragePayload.location_status || state.txData.location_status;
        if (coveragePayload.center) {
            state.txData.latitude = coveragePayload.center.lat;
            state.txData.longitude = coveragePayload.center.lng;
        }
        if (coveragePayload.tx_location_name) {
            state.txData.txLocationName = coveragePayload.tx_location_name;
        }
        if (coveragePayload.tx_site_elevation !== undefined && coveragePayload.tx_site_elevation !== null) {
            state.txData.txElevation = coveragePayload.tx_site_elevation;
        }
        if (coveragePayload.tx_parameters) {
            const params = coveragePayload.tx_parameters;
            if (params.power_w !== undefined) state.txData.transmissionPower = params.power_w;
            if (params.tower_height_m !== undefined) state.txData.towerHeight = params.tower_height_m;
            if (params.rx_height_m !== undefined) state.txData.rxHeight = params.rx_height_m;
            if (params.total_loss_db !== undefined) state.txData.total_loss = params.total_loss_db;
            if (params.antenna_gain_dbi !== undefined) state.txData.antennaGain = params.antenna_gain_dbi;
        }
        updateTxSummary(state.txData);
    }

    if (coveragePayload.center) {
        const centerLatLng = new google.maps.LatLng(coveragePayload.center.lat, coveragePayload.center.lng);
        setTxCoords(centerLatLng, { pan: false });
    }

    if (coveragePayload.requested_radius_km) {
        const radiusInput = document.getElementById('radiusInput');
        if (radiusInput) {
            const radiusValue = Number(coveragePayload.requested_radius_km);
            if (Number.isFinite(radiusValue)) {
                radiusInput.value = Math.max(radiusValue, Number(radiusInput.min) || 0);
            }
            updateRadiusLabel();
        }
    }

    applyCoverageOverlay(coveragePayload);
    updateGainSummary(coveragePayload.gain_components, coveragePayload.scale);
    updateLossSummary(coveragePayload.loss_components);
    updateCenterSummary(coveragePayload.center_metrics);

    if (Array.isArray(coveragePayload.receivers)) {
        restoreReceivers(coveragePayload.receivers);
        refreshReceiverSummaries();
        state.coverageData.receivers = serializeReceivers();
    }

    showToast('Última cobertura restaurada.');
    return coveragePayload;
}

function setOverlayOpacity(value) {
    state.overlayOpacity = value;
    if (state.coverageOverlay) {
        state.coverageOverlay.setOpacity(value);
    }
    if (state.radiusCircle) {
        state.radiusCircle.setOptions({ fillOpacity: Math.max(0.05, value / 6) });
    }
}

function findNearestFieldStrength(lat, lng, dict) {
    let best = null;
    let bestDist = Infinity;
    Object.entries(dict).forEach(([key, value]) => {
        const [lt, ln] = key.slice(1, -1).split(',').map(Number);
        const dist = Math.hypot(lat - lt, lng - ln);
        if (dist < bestDist) {
            bestDist = dist;
            best = value;
        }
    });
    return best;
}

function updateLinkSummary(summary) {
    document.getElementById('linkDistance').textContent = summary.distance || '-';
    document.getElementById('linkBearing').textContent = summary.bearing || '-';
    document.getElementById('linkField').textContent = summary.field || '-';
    document.getElementById('linkElevation').textContent = summary.elevation || '-';
}

function highlightRxEntry(index) {
    state.rxEntries.forEach((entry, idx) => {
        entry.marker.setIcon(idx === index ? entry.icons.selected : entry.icons.default);
    });
}

function updateLinkVisuals(entry) {
    if (state.linkLine) {
        state.linkLine.setMap(null);
        state.linkLine = null;
    }
    state.linkLine = new google.maps.Polyline({
        map: state.map,
        path: [state.txCoords, entry.marker.getPosition()],
        strokeColor: '#0d6efd',
        strokeOpacity: 0.9,
        strokeWeight: 3,
    });
    if (entry.summary) {
        updateLinkSummary(entry.summary);
    }
}

function selectRx(index) {
    state.selectedRxIndex = index;
    highlightRxEntry(index);
    const entry = state.rxEntries[index];
    updateLinkVisuals(entry);
    openRxLegend(entry);
    document.getElementById('btnGenerateProfile').disabled = false;
}

function removeRx(index) {
    const [entry] = state.rxEntries.splice(index, 1);
    if (entry) {
        entry.marker.setMap(null);
    }
    if (state.linkLine) {
        state.linkLine.setMap(null);
        state.linkLine = null;
    }
    state.selectedRxIndex = null;
    updateLinkSummary({});
    renderRxList();
    if (state.coverageData) {
        state.coverageData.receivers = serializeReceivers();
    }
    if (state.rxInfoWindow) {
        state.rxInfoWindow.close();
    }
}

function clearReceivers() {
    state.rxEntries.forEach((entry) => entry.marker.setMap(null));
    state.rxEntries = [];
    state.selectedRxIndex = null;

    if (state.linkLine) {
        state.linkLine.setMap(null);
        state.linkLine = null;
    }

    updateLinkSummary({});
    renderRxList();
    document.getElementById('btnGenerateProfile').disabled = true;
    if (state.coverageData) {
        state.coverageData.receivers = [];
    }
    if (state.rxInfoWindow) {
        state.rxInfoWindow.close();
    }
}

function renderRxList() {
    const container = document.getElementById('rxList');
    container.innerHTML = '';

    if (!state.rxEntries.length) {
        container.innerHTML = '<li class="rx-empty">Nenhum ponto RX selecionado.</li>';
        return;
    }

    state.rxEntries.forEach((entry, idx) => {
        const li = document.createElement('li');
        li.className = `rx-item${idx === state.selectedRxIndex ? ' selected' : ''}`;

        const title = document.createElement('div');
        title.className = 'rx-title';
        title.textContent = entry.label || getRxLabel(idx);

        const details = document.createElement('div');
        details.className = 'rx-details';
        const summary = entry.summary || {};
        details.innerHTML = `
            <span>${summary.distance || '-'}</span>
            <span>${summary.field || '-'}</span>
            <span>${summary.elevation || '-'}</span>
        `;

        const actions = document.createElement('div');
        actions.className = 'rx-actions';

        const focusBtn = document.createElement('button');
        focusBtn.type = 'button';
        focusBtn.textContent = 'Focar';
        focusBtn.className = 'btn btn-sm btn-outline-primary';
        focusBtn.onclick = () => {
            state.map.panTo(entry.marker.getPosition());
            state.map.setZoom(Math.max(state.map.getZoom(), 11));
            selectRx(idx);
        };

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = 'Remover';
        removeBtn.className = 'btn btn-sm btn-link text-danger';
        removeBtn.onclick = () => removeRx(idx);

        actions.appendChild(focusBtn);
        actions.appendChild(removeBtn);

        li.appendChild(title);
        li.appendChild(details);
        li.appendChild(actions);

        li.onclick = (event) => {
            if (event.target === removeBtn || event.target === focusBtn) return;
            selectRx(idx);
        };

        container.appendChild(li);
    });
}

function ensureElevationServiceAndGet(position) {
    ensureElevationService();
    return new Promise((resolve) => {
        state.elevationService.getElevationForLocations({ locations: [position] }, (results, status) => {
            if (status === 'OK' && results && results.length) {
                resolve(results[0].elevation);
            } else {
                resolve(null);
            }
        });
    });
}

function computeReceiverSummary(position) {
    const distanceMeters = google.maps.geometry.spherical.computeDistanceBetween(state.txCoords, position);
    const bearing = google.maps.geometry.spherical.computeHeading(state.txCoords, position);

    const summary = {
        distance: `${(distanceMeters / 1000).toFixed(2)} km`,
        bearing: `${bearing.toFixed(1)}°`,
    };

    if (state.coverageData && state.coverageData.signal_level_dict) {
        const field = findNearestFieldStrength(
            position.lat(),
            position.lng(),
            state.coverageData.signal_level_dict
        );
        if (field !== null) {
            summary.field = `${field.toFixed(1)} dBµV/m`;
        }
    }

    return ensureElevationServiceAndGet(position)
        .then((elevation) => {
            if (elevation !== null) {
                summary.elevation = `${elevation.toFixed(1)} m`;
            }
            return fetchMunicipality(position);
        })
        .then((municipality) => {
            if (municipality) {
                summary.municipality = municipality;
            }
            return summary;
        })
        .catch(() => summary);
}

function createRxMarker(position, options = {}) {
    const {
        selectOnCreate = true,
        presetLabel = null,
        presetSummary = null,
    } = options;

    const nextIndex = state.rxEntries.length;
    const labelText = presetLabel || getRxLabel(nextIndex);

    const defaultIcon = {
        path: google.maps.SymbolPath.CIRCLE,
        fillColor: '#6610f2',
        fillOpacity: 0.85,
        scale: 7,
        strokeColor: '#fff',
        strokeWeight: 2,
    };
    const selectedIcon = {
        path: google.maps.SymbolPath.CIRCLE,
        fillColor: '#d63384',
        fillOpacity: 1,
        scale: 8,
        strokeColor: '#fff',
        strokeWeight: 2,
    };

    const marker = new google.maps.Marker({
        position,
        map: state.map,
        icon: defaultIcon,
        title: labelText,
        label: {
            text: labelText,
            color: '#ffffff',
            fontWeight: '600',
        },
    });

    const entry = {
        marker,
        summary: null,
        icons: { default: defaultIcon, selected: selectedIcon },
        label: labelText,
    };

    marker.addListener('click', () => {
        const index = state.rxEntries.indexOf(entry);
        if (index >= 0) {
            selectRx(index);
        }
    });

    state.rxEntries.push(entry);

    const hydrateSummary = (summary) => {
        entry.summary = summary;
        if (state.selectedRxIndex === state.rxEntries.indexOf(entry)) {
            updateLinkSummary(summary);
            openRxLegend(entry);
        }
        renderRxList();
    };

    if (presetSummary) {
        hydrateSummary(presetSummary);
    }

    computeReceiverSummary(position).then(hydrateSummary);

    renderRxList();
    if (selectOnCreate) {
        selectRx(state.rxEntries.length - 1);
    }
    if (state.coverageData) {
        state.coverageData.receivers = serializeReceivers();
    }
}

function handleMapClick(event) {
    if (!state.txCoords) return;
    createRxMarker(event.latLng);
}

function setTxCoords(latLng, { pan = false } = {}) {
    state.txCoords = latLng;

    if (state.txMarker) {
        state.txMarker.setPosition(latLng);
    }

    if (pan) {
        state.map.panTo(latLng);
    }

    if (state.txData) {
        state.txData.latitude = latLng.lat();
        state.txData.longitude = latLng.lng();
        updateTxSummary(state.txData);
    }

    state.rxEntries.forEach((entry, idx) => {
        if (entry.summary) {
            computeReceiverSummary(entry.marker.getPosition()).then((summary) => {
                entry.summary = summary;
                if (idx === state.selectedRxIndex) {
                    updateLinkSummary(summary);
                }
                renderRxList();
            });
        }
    });

    refreshDirectionGuide();
}

function handleTxDragEnd(event) {
    const position = event.latLng;
    setTxCoords(position, { pan: false });
    persistTxLocation(position).catch(() => {});
}

function saveTilt(value) {
    if (state.pendingTiltTimeout) {
        clearTimeout(state.pendingTiltTimeout);
    }

    state.pendingTiltTimeout = setTimeout(() => {
        fetch('/update-tilt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tilt: value }),
        })
        .then((response) => {
            if (!response.ok) {
                return response.json().catch(() => ({})).then((payload) => {
                    throw new Error(payload.error || 'Falha ao atualizar tilt');
                });
            }
            return response.json();
        })
        .then((payload) => {
            const tiltValue = Number(payload?.antennaTilt ?? value);
            if (state.txData) {
                state.txData.antennaTilt = tiltValue;
            }
            updateTiltLabel(tiltValue);
            showToast('Tilt atualizado');
        })
        .catch((error) => {
            console.error(error);
            showToast('Erro ao atualizar tilt', true);
        });
    }, 350);
}

function saveDirection(value) {
    if (state.pendingDirectionTimeout) {
        clearTimeout(state.pendingDirectionTimeout);
    }

    const normalized = normalizeAzimuth(value);

    state.pendingDirectionTimeout = setTimeout(() => {
        fetch('/update-tilt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction: normalized }),
        })
        .then((response) => {
            if (!response.ok) {
                return response.json().catch(() => ({})).then((payload) => {
                    throw new Error(payload.error || 'Falha ao atualizar azimute');
                });
            }
            return response.json();
        })
        .then((payload) => {
            const directionValue = normalizeAzimuth(payload?.antennaDirection ?? normalized);

            if (state.txData) {
                state.txData.antennaDirection = directionValue;
                updateTxSummary(state.txData);
            } else {
                updateDirectionLabel(directionValue);
                const directionDisplay = document.getElementById('txDirection');
                if (directionDisplay) {
                    directionDisplay.textContent = formatAzimuth(directionValue);
                }
            }

            showToast('Azimute atualizado');
            refreshDirectionGuide();
        })
        .catch((error) => {
            console.error(error);
            showToast('Erro ao atualizar azimute', true);
        });
    }, 350);
}

function confirmPersistAndGenerate(options = {}) {
    const { requireConfirm = false } = options;
    const radiusInput = document.getElementById('radiusInput');
    const radiusValue = parseNullableNumber(radiusInput?.value);
    if (!Number.isFinite(radiusValue) || radiusValue <= 0) {
        throw new Error('Informe um raio válido antes de gerar a cobertura.');
    }

    const minField = parseNullableNumber(document.getElementById('minField')?.value);
    const maxField = parseNullableNumber(document.getElementById('maxField')?.value);

    if (!state.txCoords) {
        throw new Error('Posição da TX não definida.');
    }

    if (requireConfirm) {
        const accept = window.confirm('Deseja atualizar a mancha de cobertura usando os parâmetros atuais?');
        if (!accept) {
            return null;
        }
    }

    const coordinates = {
        lat: state.txCoords.lat(),
        lng: state.txCoords.lng(),
    };

    const payload = {
        projectSlug: window.coverageProjectSlug || null,
        coverageEngine: state.coverageData?.engine || state.txData?.coverageEngine || 'p1546',
        radius: radiusValue,
        minSignalLevel: minField,
        maxSignalLevel: maxField,
        customCenter: coordinates,
        receivers: serializeReceivers(),
    };

    return fetch('/calculate-coverage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then((response) => {
            if (!response.ok) {
                return response.json()
                    .catch(() => ({}))
                    .then((payload) => {
                        throw new Error(payload.error || 'Falha ao gerar cobertura');
                    });
            }
            return response.json();
        })
        .then((data) => {
            const coverageState = {
                ...(state.coverageData || {}),
                ...data,
            };

            if (data.assets?.heatmap?.id) {
                coverageState.asset_id = data.assets.heatmap.id;
            }
            if (data.assets?.summary?.id) {
                coverageState.json_asset_id = data.assets.summary.id;
            }
            if (data.assets?.colorbar?.id) {
                coverageState.colorbar_asset_id = data.assets.colorbar.id;
            }
            if (data.lastCoverage) {
                coverageState.asset_id = data.lastCoverage.asset_id || coverageState.asset_id;
                coverageState.json_asset_id = data.lastCoverage.json_asset_id || coverageState.json_asset_id;
                coverageState.colorbar_asset_id = data.lastCoverage.colorbar_asset_id || coverageState.colorbar_asset_id;
                coverageState.radius_km = data.lastCoverage.radius_km ?? coverageState.radius_km;
                coverageState.requested_radius_km = data.lastCoverage.requested_radius_km ?? coverageState.requested_radius_km;
                coverageState.center_metrics = data.lastCoverage.center_metrics || coverageState.center_metrics;
                coverageState.receivers = data.lastCoverage.receivers || coverageState.receivers;
            }

            coverageState.requested_radius_km = data.requested_radius_km ?? coverageState.requested_radius_km ?? payload.radius;
            coverageState.radius_km = data.radius ?? coverageState.radius_km ?? payload.radius;
            coverageState.center_metrics = data.center_metrics || coverageState.center_metrics;
            coverageState.loss_components = data.loss_components || coverageState.loss_components;
            coverageState.gain_components = data.gain_components || coverageState.gain_components;
            coverageState.scale = data.scale || coverageState.scale;
            coverageState.bounds = data.bounds || coverageState.bounds;
            coverageState.location_status = data.location_status || coverageState.location_status;

            coverageState.project_slug = data.project_slug || coverageState.project_slug || payload.projectSlug;
            coverageState.generated_at = data.generated_at || coverageState.generated_at;
            coverageState.engine = coverageState.engine || payload.coverageEngine;
            coverageState.receivers = serializeReceivers();

            state.coverageData = coverageState;

            const centerLat = parseNullableNumber(data.center?.lat ?? data.center?.latitude);
            const centerLng = parseNullableNumber(data.center?.lng ?? data.center?.longitude);
            if (Number.isFinite(centerLat) && Number.isFinite(centerLng)) {
                const centerLatLng = new google.maps.LatLng(centerLat, centerLng);
                setTxCoords(centerLatLng, { pan: false });
            }

            if (Number.isFinite(data.requested_radius_km)) {
                const radiusEl = document.getElementById('radiusInput');
                if (radiusEl) {
                    radiusEl.value = Math.max(Number(data.requested_radius_km), Number(radiusEl.min) || 0);
                    updateRadiusLabel();
                }
            }

            if (data.antenna_direction !== undefined && data.antenna_direction !== null) {
                const normalizedDirection = normalizeAzimuth(data.antenna_direction);
                if (state.txData) {
                    state.txData.antennaDirection = normalizedDirection;
                }
                updateDirectionLabel(normalizedDirection);
                const directionDisplay = document.getElementById('txDirection');
                if (directionDisplay) {
                    directionDisplay.textContent = formatAzimuth(normalizedDirection);
                }
                refreshDirectionGuide();
            }

            applyCoverageOverlay(data);
            updateGainSummary(data.gain_components, data.scale);
            updateLossSummary(data.loss_components);
            updateCenterSummary(data.center_metrics);

            state.coverageData.signal_level_dict = data.signal_level_dict;
            state.coverageData.signal_level_dict_dbm = data.signal_level_dict_dbm;

            if (state.txData) {
                if (data.txLocationName || data.tx_location_name) {
                    state.txData.txLocationName = data.txLocationName || data.tx_location_name;
                }
                if (data.txElevation !== undefined || data.tx_site_elevation !== undefined) {
                    state.txData.txElevation = data.txElevation ?? data.tx_site_elevation;
                }
                state.txData.location_status = data.location_status || state.txData.location_status;
                updateTxSummary(state.txData);
            }

            refreshReceiverSummaries();
            showToast('Cobertura atualizada com sucesso');
        });
}

function generateCoverage() {
    if (!state.txCoords) {
        showToast('Defina a posição da TX antes de gerar a cobertura', true);
        return;
    }

    setCoverageLoading(true);
    let operation = null;
    try {
        operation = confirmPersistAndGenerate({
            requireConfirm: Boolean(state.coverageData?.asset_id),
        });
    } catch (error) {
        setCoverageLoading(false);
        console.error(error);
        showToast(error.message || 'Não foi possível preparar a geração da cobertura', true);
        return;
    }

    if (!operation) {
        setCoverageLoading(false);
        return;
    }

    operation
        .catch((error) => {
            console.error(error);
            showToast(error.message || 'Não foi possível gerar a cobertura', true);
        })
        .finally(() => {
            setCoverageLoading(false);
        });
}

function generateProfile() {
    if (state.selectedRxIndex === null) {
        showToast('Selecione um RX na lista', true);
        return;
    }

    const entry = state.rxEntries[state.selectedRxIndex];
    if (!entry || !state.txCoords) return;

    const projectSlug = getActiveProjectSlug();
    if (!projectSlug) {
        showToast('Defina um projeto antes de gerar o perfil.', true);
        return;
    }

    const tx = state.txCoords;
    const rx = entry.marker.getPosition();

    const payload = {
        path: [
            { lat: tx.lat(), lng: tx.lng() },
            { lat: rx.lat(), lng: rx.lng() },
        ],
        projectSlug,
    };

    setProfileLoading(true);
    fetch('/gerar_img_perfil', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error('Falha ao gerar perfil');
        }
        return response.json();
    })
    .then((data) => {
        if (data.message) {
            showToast(data.message, Boolean(data.warning));
        }
        const img = document.getElementById('profileImage');
        img.src = `data:image/png;base64,${data.image}`;
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('profileModal'));
        modal.show();
    })
    .catch((error) => {
        console.error(error);
        showToast('Não foi possível gerar o perfil', true);
    })
    .finally(() => {
        setProfileLoading(false);
    });
}

function initControls() {
    const radiusInput = document.getElementById('radiusInput');
    if (radiusInput) {
        radiusInput.addEventListener('input', updateRadiusLabel);
    }
    document.getElementById('btnGenerateCoverage').addEventListener('click', generateCoverage);
    document.getElementById('btnGenerateProfile').addEventListener('click', generateProfile);
    document.getElementById('btnClearRx').addEventListener('click', clearReceivers);

    const overlayInput = document.getElementById('overlayOpacity');
    const overlayLabel = document.getElementById('overlayOpacityValue');

    overlayInput.addEventListener('input', (event) => {
        const value = Number(event.target.value);
        overlayLabel.textContent = value.toFixed(2);
        setOverlayOpacity(value);
    });

    overlayInput.value = OVERLAY_DEFAULT_OPACITY;
    overlayLabel.textContent = OVERLAY_DEFAULT_OPACITY.toFixed(2);

    const tiltControl = document.getElementById('tiltControl');
    tiltControl.addEventListener('input', (event) => {
        updateTiltLabel(event.target.value);
    });
    tiltControl.addEventListener('change', (event) => {
        saveTilt(event.target.value);
    });

    const directionControl = document.getElementById('directionControl');
    directionControl.addEventListener('input', (event) => {
        const normalized = normalizeAzimuth(event.target.value);
        event.target.value = normalized;
        updateDirectionLabel(normalized);

        if (state.txData) {
            state.txData.antennaDirection = normalized;
        }

        const directionDisplay = document.getElementById('txDirection');
        if (directionDisplay) {
            directionDisplay.textContent = formatAzimuth(normalized);
        }

        refreshDirectionGuide();
    });
    directionControl.addEventListener('change', (event) => {
        const normalized = normalizeAzimuth(event.target.value);
        event.target.value = normalized;
        saveDirection(normalized);
    });

    updateRadiusLabel();
}

function initCoverageMap() {
    const params = new URLSearchParams();
    const container = document.getElementById('coverageMapContainer');
    if (container && container.dataset.project) {
        params.append('project', container.dataset.project);
        window.coverageProjectSlug = container.dataset.project;
    }

    fetch(`/carregar-dados?${params.toString()}`)
        .then((response) => response.json())
        .then((data) => {
            const projectSettings = data.projectSettings || {};
            const lastCoverage = projectSettings.lastCoverage || {};

            let slugCandidate = data.projectSlug
                || projectSettings.slug
                || lastCoverage.project_slug
                || window.coverageProjectSlug
                || container?.dataset.project
                || null;
            if (slugCandidate) {
                window.coverageProjectSlug = slugCandidate;
            }

            const storedLat = parseNullableNumber(projectSettings.latitude);
            const storedLng = parseNullableNumber(projectSettings.longitude);

            const coverageCenter = lastCoverage.center || lastCoverage.tx_location || null;
            const coverageLat = parseNullableNumber(coverageCenter?.lat ?? coverageCenter?.latitude);
            const coverageLng = parseNullableNumber(coverageCenter?.lng ?? coverageCenter?.longitude);

            const dataLat = parseNullableNumber(data.latitude);
            const dataLng = parseNullableNumber(data.longitude);
            const containerLat = container ? parseNullableNumber(container.dataset.startLat) : null;
            const containerLng = container ? parseNullableNumber(container.dataset.startLng) : null;

            const finalLat = storedLat ?? coverageLat ?? dataLat ?? containerLat ?? 0;
            const finalLng = storedLng ?? coverageLng ?? dataLng ?? containerLng ?? 0;

            state.txData = { ...data };
            state.txData.coverageEngine = data.coverageEngine || data.coverage_engine || state.txData.coverageEngine;
            state.txData.txElevation = data.txElevation ?? data.tx_site_elevation ?? state.txData.txElevation;
            state.txData.txLocationName = data.txLocationName || data.tx_location_name || data.municipality || state.txData.txLocationName;
            state.txData.latitude = finalLat;
            state.txData.longitude = finalLng;
            if (lastCoverage.location_status) {
                state.txData.location_status = lastCoverage.location_status;
            }

            state.coverageData = lastCoverage.project_slug || lastCoverage.asset_id
                ? { ...lastCoverage, project_slug: lastCoverage.project_slug || slugCandidate }
                : null;
            if (state.coverageData) {
                state.coverageData.engine = state.coverageData.engine || state.txData.coverageEngine || 'p1546';
                state.coverageData.bounds = state.coverageData.bounds || null;
                state.coverageData.colorbar_bounds = state.coverageData.colorbar_bounds || null;
                state.coverageData.scale = state.coverageData.scale || null;
                state.coverageData.center = state.coverageData.center || coverageCenter || null;
                state.coverageData.requested_radius_km = state.coverageData.requested_radius_km || state.coverageData.radius_km || null;
                state.coverageData.radius = state.coverageData.radius || state.coverageData.radius_km || null;
                state.coverageData.gain_components = state.coverageData.gain_components || null;
                state.coverageData.loss_components = state.coverageData.loss_components || null;
                state.coverageData.center_metrics = state.coverageData.center_metrics || null;
                state.coverageData.signal_level_dict = state.coverageData.signal_level_dict || null;
                state.coverageData.signal_level_dict_dbm = state.coverageData.signal_level_dict_dbm || null;
                state.coverageData.location_status = state.coverageData.location_status || null;

                if (state.coverageData.center_metrics) {
                    updateCenterSummary(state.coverageData.center_metrics);
                }
                if (state.coverageData.loss_components) {
                    updateLossSummary(state.coverageData.loss_components);
                }
                const storedRadius = parseNullableNumber(
                    state.coverageData.requested_radius_km ?? state.coverageData.radius_km
                );
                if (Number.isFinite(storedRadius)) {
                    const radiusInput = document.getElementById('radiusInput');
                    if (radiusInput) {
                        radiusInput.value = Math.max(storedRadius, Number(radiusInput.min) || 0);
                        updateRadiusLabel();
                    }
                }
            }

            const txLatLng = new google.maps.LatLng(finalLat, finalLng);
            state.txCoords = txLatLng;

            updateTxSummary(state.txData);

            state.map = new google.maps.Map(document.getElementById('coverageMap'), {
                center: txLatLng,
                zoom: 9,
                mapTypeId: 'terrain',
                gestureHandling: 'greedy',
            });
            state.rxInfoWindow = new google.maps.InfoWindow();

            state.txMarker = new google.maps.Marker({
                position: txLatLng,
                map: state.map,
                title: 'Transmissor',
                draggable: true,
                icon: {
                    url: 'https://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png',
                },
            });

            state.txMarker.addListener('dragend', handleTxDragEnd);

            // Clique direto no mapa (fora do overlay) ainda cria RX
            state.map.addListener('click', handleMapClick);

            initControls();
            refreshDirectionGuide();
            ensureElevationService();

            if (state.coverageData) {
                state.coverageData.signal_level_dict = null;
                state.coverageData.signal_level_dict_dbm = null;
            }

            if (state.coverageData && state.coverageData.asset_id) {
                loadCoverageOverlay(state.coverageData)
                    .catch((error) => {
                        console.warn('Não foi possível restaurar a cobertura', error);
                        if (Array.isArray(state.coverageData?.receivers)) {
                            restoreReceivers(state.coverageData.receivers);
                        }
                    });
            } else if (state.coverageData && Array.isArray(state.coverageData.receivers)) {
                restoreReceivers(state.coverageData.receivers);
            }
        })
        .catch((error) => {
            console.error('Erro ao carregar dados do usuário', error);
            showToast('Não foi possível carregar os dados iniciais', true);
        });
}

window.initCoverageMap = initCoverageMap;
