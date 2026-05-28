/* ==========================================================================
   DERMALAI - CORE JS APPLICATION LOGIC (INFERENCE, REGISTRY, SSE PIPELINES)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // 22 clases oficiales en orden alfabético
    const CLASSES = [
        "Acne", "Actinic_Keratosis", "Benign_tumors", "Bullous", "Candidiasis",
        "DrugEruption", "Eczema", "Infestations_Bites", "Lichen", "Lupus",
        "Moles", "Psoriasis", "Rosacea", "Seborrh_Keratoses", "SkinCancer",
        "Sun_Sunlight_Damage", "Tinea", "Unknown_Normal", "Vascular_Tumors",
        "Vasculitis", "Vitiligo", "Warts"
    ];

    // Nombres en español amigables
    const CLASS_NAMES_ES = {
        "Acne": "Acné",
        "Actinic_Keratosis": "Queratosis Actínica",
        "Benign_tumors": "Tumores Benignos (Quistes/Lipomas)",
        "Bullous": "Dermatosis Ampollosa",
        "Candidiasis": "Candidiasis Cutánea",
        "DrugEruption": "Erupción por Medicamento",
        "Eczema": "Eczema / Dermatitis",
        "Infestations_Bites": "Picaduras e Infestaciones",
        "Lichen": "Liken Plano",
        "Lupus": "Lupus Cutáneo",
        "Moles": "Lunares (Nevus)",
        "Psoriasis": "Psoriasis",
        "Rosacea": "Rosácea",
        "Seborrh_Keratoses": "Queratosis Seborreica",
        "SkinCancer": "Sospecha de Cáncer de Piel",
        "Sun_Sunlight_Damage": "Daño Solar / Quemadura",
        "Tinea": "Tiña / Infección por Hongos",
        "Unknown_Normal": "Piel Sana / Normal",
        "Vascular_Tumors": "Tumores Vasculares (Puntos Rubí)",
        "Vasculitis": "Vasculitis Cutánea",
        "Vitiligo": "Vitíligo",
        "Warts": "Verrugas Virales"
    };

    // Referencias DOM
    const uploadZone = document.getElementById("upload-zone");
    const imageInput = document.getElementById("image-input");
    const uploadContent = document.getElementById("upload-content");
    const previewContainer = document.getElementById("preview-container");
    const imagePreview = document.getElementById("image-preview");
    const changeImageBtn = document.getElementById("change-image-btn");
    
    const predictBtn = document.getElementById("predict-btn");
    const diagnosticLoader = document.getElementById("diagnostic-loader");
    const diagnosticResults = document.getElementById("diagnostic-results");
    
    const activeModelBadge = document.getElementById("active-model-badge");
    const modelsTableBody = document.querySelector("#models-table tbody");
    const refreshModelsBtn = document.getElementById("refresh-models-btn");
    
    const driftClassSelect = document.getElementById("drift-class-select");
    const triggerDriftBtn = document.getElementById("trigger-drift-btn");
    const retrainForm = document.getElementById("retrain-form");
    const startRetrainBtn = document.getElementById("start-retrain-btn");
    
    const runCiBtn = document.getElementById("run-ci-btn");
    const clearConsoleBtn = document.getElementById("clear-console-btn");
    const terminalBody = document.getElementById("terminal-body");

    let probabilityChart = null;
    let selectedFile = null;

    // -------------------------------------------------------------
    // 0. NAVEGACIÓN POR PESTAÑAS (TABS INTERACTIVOS)
    // -------------------------------------------------------------
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            // Quitar clase activa de todos los botones y contenidos
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            // Añadir clase activa al botón presionado y contenido destino
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });

    // Inicializaciones
    populateClassesSelect();
    loadModelsRegistry();

    // -------------------------------------------------------------
    // 1. CARGA DE IMÁGENES (DRAG & DROP / SELECT)
    // -------------------------------------------------------------
    uploadZone.addEventListener("click", () => {
        if (!selectedFile) imageInput.click();
    });

    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("dragover");
    });

    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragover");
    });

    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    imageInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    changeImageBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // Evitar click en uploadZone
        resetImageUpload();
    });

    function handleFile(file) {
        if (!file.type.startsWith("image/")) {
            alert("Por favor, sube únicamente archivos de imagen.");
            return;
        }
        selectedFile = file;
        
        // Vista previa
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            uploadContent.style.display = "none";
            previewContainer.style.display = "flex";
            predictBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetImageUpload() {
        selectedFile = null;
        imageInput.value = "";
        imagePreview.src = "#";
        uploadContent.style.display = "block";
        previewContainer.style.display = "none";
        predictBtn.disabled = true;
        diagnosticResults.style.display = "none";
    }

    // -------------------------------------------------------------
    // 2. ENDPOINT DE INFERENCIA (PREDICT)
    // -------------------------------------------------------------
    predictBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        predictBtn.disabled = true;
        diagnosticResults.style.display = "none";
        diagnosticLoader.style.display = "block";
        
        const formData = new FormData();
        formData.append("image", selectedFile);

        logToTerminal("[CLIENTE] Subiendo muestra médica y activando inferencia de 22 clases con modelo TFLite...", "info");

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            diagnosticLoader.style.display = "none";
            predictBtn.disabled = false;

            if (data.success) {
                logToTerminal(`[INFERENCIA OK] Diagnóstico completado. Modelo utilizado: ${data.model_id}. Inferencia real: ${!data.is_fallback}`, "success");
                if (data.is_fallback) {
                    logToTerminal(`[FALLBACK ACTIVADO] Motivo: ${data.fallback_reason}`, "warning");
                }
                
                // Mostrar alerta de MLOps automático si se disparó
                const autoMlopsAlert = document.getElementById("auto-mlops-alert");
                if (data.auto_mlops_triggered) {
                    document.getElementById("auto-mlops-reason").innerText = data.auto_mlops_reason;
                    autoMlopsAlert.style.display = "flex";
                    logToTerminal(`[MLOPS ALERT] ¡Se detectó una muestra biológica con ${data.auto_mlops_reason}!`, "warning");
                    logToTerminal(`[MLOPS AUTOMÁTICO] Iniciando reentrenamiento y verificación CI/CD en segundo plano...`, "info");
                } else {
                    if (autoMlopsAlert) autoMlopsAlert.style.display = "none";
                }
                
                displayDiagnosticResults(data);
            } else {
                logToTerminal(`[ERROR DE INFERENCIA] ${data.error}`, "error");
                alert("Ocurrió un error al procesar la imagen: " + data.error);
            }
        } catch (error) {
            diagnosticLoader.style.display = "none";
            predictBtn.disabled = false;
            logToTerminal(`[ERROR DE CONEXIÓN] No se pudo conectar al servidor de inferencia.`, "error");
            alert("No se pudo conectar al servidor de predicción.");
        }
    });

    function displayDiagnosticResults(data) {
        diagnosticResults.style.display = "block";
        
        const topPred = data.predictions[0];
        
        // Actualizar tarjeta del resultado principal
        document.getElementById("result-title").innerText = topPred.name_es;
        document.getElementById("result-desc").innerText = topPred.description;
        
        // Severidad
        const severityBadge = document.getElementById("result-severity");
        severityBadge.className = "badge-severity"; // reset
        const severityClean = topPred.severity.toLowerCase().replace(" ", "-");
        severityBadge.classList.add(`severity-${severityClean}`);
        severityBadge.innerText = topPred.severity.toUpperCase();

        // Círculo de confianza circular
        const confidencePercentage = Math.round(topPred.probability * 100);
        document.getElementById("result-confidence-text").textContent = `${confidencePercentage}%`;
        const circle = document.getElementById("result-confidence-circle");
        // stroke-dasharray="prob, 100"
        circle.setAttribute("stroke-dasharray", `${confidencePercentage}, 100`);

        // Lista de recomendaciones
        const recommendationsUl = document.getElementById("result-recommendations");
        recommendationsUl.innerHTML = "";
        topPred.recommendations.forEach(rec => {
            const li = document.createElement("li");
            li.innerText = rec;
            recommendationsUl.appendChild(li);
        });

        // Dibujar gráfico horizontal Chart.js con los 5 mejores candidatos
        const top5 = data.predictions.slice(0, 5);
        const chartLabels = top5.map(p => p.name_es);
        const chartData = top5.map(p => p.probability * 100);

        if (probabilityChart) {
            probabilityChart.destroy();
        }

        const ctx = document.getElementById("probabilityChart").getContext("2d");
        probabilityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Confianza (%)',
                    data: chartData,
                    backgroundColor: [
                        'rgba(0, 242, 254, 0.7)',
                        'rgba(0, 242, 254, 0.5)',
                        'rgba(0, 242, 254, 0.3)',
                        'rgba(0, 242, 254, 0.2)',
                        'rgba(255, 255, 255, 0.1)'
                    ],
                    borderColor: [
                        '#00f2fe',
                        '#00f2fe',
                        'rgba(0, 242, 254, 0.6)',
                        'rgba(0, 242, 254, 0.4)',
                        'rgba(255, 255, 255, 0.3)'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#f0f4f9', font: { family: 'Outfit', size: 11 } }
                    }
                }
            }
        });

        // Auto Scroll suave hasta los resultados
        document.querySelector(".diagnostic-card").scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    // -------------------------------------------------------------
    // 3. REGISTRO DE MODELOS (MODEL REGISTRY)
    // -------------------------------------------------------------
    async function loadModelsRegistry() {
        try {
            const response = await fetch("/api/models");
            const models = await response.json();
            
            modelsTableBody.innerHTML = "";
            
            if (models.length === 0) {
                modelsTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No hay modelos en el repositorio.</td></tr>`;
                activeModelBadge.innerText = "Ningún modelo cargado";
                return;
            }

            // Identificar activo
            const activeModel = models.find(m => m.status === "active");
            if (activeModel) {
                activeModelBadge.innerText = `${activeModel.model_id} (v${activeModel.version})`;
            }

            models.forEach(model => {
                const tr = document.createElement("tr");
                
                // Formatear fecha corta
                const dateShort = model.created_at ? model.created_at.substring(0, 10) : "Sin fecha";
                
                // Badge de estado
                const statusBadge = `<span class="badge badge-${model.status}">${model.status}</span>`;
                
                // Botón de acción: Promover si no es activo
                let actionBtn = "";
                if (model.status !== "active") {
                    actionBtn = `
                        <button class="btn btn-secondary btn-sm promote-btn" data-id="${model.model_id}">
                            <i class="fa-solid fa-cloud-arrow-up"></i> Activar
                        </button>`;
                } else {
                    actionBtn = `<span style="color:var(--success-color);font-size:0.75rem;font-weight:600;"><i class="fa-solid fa-circle-check"></i> En Producción</span>`;
                }

                tr.innerHTML = `
                    <td><strong>v${model.version}</strong></td>
                    <td style="font-family:monospace;color:var(--text-secondary);">${model.model_id}</td>
                    <td><strong style="color:var(--primary-color);">${(model.accuracy * 100).toFixed(2)}%</strong></td>
                    <td>${statusBadge}</td>
                    <td>${actionBtn}</td>
                `;
                
                modelsTableBody.appendChild(tr);
            });

            // Asignar listeners a los botones de promover
            document.querySelectorAll(".promote-btn").forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const modelId = e.currentTarget.getAttribute("data-id");
                    await promoteModel(modelId);
                });
            });

        } catch (error) {
            console.error("Error cargando el repositorio de modelos:", error);
            modelsTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--danger-color);">Fallo al conectar con el Registro de Modelos.</td></tr>`;
        }
    }

    async function promoteModel(modelId) {
        logToTerminal(`[REGISTRO] Solicitando promoción/rollback de modelo: ${modelId}...`, "info");
        try {
            const response = await fetch("/api/models/promote", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model_id: modelId })
            });
            const data = await response.json();
            if (data.success) {
                logToTerminal(`[CD] Despliegue de actualización médica completada: ${data.message}`, "success");
                await loadModelsRegistry(); // Recargar tabla
            } else {
                logToTerminal(`[ERROR DE CD] No se pudo promover el modelo: ${data.error}`, "error");
            }
        } catch (error) {
            logToTerminal(`[ERROR DE CD] Falló la petición de despliegue continuo.`, "error");
        }
    }

    refreshModelsBtn.addEventListener("click", () => {
        loadModelsRegistry();
        logToTerminal("[REGISTRO] Repositorio de MLOps sincronizado localmente con éxito.", "info");
    });

    // -------------------------------------------------------------
    // 4. MONITOREO DE DERIVA (DATA DRIFT) & REENTRENAMIENTO (SSE)
    // -------------------------------------------------------------
    function populateClassesSelect() {
        CLASSES.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.innerText = CLASS_NAMES_ES[c] || c;
            driftClassSelect.appendChild(opt);
        });
    }

    triggerDriftBtn.addEventListener("click", async () => {
        const classId = driftClassSelect.value;
        logToTerminal(`[PACIENTE] Nueva muestra biológica reportada para análisis: ${classId}.`, "info");
        
        try {
            const response = await fetch("/api/add-data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ class_id: classId, notes: "Caso clínico desde simulador de deriva" })
            });
            const data = await response.json();
            if (data.success) {
                logToTerminal(`[DRIFT ENGINE] Muestra añadida. Monitoreo clínico: Alerta de deriva en rango crítico para '${CLASS_NAMES_ES[classId]}'.`, "warning");
                // Mostrar la caja de alerta de drift si estaba oculta
                document.getElementById("drift-alert").style.display = "flex";
            }
        } catch (e) {
            console.error(e);
        }
    });

    // REENTRENAMIENTO - EVENT STREAMING (SSE)
    startRetrainBtn.addEventListener("click", () => {
        const epochs = document.getElementById("retrain-epochs").value;
        const lr = document.getElementById("retrain-lr").value;
        
        // Bloquear interfaz
        startRetrainBtn.disabled = true;
        predictBtn.disabled = true;
        clearTerminal();
        
        logToTerminal("[SISTEMA] Disparando pipeline de mantenimiento automatizado asíncrono...", "info");
        logToTerminal("[MLOPS] Conectando con el stream de salida del reentrenamiento...", "info");

        // Creamos FormData
        const formData = new FormData();
        formData.append("epochs", epochs);
        formData.append("lr", lr);

        // Hacemos el fetch que nos devolverá el stream de Server-Sent Events (SSE)
        // SSE nativo usa EventSource pero EventSource no soporta POST de forma nativa.
        // Hacemos POST a la ruta y leemos la respuesta como un stream directo!
        fetch("/api/retrain", {
            method: "POST",
            body: formData
        }).then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        logToTerminal("\n[FIN] Conexión cerrada. Pipeline de reentrenamiento finalizado.", "success");
                        startRetrainBtn.disabled = false;
                        predictBtn.disabled = false;
                        loadModelsRegistry(); // Recargar modelos entrenados
                        return;
                    }
                    
                    const chunk = decoder.decode(value);
                    // SSE envía datos formateados como 'data: text\n\n'
                    const lines = chunk.split("\n\n");
                    lines.forEach(line => {
                        if (line.startsWith("data: ")) {
                            const rawText = line.substring(6);
                            // Limpiar retornos de carro simulados de progreso de TensorFlow
                            if (rawText.includes("\r")) {
                                const sublines = rawText.split("\r");
                                // Mostrar la última sublinea de progreso
                                appendTerminalLine(sublines[sublines.length - 1], "terminal-line");
                            } else {
                                appendTerminalLine(rawText, "terminal-line");
                            }
                        }
                    });
                    
                    readStream(); // Siguiente fragmento
                });
            }

            readStream();
        }).catch(err => {
            logToTerminal(`[ERROR DE COMUNICACIÓN] Falló el stream del reentrenamiento: ${err}`, "error");
            startRetrainBtn.disabled = false;
            predictBtn.disabled = false;
        });
    });

    // -------------------------------------------------------------
    // 5. PIPELINE CI/CD (SSE EVENT STREAMING)
    // -------------------------------------------------------------
    runCiBtn.addEventListener("click", () => {
        runCiBtn.disabled = true;
        clearTerminal();
        
        logToTerminal("[CI/CD ENGINE] Inicializando pipeline automático de Integración Continua...", "info");
        
        fetch("/api/run-ci", {
            method: "POST"
        }).then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readCiStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        logToTerminal("\n[FIN] Pipeline CI/CD completado.", "success");
                        runCiBtn.disabled = false;
                        loadModelsRegistry(); // Recargar modelos promovidos
                        return;
                    }
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split("\n\n");
                    lines.forEach(line => {
                        if (line.startsWith("data: ")) {
                            const text = line.substring(6);
                            
                            // Asignar colores de acuerdo al contenido
                            let lineType = "terminal-line";
                            if (text.includes("[OK]") || text.includes("SUCCESSFUL") || text.includes("passed")) {
                                lineType = "success-line";
                            } else if (text.includes("[ERROR]") || text.includes("FAILED")) {
                                lineType = "error-line";
                            }
                            
                            appendTerminalLine(text, lineType);
                        }
                    });
                    
                    readCiStream();
                });
            }

            readCiStream();
        }).catch(err => {
            logToTerminal(`[ERROR CI/CD] Falló el streaming: ${err}`, "error");
            runCiBtn.disabled = false;
        });
    });

    // -------------------------------------------------------------
    // 6. CONTROLADORES DE TERMINAL CONSOLA
    // -------------------------------------------------------------
    clearConsoleBtn.addEventListener("click", () => {
        clearTerminal();
    });

    function clearTerminal() {
        terminalBody.innerHTML = "";
    }

    function appendTerminalLine(text, className) {
        // Si la línea es de progreso, intentamos actualizar el último nodo si ya existe
        if (text.trim().startsWith("43/") || text.trim().startsWith("86/") || text.trim().includes("━")) {
            const lastLine = terminalBody.lastElementChild;
            if (lastLine && (lastLine.innerText.includes("━") || lastLine.innerText.startsWith("43/") || lastLine.innerText.startsWith("86/"))) {
                lastLine.innerText = text;
                return;
            }
        }
        
        const p = document.createElement("p");
        p.className = `terminal-line ${className}`;
        p.innerText = text;
        terminalBody.appendChild(p);
        
        // Auto-Scroll terminal a la parte inferior
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    function logToTerminal(message, type = "info") {
        let className = "terminal-line";
        if (type === "success") className = "success-line";
        if (type === "warning") className = "terminal-line"; // regular o color warning
        if (type === "error") className = "error-line";
        
        const timestamp = new Date().toISOString().substring(11, 19);
        appendTerminalLine(`[${timestamp}] ${message}`, className);
    }
});
