// Variables globales
let datos = [];
let diaActual = 1;
let isPlaying = false;
let velocidad = 1;
let animationInterval = null;
let escenarioSeleccionado = 0;
let escenarioDisponibles = [];

// Elementos del DOM
const dayNumber = document.getElementById('dayNumber');
const dayDate = document.getElementById('dayDate');
const accionesHoy = document.getElementById('accionesHoy');
const ofertaBrutaM3 = document.getElementById('ofertaBrutaM3');
const perdidaTotalM3 = document.getElementById('perdidaTotalM3');
const caudalEfectivoLS = document.getElementById('caudalEfectivoLS');
const stockHoy = document.getElementById('stockHoy');
const desmarqueHoy = document.getElementById('desmarqueHoy');
const turnoActivo = document.getElementById('turnoActivo');
const chipTurnoActivo = document.getElementById('chipTurnoActivo');
const chipEnParada = document.getElementById('chipEnParada');
const chipAperturaCanal = document.getElementById('chipAperturaCanal');
const logicDesc = document.getElementById('logicDesc');
const playBtn = document.getElementById('playBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const endBtn = document.getElementById('endBtn');
const speedSlider = document.getElementById('speedSlider');
const speedValue = document.getElementById('speedValue');
const daySlider = document.getElementById('daySlider');
const dayValue = document.getElementById('dayValue');
const progressBar = document.getElementById('progressBar');
const chart1 = document.getElementById('chart1');
const chart2 = document.getElementById('chart2');
const scenarioSelect = document.getElementById('scenarioSelect');
const maxSinSuperficial = document.getElementById('maxSinSuperficial');
const diasSinAgua = document.getElementById('diasSinAgua');
const sumaSuperficial = document.getElementById('sumaSuperficial');
const ofertaTotalDisp = document.getElementById('ofertaTotalDisp');
const perdidaMin = document.getElementById('perdidaMin');
const perdidaMax = document.getElementById('perdidaMax');
const perdidaProm = document.getElementById('perdidaProm');
const promedioTotal = document.getElementById('promedioTotal');
const parametrosBox = document.getElementById('parametrosBox');

// Cargar escenarios disponibles
async function cargarEscenarios() {
    try {
        const response = await fetch('/api/escenarios');
        const json = await response.json();
        escenarioDisponibles = json.escenarios;
        
        // Llenar selector de escenarios
        scenarioSelect.innerHTML = '';
        escenarioDisponibles.forEach(escenario => {
            const option = document.createElement('option');
            option.value = String(escenario);
            option.textContent = escenario === 0 ? 'Principal' : `Escenario ${Math.abs(escenario)} (${escenario > 0 ? '+' : ''}${escenario}%)`;
            scenarioSelect.appendChild(option);
        });
        
        escenarioSeleccionado = escenarioDisponibles.includes(0) ? 0 : escenarioDisponibles[0];
        scenarioSelect.value = String(escenarioSeleccionado);  // Establecer dropdown a "Principal" por defecto
        console.log(`[OK] ${escenarioDisponibles.length} escenarios cargados`);
    } catch (error) {
        console.error('Error cargando escenarios:', error);
        escenarioDisponibles = [0];
    }
}

// Cargar datos al inicio
async function cargarDatos() {
    try {
        const url = `/api/datos?escenario=${escenarioSeleccionado}`;
        const response = await fetch(url);
        const json = await response.json();
        datos = json.datos;
        daySlider.max = datos.length;
        dayValue.textContent = `1 / ${datos.length}`;
        
        // Reiniciar a día 1
        diaActual = 1;
        isPlaying = false;
        playBtn.style.opacity = '1';
        if (animationInterval) clearInterval(animationInterval);
        
        console.log(`✓ Datos cargados: ${datos.length} días (Escenario ${escenarioSeleccionado})`);
        
        // Cargar parámetros (solo una vez)
        cargarParametros();
        
        actualizarGrafico();
        actualizarEstadisticas();
        cargarIndicadores();
    } catch (error) {
        console.error('Error cargando datos:', error);
        chart1.innerHTML = '<p style="padding: 20px; color: red;">Error cargando datos</p>';
    }
}

// Cargar indicadores del escenario
async function cargarIndicadores() {
    try {
        const response = await fetch(`/api/indicadores?escenario=${escenarioSeleccionado}`);
        const json = await response.json();
        
        if (!json.indicador) {
            console.warn('No hay indicadores disponibles para este escenario');
            return;
        }
        
        const ind = json.indicador;
        
        maxSinSuperficial.textContent = ind.Tiempo_Max_Sin_Agua_Superficial_Dias || '-';
        diasSinAgua.textContent = ind.Dias_Sin_Ninguna_Agua || '-';
        sumaSuperficial.textContent = (ind.Suma_Total_Agua_Superficial_m3 || 0).toFixed(0);
        ofertaTotalDisp.textContent = (ind.Suma_Total_Oferta_m3 || 0).toFixed(0);
        promedioTotal.textContent = (ind.Promedio_Oferta_Total_m3_dia || 0).toFixed(2);
        
        console.log('✓ Indicadores cargados para escenario ' + escenarioSeleccionado);
    } catch (error) {
        console.error('Error cargando indicadores:', error);
        maxSinSuperficial.textContent = '-';
        diasSinAgua.textContent = '-';
        sumaSuperficial.textContent = '-';
        ofertaTotalDisp.textContent = '-';
        promedioTotal.textContent = '-';
    }
}

// Cargar parámetros del modelo (se carga una sola vez)
let parametrosCargados = false;
let parametrosGlobales = null;
async function cargarParametros() {
    if (parametrosCargados) return; // Cargar solo una vez
    
    try {
        const response = await fetch('/api/parametros');
        const parametros = await response.json();
        parametrosGlobales = parametros;  // guardar para uso en actualizarEstadisticas
        
        let html = '';
        
        // Sección ACCIONES
        html += '<div class="param-section">';
        html += '<div class="param-section-title">⚡ Acciones de Agua</div>';
        html += `<div class="param-item"><span class="param-label">Número:</span><span class="param-value">${parametros.ACCIONES.NUMERO_ACCIONES}</span></div>`;
        html += `<div class="param-item"><span class="param-label">Valor/Acción:</span><span class="param-value">1 L/s</span></div>`;
        html += `<div class="param-item"><span class="param-label">Duración turno:</span><span class="param-value">${parametros.ACCIONES.HORAS_TURNO || 12} horas</span></div>`;
        html += `<div class="param-item"><span class="param-label">Caudal bruto/acción:</span><span class="param-value">${parametros.ACCIONES.NUMERO_ACCIONES} L/s</span></div>`;
        html += `<div class="param-item" style="border-top:1px solid #ffffff33;padding-top:6px;margin-top:4px"><span class="param-label" style="color:#4fc3f7">Caudal máximo:</span><span class="param-value" style="color:#4fc3f7;font-size:1.1em">${parametros.ACCIONES.CAUDAL_MAXIMO_LS || 0} L/s</span></div>`;
        html += '</div>';
        
        // Sección DESMARQUE
        html += '<div class="param-section">';
        html += '<div class="param-section-title">📊 Desmarque</div>';
        html += `<div class="param-item"><span class="param-label">Inicial (antes):</span><span class="param-value">${parametros.DESMARQUE.PORCENTAJE_INICIAL}%</span></div>`;
        html += `<div class="param-item"><span class="param-label">Final (desde):</span><span class="param-value">${parametros.DESMARQUE.PORCENTAJE_FINAL}%</span></div>`;
        html += `<div class="param-item"><span class="param-label">Fecha Cambio:</span><span class="param-value">${parametros.DESMARQUE.FECHA_CAMBIO}</span></div>`;
        html += `<div class="param-item"><span class="param-label">Salto escenarios:</span><span class="param-value">±${parametros.DESMARQUE.SALTO_DESMARQUE}%</span></div>`;
        html += '</div>';
        
        html += '<div class="param-section">';
        html += '<div class="param-section-title">💧 Agua Subterránea</div>';
        if (parametros.AGUA_SUBTERRANEA.RECARGAS && parametros.AGUA_SUBTERRANEA.RECARGAS.length > 0) {
            parametros.AGUA_SUBTERRANEA.RECARGAS.forEach((r, i) => {
                html += `<div class="param-item"><span class="param-label">Recarga ${i+1} (${r.fecha}):</span><span class="param-value">${r.cantidad} m³</span></div>`;
            });
        }
        // Sección TURNO
        html += '<div class="param-section">';
        html += '<div class="param-section-title">🔄 Ciclo de Turno</div>';
        html += `<div class="param-item"><span class="param-label">Frecuencia:</span><span class="param-value">Cada ${parametros.TURNO.FRECUENCIA_DIAS} días</span></div>`;
        html += `<div class="param-item"><span class="param-label">Mantenimiento:</span><span class="param-value">${parametros.TURNO.MANTENIMIENTO_DIAS} días</span></div>`;
        html += '</div>';
        
        parametrosBox.innerHTML = html;
        parametrosCargados = true;
        console.log('✓ Parámetros cargados');
    } catch (error) {
        console.error('Error cargando parámetros:', error);
        parametrosBox.innerHTML = '<p style="color: red;">Error cargando parámetros</p>';
    }
}

// Cargar variables del estado actual
async function cargarVariables() {
    try {
        const response = await fetch(`/api/variables?escenario=${escenarioSeleccionado}&dia=${diaActual}`);
        const vars = await response.json();
        
        // Actualizar elementos con valores de variables
        if (desmarqueHoy) desmarqueHoy.textContent = vars.PORCENTAJE_DESMARQUE.toFixed(2);
        if (turnoActivo) turnoActivo.textContent = vars.TURNO_ACTIVO ? 'Sí' : 'No';
        
        console.log('✓ Variables cargadas para día ' + diaActual);
    } catch (error) {
        console.error('Error cargando variables:', error);
        // Valores por defecto si hay error
        if (desmarqueHoy) desmarqueHoy.textContent = '0.00';
        if (turnoActivo) turnoActivo.textContent = '-';
        resetLogicaApertura();
    }
}

function actualizarLogicaApertura(turno, parada, apertura) {
    if (chipTurnoActivo) {
        chipTurnoActivo.textContent = turno ? 'Sí' : 'No';
        chipTurnoActivo.className = 'logic-chip ' + (turno ? 'chip-true' : 'chip-neutral');
    }
    if (chipEnParada) {
        chipEnParada.textContent = parada ? 'Sí' : 'No';
        // Parada=Sí es malo (bloquea), Parada=No es bueno
        chipEnParada.className = 'logic-chip ' + (parada ? 'chip-parada' : 'chip-neutral');
    }
    if (chipAperturaCanal) {
        chipAperturaCanal.textContent = apertura ? 'ABIERTO' : 'BLOQUEADO';
        chipAperturaCanal.className = 'logic-chip logic-result ' + (apertura ? 'chip-open' : 'chip-closed');
    }
    if (logicDesc) {
        if (apertura === 1) {
            logicDesc.textContent = '✓ Turno activo sin parada · el canal se abre hoy';
            logicDesc.className = 'logic-desc desc-ok';
        } else if (turno === 1 && parada === 1) {
            logicDesc.textContent = '⚠ Turno bloqueado por mantenimiento · no hay agua superficial hoy';
            logicDesc.className = 'logic-desc desc-warn';
        } else if (turno === 0 && parada === 1) {
            logicDesc.textContent = '— Sin turno y en período de mantenimiento';
            logicDesc.className = 'logic-desc desc-neutral';
        } else {
            logicDesc.textContent = '— Día sin turno · el canal permanece cerrado';
            logicDesc.className = 'logic-desc desc-neutral';
        }
    }
}

function resetLogicaApertura() {
    if (chipTurnoActivo) { chipTurnoActivo.textContent = '-'; chipTurnoActivo.className = 'logic-chip chip-neutral'; }
    if (chipEnParada)    { chipEnParada.textContent = '-';    chipEnParada.className    = 'logic-chip chip-neutral'; }
    if (chipAperturaCanal) { chipAperturaCanal.textContent = '-'; chipAperturaCanal.className = 'logic-chip logic-result chip-neutral'; }
    if (logicDesc) { logicDesc.textContent = '—'; logicDesc.className = 'logic-desc desc-neutral'; }
}

// Actualizar indicadores dinámicamente hasta el día actual
function actualizarIndicadoresDinamicos() {
    if (!datos.length || diaActual < 1 || diaActual > datos.length) return;
    
    // Datos acumulados hasta el día actual
    const datosAcumulados = datos.slice(0, diaActual);
    
    // 1. Días consecutivos máximos sin agua superficial (hasta hoy)
    let maxDiasSinSuperficial = 0;
    let diasConsecutivos = 0;
    for (let d of datosAcumulados) {
        const oferta = parseFloat(d.OfertaSuperficial || 0);
        if (oferta === 0) {
            diasConsecutivos++;
            maxDiasSinSuperficial = Math.max(maxDiasSinSuperficial, diasConsecutivos);
        } else {
            diasConsecutivos = 0;
        }
    }
    
    // 2. Días consecutivos máximos sin ninguna agua (hasta hoy)
    let maxDiasSinAgua = 0;
    diasConsecutivos = 0;
    for (let d of datosAcumulados) {
        const oferta = parseFloat(d.OfertaSuperficial || 0);
        if (oferta === 0) {
            diasConsecutivos++;
            maxDiasSinAgua = Math.max(maxDiasSinAgua, diasConsecutivos);
        } else {
            diasConsecutivos = 0;
        }
    }
    
    // 3. Oferta neta acumulada
    const sumaSuperficialAcum = datosAcumulados.reduce((sum, d) =>
        sum + parseFloat(d.OfertaSuperficial || 0), 0);

    // 4. Oferta bruta acumulada
    const sumaBrutaAcum = datosAcumulados.reduce((sum, d) =>
        sum + parseFloat(d.OfertaBruta || d.OfertaSuperficial || 0), 0);

    // 5. Pérdida acumulada por posición (bruta − neta)
    const perdidaAcum = sumaBrutaAcum - sumaSuperficialAcum;
    const pctPerdida  = sumaBrutaAcum > 0
        ? (perdidaAcum / sumaBrutaAcum * 100) : 0;

    // Turnos con canal abierto (OfertaBruta > 0)
    const diasTurno = datosAcumulados.filter(d =>
        parseFloat(d.OfertaBruta || d.OfertaSuperficial || 0) > 0).length;
    const perdPorTurno = diasTurno > 0 ? perdidaAcum / diasTurno : 0;

    // 6. Promedio neto por día
    const promedioOfertaAcum = datosAcumulados.length > 0
        ? sumaSuperficialAcum / datosAcumulados.length : 0;

    // Actualizar DOM
    maxSinSuperficial.textContent = maxDiasSinSuperficial;
    diasSinAgua.textContent = maxDiasSinAgua;
    sumaSuperficial.textContent = sumaSuperficialAcum.toFixed(0);
    ofertaTotalDisp.textContent  = sumaBrutaAcum.toFixed(0);
    promedioTotal.textContent    = promedioOfertaAcum.toFixed(2);
    if (perdidaMin)  perdidaMin.textContent  = perdidaAcum.toFixed(1);
    if (perdidaMax)  perdidaMax.textContent  = pctPerdida.toFixed(1);
    if (perdidaProm) perdidaProm.textContent = perdPorTurno.toFixed(2);
}

// Actualizar estadísticas del día actual
function actualizarEstadisticas() {
    if (!datos.length || diaActual < 1 || diaActual > datos.length) return;
    
    const datoDia = datos[diaActual - 1];
    
    dayNumber.textContent = diaActual;
    dayDate.textContent = datoDia.Fecha || '---';
    // Caudal máximo en parámetros (se actualiza desde parametrosGlobales, no aquí)

    accionesHoy.textContent = parseFloat(datoDia.OfertaSuperficial || 0).toFixed(2);
    const perdHoyTotal = parseFloat(datoDia.PerdidaTotal || 0);
    const ofertaBruta  = parseFloat(datoDia.OfertaBruta  || 0);
    const ofertaNeta   = parseFloat(datoDia.OfertaSuperficial || 0);
    // L/s = m³ × 1000 / (12 h × 3600 s/h)
    const SEG_TURNO = 12 * 3600;
    const caudalBrutoVal   = ofertaBruta * 1000 / SEG_TURNO;
    const caudalEfectivoVal = ofertaNeta  * 1000 / SEG_TURNO;
    if (ofertaBrutaM3)    ofertaBrutaM3.textContent    = ofertaBruta.toFixed(2);
    if (perdidaTotalM3)   perdidaTotalM3.textContent   = perdHoyTotal.toFixed(2);
    if (caudalEfectivoLS) caudalEfectivoLS.textContent = caudalEfectivoVal.toFixed(3);
    stockHoy.textContent = parseFloat(datoDia.RecargaSubterranea || 0).toFixed(2);
    stockHoy.textContent = parseFloat(datoDia.RecargaSubterranea || 0).toFixed(2);
    if (desmarqueHoy) desmarqueHoy.textContent = parseFloat(datoDia.PorcentajeDesmarque || 0).toFixed(4) * 100;
    if (turnoActivo) turnoActivo.textContent = datoDia.TurnoActivo ? 'Sí' : 'No';

    // Lógica de apertura del canal
    const turnoVal = parseInt(datoDia.TurnoActivo || 0);
    const paradaVal = parseInt(datoDia.EnParada || 0);
    const aperturaVal = parseInt(datoDia.AperturaCanal || 0);
    actualizarLogicaApertura(turnoVal, paradaVal, aperturaVal);
    
    // Actualizar sliders
    daySlider.value = diaActual;
    dayValue.textContent = `${diaActual} / ${datos.length}`;
    
    // Actualizar barra de progreso
    const progreso = (diaActual / datos.length) * 100;
    progressBar.style.width = progreso + '%';
    
    // Actualizar indicadores dinámicamente
    actualizarIndicadoresDinamicos();
    
    // Cargar variables del estado actual
    cargarVariables();
}

// Crear gráficos con Plotly (2 paneles)
function actualizarGrafico() {
    if (!datos.length) return;
    
    // Datos hasta el día actual
    const datosAhora = datos.slice(0, diaActual);
    const fechas      = datosAhora.map(d => d.Fecha);
    const superficial = datosAhora.map(d => parseFloat(d.OfertaSuperficial || 0));
    // Pérdida por caudal máximo = OfertaBruta - OfertaSuperficial
    const perdida     = datosAhora.map(d =>
        Math.max(0, parseFloat(d.OfertaBruta || 0) - parseFloat(d.OfertaSuperficial || 0))
    );

    // ===== GRÁFICO 1 =====
    const trace1_superficial = {
        x: fechas, y: superficial, type: 'bar',
        marker: { color: 'rgba(37,99,168,0.8)' },
        name: 'Recibido (m³)'
    };
    const trace1_perdida = {
        x: fechas, y: perdida, type: 'bar',
        marker: { color: 'rgba(220,38,38,0.5)' },
        name: 'No recibido — cap posición (m³)'
    };
    
    // Detectar períodos de mantenimiento (EnParada = 1)
    const shapes = [];
    let enParadaInicio = null;
    
    datosAhora.forEach((d, idx) => {
        const enParada = parseInt(d.EnParada || 0);
        
        if (enParada === 1 && enParadaInicio === null) {
            // Inicio de un período de parada
            enParadaInicio = d.Fecha;
        } else if (enParada === 0 && enParadaInicio !== null) {
            // Fin de un período de parada
            shapes.push({
                type: 'rect',
                xref: 'x',
                yref: 'paper',
                x0: enParadaInicio,
                x1: d.Fecha,
                y0: 0,
                y1: 1,
                fillcolor: 'rgba(255, 0, 0, 0.25)',
                line: { color: 'rgba(255, 0, 0, 0.5)', width: 2 }
            });
            enParadaInicio = null;
        }
    });
    
    // Si la parada continúa hasta el final del período
    if (enParadaInicio !== null && datosAhora.length > 0) {
        shapes.push({
            type: 'rect',
            xref: 'x',
            yref: 'paper',
            x0: enParadaInicio,
            x1: fechas[fechas.length - 1],
            y0: 0,
            y1: 1,
            fillcolor: 'rgba(255, 0, 0, 0.25)',
            line: { color: 'rgba(255, 0, 0, 0.5)', width: 2 }
        });
    }
    
    // Rango X progresivo: empieza en día 1 y crece hasta el día actual
    // (mínimo 30 días de ventana para evitar zoom extremo al inicio)
    const xRangeMin = datos[0].Fecha;
    const ultimoDato = datos[datos.length - 1].Fecha;
    const diaActualFecha = datosAhora.length > 0 ? datosAhora[datosAhora.length - 1].Fecha : xRangeMin;
    const MIN_DIAS_VENTANA = 30;
    const xRangeMaxDate = new Date(Math.max(
        new Date(diaActualFecha).getTime() + 7 * 24 * 60 * 60 * 1000,           // día actual + 7 días de margen
        new Date(xRangeMin).getTime() + MIN_DIAS_VENTANA * 24 * 60 * 60 * 1000  // mínimo 30 días
    ));
    // No superar el último día del dataset
    const xRangeMax = new Date(Math.min(xRangeMaxDate.getTime(), new Date(ultimoDato).getTime()))
        .toISOString().split('T')[0];

    const layout1 = {
        title: { text: 'Oferta Superficial por Turno', font: { family: 'Segoe UI, system-ui', size: 13, color: '#1a3d6e' } },
        xaxis: { title: '', type: 'date', range: [xRangeMin, xRangeMax],
                 gridcolor: '#e9eef5', linecolor: '#d1d9e4', tickfont: { family: 'Segoe UI', size: 11, color: '#6b7280' } },
        yaxis: { title: 'm³/turno', gridcolor: '#e9eef5', linecolor: '#d1d9e4',
                 tickfont: { family: 'Segoe UI', size: 11, color: '#6b7280' },
                 titlefont: { family: 'Segoe UI', size: 11, color: '#6b7280' } },
        barmode: 'stack',
        hovermode: 'x unified',
        margin: { l: 50, r: 14, t: 30, b: 34 },
        height: 230,
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        shapes: shapes,
        legend: { orientation: 'h', y: -0.28, font: { family: 'Segoe UI', size: 11, color: '#374151' } },
        font: { family: 'Segoe UI, system-ui' }
    };
    
    Plotly.newPlot(chart1, [trace1_superficial, trace1_perdida], layout1, { responsive: true, displayModeBar: false });
    
    // ===== GRÁFICO 2: RECARGAS SUBTERRÁNEAS =====
    const recargasHoy = datosAhora.filter(d => parseFloat(d.RecargaSubterranea || 0) > 0);
    const recargaFechas = recargasHoy.map(d => d.Fecha);
    const recargaMontos = recargasHoy.map(d => parseFloat(d.RecargaSubterranea));

    // Ancho de barra: 14 días en milisegundos (Plotly usa ms para ejes de fecha)
    const anchoBarraMs = 14 * 24 * 60 * 60 * 1000;

    const trace2_recarga = {
        x: recargaFechas, y: recargaMontos, type: 'bar',
        width: recargaFechas.map(() => anchoBarraMs),
        marker: { color: 'rgba(22,163,74,0.75)', line: { color: 'rgba(22,163,74,1)', width: 1 } },
        name: 'Recarga Subterránea',
        text: recargaMontos.map(m => `+${m.toFixed(0)} m³`),
        textposition: 'outside'
    };

    const maxRecarga = recargaMontos.length > 0 ? Math.max(...recargaMontos) : 50;

    const layout2 = {
        title: { text: 'Recargas de Agua Subterránea', font: { family: 'Segoe UI, system-ui', size: 13, color: '#1a3d6e' } },
        xaxis: { title: '', type: 'date', range: [xRangeMin, xRangeMax],
                 gridcolor: '#e9eef5', linecolor: '#d1d9e4', tickfont: { family: 'Segoe UI', size: 11, color: '#6b7280' } },
        yaxis: { title: 'm³ recargados', range: [0, maxRecarga * 1.45],
                 gridcolor: '#e9eef5', linecolor: '#d1d9e4',
                 tickfont: { family: 'Segoe UI', size: 11, color: '#6b7280' },
                 titlefont: { family: 'Segoe UI', size: 11, color: '#6b7280' } },
        hovermode: 'x unified',
        margin: { l: 50, r: 14, t: 30, b: 34 },
        height: 230,
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        font: { family: 'Segoe UI, system-ui' }
    };

    Plotly.newPlot(chart2, [trace2_recarga], layout2, { responsive: true, displayModeBar: false });
}

// Controles
playBtn.addEventListener('click', () => {
    if (!isPlaying && diaActual <= datos.length) {
        isPlaying = true;
        playBtn.style.opacity = '0.5';
        reproducir();
    }
});

pauseBtn.addEventListener('click', () => {
    isPlaying = false;
    playBtn.style.opacity = '1';
    if (animationInterval) clearInterval(animationInterval);
});

resetBtn.addEventListener('click', () => {
    isPlaying = false;
    playBtn.style.opacity = '1';
    diaActual = 1;
    if (animationInterval) clearInterval(animationInterval);
    actualizarEstadisticas();
    actualizarGrafico();
});

endBtn.addEventListener('click', () => {
    isPlaying = false;
    playBtn.style.opacity = '1';
    diaActual = datos.length;
    if (animationInterval) clearInterval(animationInterval);
    actualizarEstadisticas();
    actualizarGrafico();
});

speedSlider.addEventListener('input', (e) => {
    velocidad = parseFloat(e.target.value);
    speedValue.textContent = velocidad.toFixed(1) + 'x';
});

daySlider.addEventListener('input', (e) => {
    isPlaying = false;
    playBtn.style.opacity = '1';
    if (animationInterval) clearInterval(animationInterval);
    
    diaActual = parseInt(e.target.value);
    actualizarEstadisticas();
    actualizarGrafico();
});

// Cambio de escenario
scenarioSelect.addEventListener('change', (e) => {
    escenarioSeleccionado = parseInt(e.target.value);
    cargarDatos();
});

// Reproducción animada
function reproducir() {
    if (!isPlaying || diaActual > datos.length) {
        isPlaying = false;
        playBtn.style.opacity = '1';
        return;
    }
    
    // Intervalo basado en velocidad (velocidad = 1 → 100ms = 10 días/segundo)
    const intervalo = Math.max(50, 100 / velocidad);
    
    animationInterval = setInterval(() => {
        if (isPlaying && diaActual < datos.length) {
            diaActual++;
            actualizarEstadisticas();
            actualizarGrafico();
        } else if (diaActual >= datos.length) {
            isPlaying = false;
            playBtn.style.opacity = '1';
            if (animationInterval) clearInterval(animationInterval);
        }
    }, intervalo);
}

// Resize de los gráficos
window.addEventListener('resize', () => {
    if (datos.length > 0) {
        Plotly.Plots.resize(chart1);
        Plotly.Plots.resize(chart2);
    }
});

// Inicializar
document.addEventListener('DOMContentLoaded', async () => {
    await cargarEscenarios();
    cargarDatos();
});
