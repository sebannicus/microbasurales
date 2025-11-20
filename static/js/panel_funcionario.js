(function () {
    const mapaElemento = document.getElementById("mapa-denuncias");
    if (!mapaElemento) {
        return;
    }

    const token = mapaElemento.dataset.token;
    const apiUrl = mapaElemento.dataset.apiUrl;
    const updateUrlTemplate = mapaElemento.dataset.updateUrl || "";
    const updateBaseUrl = updateUrlTemplate.replace(/0\/?$/, "");
    const esFiscalizador = mapaElemento.dataset.esFiscalizador === "true";
    const esAdministrador = mapaElemento.dataset.esAdministrador === "true";
    const jefesCuadrillaUrl = mapaElemento.dataset.jefesUrl || "";
    let jefesCuadrillaCache = [];
    let jefesCuadrillaPromise = null;
    let jefesCuadrillaDatos = [];

    const jefesScript = document.getElementById("jefes-cuadrilla-data");
    if (jefesScript) {
        try {
            const parsed = JSON.parse(jefesScript.textContent || "[]");
            if (Array.isArray(parsed)) {
                jefesCuadrillaDatos = parsed;
            }
        } catch (error) {
            console.warn("No se pudieron cargar los jefes de cuadrilla embebidos", error);
        }
    }

    const ultimaActualizacion = document.getElementById("ultima-actualizacion");
    const filtrosForm = document.getElementById("filtros-form");
    const recargarBtn = document.getElementById("recargar-btn");
    const listaPendientes = document.getElementById("denuncias-pendientes-list");
    const sinDenunciasRow = document.getElementById("sin-denuncias-pendientes");
    const contadorPendientes = document.getElementById("contador-pendientes");
    const sinDenunciasTemplate = sinDenunciasRow ? sinDenunciasRow.cloneNode(true) : null;

    const estadoTabs = document.querySelectorAll(".estado-tab");
    const estadoPaneles = document.querySelectorAll(".estado-panel");

    if (sinDenunciasRow) {
        sinDenunciasRow.remove();
    }

    const listaEnGestion = document.getElementById("denuncias-en-gestion-list");
    const sinEnGestionElemento = document.getElementById("sin-denuncias-en-gestion");
    const contadorEnGestion = document.getElementById("contador-en-gestion");
    const sinEnGestionTemplate = sinEnGestionElemento
        ? sinEnGestionElemento.cloneNode(true)
        : null;

    if (sinEnGestionElemento) {
        sinEnGestionElemento.remove();
    }

    const listaRealizado = document.getElementById("denuncias-realizado-list");
    const sinRealizadoElemento = document.getElementById("sin-denuncias-realizado");
    const contadorRealizados = document.getElementById("contador-realizados");
    const sinRealizadoTemplate = sinRealizadoElemento
        ? sinRealizadoElemento.cloneNode(true)
        : null;

    if (sinRealizadoElemento) {
        sinRealizadoElemento.remove();
    }

    const listaFinalizado = document.getElementById("denuncias-finalizado-list");
    const sinFinalizadoElemento = document.getElementById("sin-denuncias-finalizado");
    const contadorFinalizados = document.getElementById("contador-finalizados");
    const sinFinalizadoTemplate = sinFinalizadoElemento
        ? sinFinalizadoElemento.cloneNode(true)
        : null;

    if (sinFinalizadoElemento) {
        sinFinalizadoElemento.remove();
    }

    const listaRechazadas = document.getElementById("denuncias-rechazadas-list");
    const sinRechazadasElemento = document.getElementById("sin-denuncias-rechazadas");
    const contadorRechazadas = document.getElementById("contador-rechazadas");
    const sinRechazadasTemplate = sinRechazadasElemento
        ? sinRechazadasElemento.cloneNode(true)
        : null;

    if (sinRechazadasElemento) {
        sinRechazadasElemento.remove();
    }

    const rechazoModalElement = document.getElementById("modalRechazoDenuncia");
    const rechazoModal =
        rechazoModalElement && window.bootstrap
            ? new window.bootstrap.Modal(rechazoModalElement)
            : null;
    const rechazoForm = document.getElementById("formRechazoDenuncia");
    const rechazoError = document.getElementById("rechazo-error");
    const motivoRechazoSelect = document.getElementById("motivo_rechazo_select");
    const motivoRechazoComentarioWrapper = document.getElementById(
        "motivoRechazoComentarioWrapper"
    );
    const motivoRechazoComentario = document.getElementById(
        "motivo_rechazo_comentario"
    );
    const rechazoDenunciaIdElemento = rechazoModalElement
        ? rechazoModalElement.querySelector("[data-rechazo-denuncia-id]")
        : null;
    let denunciaRechazoActual = null;
    const denunciasPorId = new Map();
    const denunciasPorEstado = {
        pendiente: [],
        en_gestion: [],
        realizado: [],
        finalizado: [],
        rechazada: [],
    };
    const resumenEstadoConfig = {
        en_gestion: {
            contenedor: listaEnGestion,
            plantilla: sinEnGestionTemplate,
            contador: contadorEnGestion,
        },
        realizado: {
            contenedor: listaRealizado,
            plantilla: sinRealizadoTemplate,
            contador: contadorRealizados,
        },
        finalizado: {
            contenedor: listaFinalizado,
            plantilla: sinFinalizadoTemplate,
            contador: contadorFinalizados,
        },
        rechazada: {
            contenedor: listaRechazadas,
            plantilla: sinRechazadasTemplate,
            contador: contadorRechazadas,
        },
    };

    const estadosConfigElement = document.getElementById("estados-config");
    const DEFAULT_ESTADOS_CONFIG = [
        { value: "pendiente", label: "Pendiente", color: "#d32f2f" },
        { value: "rechazada", label: "Rechazada", color: "#c62828" },
        { value: "en_gestion", label: "En gestión", color: "#f57c00" },
        { value: "realizado", label: "Realizado", color: "#1976d2" },
        { value: "finalizado", label: "Finalizado", color: "#388e3c" },
    ];

    let estadosConfig = DEFAULT_ESTADOS_CONFIG;
    if (estadosConfigElement) {
        try {
            const parsed = JSON.parse(estadosConfigElement.textContent || "");
            if (Array.isArray(parsed) && parsed.length) {
                estadosConfig = parsed;
            }
        } catch (error) {
            console.warn("No fue posible interpretar la configuración de estados", error);
        }
    }

    const estadosMap = new Map(
        estadosConfig.map((estado) => [estado.value, estado])
    );
    const DEFAULT_MARKER_COLOR = "#1d3557";
    const ESTADO_DEFECTO =
        (estadosMap.has("pendiente")
            ? "pendiente"
            : estadosConfig[0] && estadosConfig[0].value) || "pendiente";

    const ESTADOS_EQUIVALENCIAS = new Map([
        ["nuevo", "pendiente"],
        ["nueva", "pendiente"],
        ["nuevos", "pendiente"],
        ["nuevas", "pendiente"],
        ["pendientes", "pendiente"],
        ["en_proceso", "en_gestion"],
        ["en-proceso", "en_gestion"],
        ["enproceso", "en_gestion"],
        ["gestion", "en_gestion"],
        ["rechazada", "rechazada"],
        ["rechazadas", "rechazada"],
        ["rechazado", "rechazada"],
        ["resuelta", "finalizado"],
        ["resueltas", "finalizado"],
        ["resuelto", "finalizado"],
        ["resueltos", "finalizado"],
        ["finalizada", "finalizado"],
        ["finalizadas", "finalizado"],
        ["finalizo", "finalizado"],
        ["finalizados", "finalizado"],
        ["realizada", "realizado"],
        ["realizadas", "realizado"],
        ["realizados", "realizado"],
        ["operativo_realizado", "realizado"],
        ["operativo-realizado", "realizado"],
        ["operativo realizado", "realizado"],
    ]);

    function normalizarEstado(valor) {
        if (!valor) {
            return valor;
        }
        const clave = valor
            .toString()
            .trim()
            .toLowerCase()
            .replace(/[-\s]+/g, "_");
        return ESTADOS_EQUIVALENCIAS.get(clave) || clave;
    }

    function ordenarDenunciasPorFecha(denuncias) {
        denuncias.sort((a, b) => {
            const fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : null;
            const fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : null;

            if (fechaA && fechaB) {
                return fechaA - fechaB;
            }

            if (fechaA) {
                return -1;
            }

            if (fechaB) {
                return 1;
            }

            return 0;
        });
    }

    function obtenerConfigEstado(valor) {
        return estadosMap.get(normalizarEstado(valor));
    }

    function obtenerColorDenuncia(denuncia) {
        if (denuncia && denuncia.color) {
            return denuncia.color;
        }

        const estado = denuncia ? normalizarEstado(denuncia.estado) : null;
        const config = denuncia ? obtenerConfigEstado(estado) : null;
        return (config && config.color) || DEFAULT_MARKER_COLOR;
    }

    function obtenerEtiquetaEstado(denuncia) {
        if (!denuncia) {
            return "";
        }

        if (denuncia.estado_display) {
            return denuncia.estado_display;
        }

        const config = obtenerConfigEstado(denuncia.estado);
        if (config && config.label) {
            return config.label;
        }

        return denuncia.estado;
    }

    function escapeHtml(texto) {
        if (texto === null || texto === undefined) {
            return "";
        }
        return String(texto)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function escapeAttribute(texto) {
        return escapeHtml(texto);
    }

    function construirOpcionesJefes(selectedId = "") {
        const opciones = [
            '<option value="">Seleccione jefe de cuadrilla</option>',
        ];
        jefesCuadrillaDatos.forEach((jefe) => {
            const id = jefe.id;
            const nombre = jefe.full_name || jefe.username || id;
            const seleccionado = String(id) === String(selectedId) ? "selected" : "";
            opciones.push(
                `<option value="${escapeAttribute(id)}" ${seleccionado}>${escapeHtml(
                    nombre
                )}</option>`
            );
        });
        return opciones.join("");
    }

    async function cargarJefesCuadrilla() {
        if (!esFiscalizador || !jefesCuadrillaUrl) {
            return [];
        }

        if (jefesCuadrillaCache.length) {
            return jefesCuadrillaCache.slice();
        }

        if (jefesCuadrillaPromise) {
            return jefesCuadrillaPromise;
        }

        jefesCuadrillaPromise = (async () => {
            try {
                const response = await fetch(jefesCuadrillaUrl, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        Accept: "application/json",
                    },
                });

                if (!response.ok) {
                    console.error("Error cargando jefes:", response.status);
                    return [];
                }

                const data = await response.json();
                jefesCuadrillaCache = Array.isArray(data) ? data : [];
                return jefesCuadrillaCache.slice();
            } catch (error) {
                console.error("Error cargando jefes:", error);
                return [];
            } finally {
                jefesCuadrillaPromise = null;
            }
        })();

        return jefesCuadrillaPromise;
    }

    function prepararSelectorJefe(contenedor) {
        if (!esFiscalizador) {
            return;
        }
        const wrapper = contenedor.querySelector("[data-selector-jefe]");
        if (!wrapper || wrapper.dataset.ready === "true") {
            return;
        }
        wrapper.dataset.ready = "true";
        const lista = wrapper.querySelector("[data-lista-jefes]");
        const loading = wrapper.querySelector("[data-jefes-loading]");
        const inputJefe = wrapper.querySelector(
            'input[name="jefe_cuadrilla_asignado_id"]'
        );
        const inputCuadrilla = wrapper.querySelector(
            'input[name="cuadrilla_asignada"]'
        );
        const seleccionTexto = wrapper.querySelector("[data-jefe-seleccion]");

        if (!lista) {
            return;
        }

        if (!jefesCuadrillaUrl) {
            if (loading) {
                loading.textContent =
                    "No hay jefes de cuadrilla disponibles para asignar.";
            }
            lista.classList.remove("d-none");
            lista.innerHTML =
                "<li class='list-group-item small text-muted'>No hay jefes de cuadrilla configurados.</li>";
            return;
        }

        function actualizarSeleccionVisual(jefe) {
            if (seleccionTexto) {
                const texto = jefe
                    ? `Seleccionado: ${escapeHtml(jefe.username)}`
                    : "Seleccionado: No asignado";
                seleccionTexto.textContent = texto;
            }
            if (inputCuadrilla) {
                inputCuadrilla.value = jefe ? jefe.username : "";
            }
            if (inputJefe) {
                inputJefe.value = jefe ? jefe.id : "";
            }
        }

        lista.addEventListener("click", (event) => {
            const opcion = event.target.closest(".jefe-cuadrilla-opcion");
            if (!opcion) {
                return;
            }
            const jefeId = Number(opcion.dataset.jefeId);
            const jefe = jefesCuadrillaCache.find(
                (item) => Number(item.id) === jefeId
            );
            lista
                .querySelectorAll(".jefe-cuadrilla-opcion")
                .forEach((item) => item.classList.remove("active"));
            opcion.classList.add("active");
            actualizarSeleccionVisual(jefe || null);
        });

        lista.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") {
                return;
            }
            const opcion = event.target.closest(".jefe-cuadrilla-opcion");
            if (!opcion) {
                return;
            }
            event.preventDefault();
            opcion.click();
        });

        cargarJefesCuadrilla()
            .then((jefes) => {
                lista.innerHTML = "";
                if (!jefes.length) {
                    lista.innerHTML =
                        "<li class='list-group-item small text-muted'>No hay jefes de cuadrilla disponibles.</li>";
                } else {
                    const seleccionadoId = inputJefe ? inputJefe.value : "";
                    jefes.forEach((jefe) => {
                        const item = document.createElement("li");
                        item.className =
                            "list-group-item list-group-item-action jefe-cuadrilla-opcion d-flex justify-content-between align-items-center";
                        item.dataset.jefeId = jefe.id;
                        item.tabIndex = 0;
                        item.innerHTML = `<span>${escapeHtml(
                            jefe.username
                        )}</span><span class="text-muted small">#${escapeHtml(
                            jefe.id
                        )}</span>`;
                        if (String(jefe.id) === String(seleccionadoId)) {
                            item.classList.add("active");
                        }
                        lista.appendChild(item);
                    });
                }
                lista.classList.remove("d-none");
                if (loading) {
                    loading.classList.add("d-none");
                }
            })
            .catch(() => {
                lista.innerHTML =
                    "<li class='list-group-item text-danger small'>No se pudo cargar la lista de jefes de cuadrilla.</li>";
                lista.classList.remove("d-none");
                if (loading) {
                    loading.classList.add("d-none");
                }
            });
    }

    function obtenerOpcionesEstadoParaUsuario(denuncia) {
        const estadoActual = normalizarEstado(denuncia.estado);
        if (esAdministrador) {
            if (estadoActual === "realizado") {
                return [estadoActual, "finalizado"];
            }
            return [estadoActual];
        }

        if (esFiscalizador) {
            if (estadoActual === "pendiente") {
                return [estadoActual, "en_gestion"];
            }
            if (estadoActual === "en_gestion") {
                return [estadoActual, "realizado"];
            }
            return [estadoActual];
        }

        return [estadoActual];
    }

    function obtenerTextoAyudaEstado(estadoActual) {
        if (esAdministrador && estadoActual === "realizado") {
            return "Al finalizar se notificará automáticamente al denunciante.";
        }
        if (esAdministrador && estadoActual !== "realizado") {
            return "Solo puedes finalizar denuncias marcadas como realizadas.";
        }
        if (esFiscalizador && estadoActual === "realizado") {
            return "Pendiente de revisión administrativa para cierre definitivo.";
        }
        if (esFiscalizador && estadoActual === "en_gestion") {
            return "Debes adjuntar el reporte de cuadrilla antes de marcarla como realizada.";
        }
        return "";
    }

    function activarTab(estadoObjetivo) {
        if (!estadoObjetivo) {
            estadoObjetivo = ESTADO_DEFECTO;
        }

        const estadoExiste = Array.from(estadoTabs).some(
            (tab) => tab.dataset.estado === estadoObjetivo
        );

        const estadoActivo = estadoExiste ? estadoObjetivo : ESTADO_DEFECTO;

        estadoTabs.forEach((tab) => {
            if (tab.dataset.estado === estadoActivo) {
                tab.classList.add("active");
            } else {
                tab.classList.remove("active");
            }
        });

        estadoPaneles.forEach((panel) => {
            if (panel.dataset.estado === estadoActivo) {
                panel.classList.remove("d-none");
                panel.classList.add("active");
            } else {
                panel.classList.add("d-none");
                panel.classList.remove("active");
            }
        });
    }

    estadoTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            activarTab(tab.dataset.estado);
        });
    });

    const map = L.map("mapa-denuncias", {
        scrollWheelZoom: true,
    }).setView([-33.4507, -70.6671], 14);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);
    const marcadoresPorId = new Map();
    let filtrosActivos = {};

    function obtenerCSRFToken() {
        const nombre = "csrftoken";
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (const cookie of cookies) {
            const partes = cookie.trim().split("=");
            const clave = partes.shift();
            if (clave === nombre) {
                return decodeURIComponent(partes.join("="));
            }
        }

        return null;
    }

    const MOTIVOS_RECHAZO_TEXTOS = {
        foto_insuficiente:
            "La denuncia no puede procesarse: evidencia insuficiente (foto poco clara).",
        no_verificada: "No se logró verificar el microbasural en terreno.",
        datos_insuficientes:
            "El reporte no contiene datos suficientes para acudir al lugar.",
        ya_gestionada:
            "La denuncia ya está siendo gestionada bajo otro caso activo. (denuncia duplicada)",
    };
    const MOTIVOS_RECHAZO_PREDEFINIDOS = new Set(
        Object.values(MOTIVOS_RECHAZO_TEXTOS)
    );

    async function enviarActualizacionDenuncia(denunciaId, payload) {
        const csrfToken = obtenerCSRFToken();
        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            Accept: "application/json",
        };

        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken;
        }

        const respuesta = await fetch(`${updateBaseUrl}${denunciaId}/`, {
            method: "PATCH",
            headers,
            credentials: "same-origin",
            body: JSON.stringify(payload),
        });

        if (!respuesta.ok) {
            const detalle = await extraerMensajeDeError(respuesta);
            throw new Error(detalle);
        }
    }

    async function cargarDenuncias(filtros = {}) {
        filtrosActivos = filtros;
        markerLayer.clearLayers();
        marcadoresPorId.clear();
        denunciasPorId.clear();
        Object.keys(denunciasPorEstado).forEach((estado) => {
            denunciasPorEstado[estado] = [];
        });

        try {
            const parametros = new URLSearchParams();
            Object.entries(filtros)
                .filter(([, value]) => value)
                .forEach(([clave, valor]) => parametros.append(clave, valor));

            let paginaUrl = new URL(apiUrl);
            paginaUrl.search = parametros.toString();

            const bounds = [];
            const pendientes = [];
            const enGestion = [];
            const realizados = [];
            const finalizados = [];
            const rechazadas = [];

            while (paginaUrl) {
                const respuesta = await fetch(paginaUrl.toString(), {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        Accept: "application/json",
                    },
                    credentials: "same-origin",
                });

                if (!respuesta.ok) {
                    throw new Error("No fue posible obtener las denuncias");
                }

                const data = await respuesta.json();
                (data.results || []).forEach((denuncia) => {
                    agregarMarcador(denuncia, bounds);
                    denunciasPorId.set(Number(denuncia.id), denuncia);
                    const estadoNormalizado = normalizarEstado(denuncia.estado);
                    if (estadoNormalizado === "pendiente") {
                        pendientes.push(denuncia);
                    } else if (estadoNormalizado === "en_gestion") {
                        enGestion.push(denuncia);
                    } else if (estadoNormalizado === "realizado") {
                        realizados.push(denuncia);
                    } else if (estadoNormalizado === "finalizado") {
                        finalizados.push(denuncia);
                    } else if (estadoNormalizado === "rechazada") {
                        rechazadas.push(denuncia);
                    }
                });

                if (data.next) {
                    paginaUrl = new URL(data.next);
                } else {
                    paginaUrl = null;
                }
            }

            ordenarDenunciasPorFecha(pendientes);
            ordenarDenunciasPorFecha(enGestion);
            ordenarDenunciasPorFecha(realizados);
            ordenarDenunciasPorFecha(finalizados);
            ordenarDenunciasPorFecha(rechazadas);

            denunciasPorEstado.pendiente = pendientes.slice();
            denunciasPorEstado.en_gestion = enGestion.slice();
            denunciasPorEstado.realizado = realizados.slice();
            denunciasPorEstado.finalizado = finalizados.slice();
            denunciasPorEstado.rechazada = rechazadas.slice();

            ajustarMapa(bounds);
            actualizarMarcaDeTiempo();
            renderEstado("pendiente");
            renderEstado("en_gestion");
            renderEstado("realizado");
            renderEstado("finalizado");
            renderEstado("rechazada");
            activarTab(normalizarEstado(filtros.estado));
        } catch (error) {
            console.error(error);
            mostrarMensajeGlobal(
                "No se pudieron cargar las denuncias. Intenta nuevamente.",
                "danger"
            );
            renderEstado("pendiente");
            renderEstado("en_gestion");
            renderEstado("realizado");
            renderEstado("finalizado");
            renderEstado("rechazada");
        }
    }

    function agregarMarcador(denuncia, bounds) {
        if (!denuncia.latitud || !denuncia.longitud) {
            return;
        }

        const color = obtenerColorDenuncia(denuncia);

        const marker = L.circleMarker([denuncia.latitud, denuncia.longitud], {
            radius: 16,
            fillColor: color,
            color: "#ffffff",
            weight: 3,
            fillOpacity: 1,
        });

        marker.bindPopup(construirPopup(denuncia));
        markerLayer.addLayer(marker);
        marcadoresPorId.set(Number(denuncia.id), marker);
        bounds.push([denuncia.latitud, denuncia.longitud]);
    }

    function construirPopup(denuncia) {
        const wrapper = document.createElement("div");
        wrapper.className = "popup-denuncia";
        wrapper.dataset.id = denuncia.id;

        const detalle = renderDenuncia(denuncia, { mostrarAcciones: false });
        detalle.classList.add("mb-3");
        wrapper.appendChild(detalle);

        const jefeAsignado = denuncia.jefe_cuadrilla_asignado || null;
        const jefeAsignadoTexto = jefeAsignado
            ? `${escapeHtml(jefeAsignado.username)}`
            : "No asignado";
        const cuadrilla =
            denuncia.cuadrilla_asignada ||
            (jefeAsignado && jefeAsignado.username) ||
            "";
        const estadoActual = normalizarEstado(denuncia.estado);
        const estadoOptions = obtenerOpcionesEstadoParaUsuario(denuncia);
        const selectDisabled = estadoOptions.length <= 1;
        const estadoSelectOptions = estadoOptions
            .map((value) => {
                const config = obtenerConfigEstado(value) || {};
                const label = config.label || value;
                const selected = value === estadoActual ? "selected" : "";
                return `<option value="${value}" ${selected}>${label}</option>`;
            })
            .join("");
        const estadoHelpText = obtenerTextoAyudaEstado(estadoActual);
        let reporteCuadrilla = denuncia.reporte_cuadrilla || "";
        if (reporteCuadrilla && typeof reporteCuadrilla === "object") {
            reporteCuadrilla = reporteCuadrilla.comentario || "";
        }
        const puedeEditarReporte = esFiscalizador && estadoActual === "en_gestion";
        const reporteHelpText = puedeEditarReporte
            ? "Adjunta la información entregada por la cuadrilla municipal."
            : "";
        const reporteAtributos = puedeEditarReporte ? "" : "readonly";
        const fecha = denuncia.fecha_creacion
            ? new Date(denuncia.fecha_creacion).toLocaleString("es-CL")
            : "Fecha no disponible";
        const puedeRechazarDenuncia =
            esFiscalizador &&
            (estadoActual === "pendiente" || estadoActual === "en_gestion");
        const botonRechazoHtml = puedeRechazarDenuncia
            ? `<button type="button" class="btn btn-outline-danger btn-sm w-100 mt-2 btn-rechazar-denuncia" data-denuncia-id="${escapeAttribute(
                  denuncia.id
              )}">Rechazar denuncia</button>`
            : "";

        const selectorCuadrilla = esFiscalizador
            ? `
                    <div class="mb-2" data-selector-jefe>
                        <label class="form-label">Cuadrilla asignada</label>
                        <input type="hidden" name="cuadrilla_asignada" value="${escapeAttribute(
                            cuadrilla
                        )}">
                        <input type="hidden" name="jefe_cuadrilla_asignado_id" value="${
                            jefeAsignado ? escapeAttribute(jefeAsignado.id) : ""
                        }">
                        <div class="accordion accordion-flush">
                            <div class="accordion-item">
                                <h2 class="accordion-header" id="heading-jefe-${escapeAttribute(
                                    denuncia.id
                                )}">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#selector-jefe-${escapeAttribute(
                                        denuncia.id
                                    )}" aria-expanded="false">
                                        Seleccionar jefe de cuadrilla
                                    </button>
                                </h2>
                                <div id="selector-jefe-${escapeAttribute(
                                    denuncia.id
                                )}" class="accordion-collapse collapse">
                                    <div class="accordion-body">
                                        <div class="small text-muted mb-2" data-jefe-seleccion>Seleccionado: ${
                                            jefeAsignadoTexto
                                        }</div>
                                        <div id="lista-jefes">
                                            <div class="text-center small text-muted" data-jefes-loading>Cargando jefes de cuadrilla...</div>
                                            <ul class="list-group list-group-flush d-none" data-lista-jefes></ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>`
            : `
                    <div class="mb-2">
                        <label class="form-label">Jefe de cuadrilla asignado</label>
                        <p class="form-control-plaintext mb-0">${jefeAsignadoTexto}</p>
                    </div>`;

        wrapper.insertAdjacentHTML(
            "beforeend",
            `
                <form class="update-form" data-estado-actual="${estadoActual}">
                    <div class="mb-2">
                        <label class="form-label">Actualizar estado</label>
                        <select class="form-select form-select-sm" name="estado" ${
                            selectDisabled ? "disabled" : ""
                        }>
                            ${estadoSelectOptions}
                        </select>
                        ${
                            estadoHelpText
                                ? `<div class="form-text text-muted">${estadoHelpText}</div>`
                                : ""
                        }
                    </div>
                    ${selectorCuadrilla}
                    <div class="mb-2 reporte-cuadrilla-group">
                        <label class="form-label">Reporte de cuadrilla</label>
                        <textarea class="form-control form-control-sm" name="reporte_cuadrilla" ${reporteAtributos}>${escapeHtml(
                            reporteCuadrilla
                        )}</textarea>
                        ${
                            reporteHelpText
                                ? `<div class="form-text text-muted">${reporteHelpText}</div>`
                                : ""
                        }
                    </div>
                    <button type="submit" class="btn btn-sm btn-background w-100">Guardar cambios</button>
                </form>
                ${botonRechazoHtml}
                <div class="small text-muted mt-2">Reportado el ${fecha}</div>
                <div class="feedback mt-2"></div>
            `
        );

        return wrapper.outerHTML;
    }

    function actualizarTablaPendientes(denuncias) {
        if (!listaPendientes) {
            return;
        }

        listaPendientes.innerHTML = "";

        if (!denuncias.length) {
            if (sinDenunciasTemplate) {
                const vacio = sinDenunciasTemplate.cloneNode(true);
                vacio.id = "";
                listaPendientes.appendChild(vacio);
            }
            actualizarContador(contadorPendientes, denuncias.length);
            return;
        }

        if (!esFiscalizador) {
            denuncias.forEach((denuncia) => {
                listaPendientes.appendChild(renderDenuncia(denuncia));
            });
            actualizarContador(contadorPendientes, denuncias.length);
            return;
        }

        const accordion = document.createElement("div");
        accordion.className = "accordion";
        accordion.id = "pendientes-accordion";

        denuncias.forEach((denuncia) => {
            accordion.appendChild(construirAccordionPendiente(denuncia));
        });

        listaPendientes.appendChild(accordion);
        prepararAsignacionPendientes(accordion);

        actualizarContador(contadorPendientes, denuncias.length);
    }

    function prepararAsignacionPendientes(contenedor) {
        if (!esFiscalizador) {
            return;
        }

        contenedor.querySelectorAll(".asignar-btn").forEach((boton) => {
            if (boton.dataset.listenerAttached === "true") {
                return;
            }

            boton.dataset.listenerAttached = "true";
            boton.addEventListener("click", async () => {
                const denunciaId = boton.dataset.denunciaId;
                const item = boton.closest(".accordion-item");
                const select = item
                    ? item.querySelector(
                          ".jefe-cuadrilla-select[data-denuncia-id='" +
                              denunciaId +
                              "']"
                      )
                    : null;
                const errorElemento = item
                    ? item.querySelector(
                          "[data-error-denuncia='" + denunciaId + "']"
                      )
                    : null;
                const jefeId = select ? select.value : "";

                if (errorElemento) {
                    errorElemento.textContent = "";
                    errorElemento.classList.add("d-none");
                }

                if (!jefeId) {
                    if (errorElemento) {
                        errorElemento.textContent =
                            "Debe seleccionar un jefe de cuadrilla antes de asignar.";
                        errorElemento.classList.remove("d-none");
                    }
                    return;
                }

                const textoOriginal = boton.textContent;
                boton.disabled = true;
                boton.textContent = "Asignando...";

                try {
                    await enviarActualizacionDenuncia(denunciaId, {
                        estado: "en_gestion",
                        jefe_cuadrilla_asignado_id: Number(jefeId),
                    });
                    mostrarMensajeGlobal(
                        "Denuncia asignada y marcada en gestión correctamente.",
                        "success"
                    );
                    cargarDenuncias(filtrosActivos);
                } catch (error) {
                    if (errorElemento) {
                        errorElemento.textContent =
                            error.message ||
                            "No se pudo asignar la denuncia en este momento.";
                        errorElemento.classList.remove("d-none");
                    }
                } finally {
                    boton.disabled = false;
                    boton.textContent = textoOriginal;
                }
            });
        });
    }

    function puedeEditarDenuncia(denuncia) {
        const estadoActual = normalizarEstado(denuncia.estado);
        if (esAdministrador) {
            return estadoActual === "realizado";
        }
        if (esFiscalizador) {
            return estadoActual === "pendiente" || estadoActual === "en_gestion";
        }
        return false;
    }

    function renderDenuncia(denuncia, opciones = {}) {
        const { mostrarAcciones = true } = opciones;
        const item = document.createElement("article");
        item.className = "denuncia-card";
        item.dataset.denunciaId = String(denuncia.id);
        item.innerHTML = construirDenunciaHtml(denuncia);

        if (mostrarAcciones) {
            const acciones = document.createElement("div");
            acciones.className = "denuncia-card__actions";

            const btnVer = document.createElement("button");
            btnVer.type = "button";
            btnVer.className = "btn btn-outline-secondary btn-sm";
            btnVer.textContent = "Ver en mapa";
            btnVer.addEventListener("click", () => {
                centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: false });
            });
            acciones.appendChild(btnVer);

            if (puedeEditarDenuncia(denuncia)) {
                const btnEditar = document.createElement("button");
                btnEditar.type = "button";
                btnEditar.className = "btn btn-background btn-sm";
                btnEditar.textContent = "Editar";
                btnEditar.addEventListener("click", () => {
                    centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: true });
                });
                acciones.appendChild(btnEditar);
            }

            item.appendChild(acciones);
        }

        return item;
    }

    function construirAccordionPendiente(denuncia) {
        const headingId = `pendiente-heading-${escapeAttribute(denuncia.id)}`;
        const collapseId = `pendiente-collapse-${escapeAttribute(denuncia.id)}`;
        const item = document.createElement("div");
        item.className = "accordion-item";
        const descripcion = escapeHtml(
            denuncia.descripcion || "Sin descripción registrada"
        );
        const jefeActual =
            (denuncia.jefe_cuadrilla_asignado &&
                denuncia.jefe_cuadrilla_asignado.id) || "";

        item.innerHTML = `
            <h2 class="accordion-header" id="${headingId}">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="false" aria-controls="${collapseId}">
                    Caso #${escapeHtml(denuncia.id)} - ${descripcion}
                </button>
            </h2>
            <div id="${collapseId}" class="accordion-collapse collapse" aria-labelledby="${headingId}" data-bs-parent="#pendientes-accordion">
                <div class="accordion-body d-flex flex-column gap-3">
                    ${construirDenunciaHtml(denuncia)}
                    <div class="d-flex flex-column flex-lg-row gap-2 align-items-lg-center">
                        <select class="form-select jefe-cuadrilla-select" data-denuncia-id="${escapeAttribute(
                            denuncia.id
                        )}">
                            ${construirOpcionesJefes(jefeActual)}
                        </select>
                        <button class="btn btn-primary asignar-btn" data-denuncia-id="${escapeAttribute(
                            denuncia.id
                        )}">Asignar y marcar en gestión</button>
                        <div class="text-danger small d-none" data-error-denuncia="${escapeAttribute(
                            denuncia.id
                        )}"></div>
                    </div>
                </div>
            </div>
        `;

        return item;
    }

    function construirDenunciaHtml(denuncia) {
        const estadoNormalizado = normalizarEstado(denuncia.estado);  
        const color = obtenerColorDenuncia(denuncia);
        const estadoEtiqueta = escapeHtml(obtenerEtiquetaEstado(denuncia));
        const fecha = formatearFecha(denuncia.fecha_creacion);
        const descripcion = escapeHtml(
            denuncia.descripcion || "Sin descripción registrada"
        );
        const zona = escapeHtml(denuncia.zona || "No asignada");
        const direccionTextual = escapeHtml(
            denuncia.direccion_textual || "Sin referencia del denunciante"
        );
        const coordenadas = formatearCoordenadas(
            denuncia.latitud,
            denuncia.longitud
        );
        const latitudTexto =
            denuncia.latitud === 0 || denuncia.latitud
                ? escapeHtml(denuncia.latitud)
                : "-";
        const longitudTexto =
            denuncia.longitud === 0 || denuncia.longitud
                ? escapeHtml(denuncia.longitud)
                : "-";
        const usuario = denuncia.usuario || {};
        const denuncianteNombre = usuario.nombre
            ? escapeHtml(usuario.nombre)
            : "Sin registro";
        const denuncianteRol = usuario.rol
            ? escapeHtml(usuario.rol)
            : "Sin registro";
        const denuncianteId =
            usuario.id === 0 || usuario.id
                ? `#${escapeHtml(usuario.id)}`
                : "-";
        const jefeAsignado = denuncia.jefe_cuadrilla_asignado || null;
        const jefeAsignadoTexto = jefeAsignado
            ? `${escapeHtml(jefeAsignado.username)}`
            : "No asignado";
        const cuadrilla = escapeHtml(
            denuncia.cuadrilla_asignada ||
                (jefeAsignado && jefeAsignado.username) ||
                "No asignada"
        );
        const reporte = denuncia.reporte_cuadrilla || null;
        const reporteId = reporte && (reporte.id === 0 || reporte.id)
            ? `#${escapeHtml(reporte.id)}`
            : "-";
        const reporteComentario = escapeHtml(
            (reporte && reporte.comentario) || "Sin comentario registrado"
        );
        const reporteFecha =
            reporte && reporte.fecha_reporte
                ? formatearFecha(reporte.fecha_reporte)
                : "-";
        const jefeCuadrilla = reporte && reporte.jefe_cuadrilla
            ? escapeHtml(
                  reporte.jefe_cuadrilla.nombre || "Sin nombre registrado"
              )
            : "Sin registro";
        const evidenciaDenuncia = denuncia.imagen
            ? `<figure class="denuncia-card__image-large"><img src="${escapeAttribute(
                  denuncia.imagen
              )}" alt="Evidencia fotográfica de la denuncia" loading="lazy"><figcaption>Registro del denunciante</figcaption></figure>`
            : "";
        const evidenciaReporte =
            reporte && reporte.foto_trabajo
                ? `<figure class="denuncia-card__image-large"><img src="${escapeAttribute(
                      reporte.foto_trabajo
                  )}" alt="Registro fotográfico de la cuadrilla" loading="lazy"><figcaption>Reporte de cuadrilla</figcaption></figure>`
                : "";
        const galeriaHtml = evidenciaDenuncia || evidenciaReporte
            ? `<div class="denuncia-card__gallery">${evidenciaDenuncia}${evidenciaReporte}</div>`
            : `<div class="denuncia-card__gallery denuncia-card__gallery--empty">Sin material fotográfico disponible.</div>`;
        const reporteFotoHtml =
            reporte && reporte.foto_trabajo
                ? `<div class="denuncia-card__report-photo"><img src="${escapeAttribute(
                      reporte.foto_trabajo
                  )}" alt="Foto del trabajo de cuadrilla" loading="lazy"></div>`
                : "";
        const reporteDetalleHtml = reporte
            ? `<ul class="denuncia-card__detail-list">
                    <li><span>ID reporte</span><strong>${reporteId}</strong></li>
                    <li><span>Fecha</span><strong>${reporteFecha}</strong></li>
                    <li><span>Jefe de cuadrilla</span><strong>${jefeCuadrilla}</strong></li>
                    <li><span>Comentario</span><strong>${reporteComentario}</strong></li>
                </ul>
                ${reporteFotoHtml}`
            : `<p class="text-muted mb-0">Sin reporte registrado.</p>`;
        const miniaturaFuente = denuncia.imagen
            ? denuncia.imagen
            : reporte && reporte.foto_trabajo
              ? reporte.foto_trabajo
              : null;
        const miniaturaHtml = miniaturaFuente
            ? `<img src="${escapeAttribute(
                  miniaturaFuente
              )}" alt="Vista previa del caso ${escapeAttribute(denuncia.id)}" loading="lazy">`
            : `<div class="denuncia-card__thumb-placeholder">Sin imagen</div>`;
        const esRechazada = estadoNormalizado === "rechazada";
        const motivoRechazoBruto = (denuncia.motivo_rechazo || "").trim();
        const motivoRechazoHtml = escapeHtml(
            motivoRechazoBruto || "No disponible"
        );
        const estadoMotivoInline =
            esRechazada && motivoRechazoBruto
                ? `<small class="denuncia-card__estado-motivo">Motivo: ${motivoRechazoHtml}</small>`
                : "";
        const comentarioLibreDetalle =
            esRechazada && motivoRechazoBruto
            && !MOTIVOS_RECHAZO_PREDEFINIDOS.has(motivoRechazoBruto)
                ? escapeHtml(motivoRechazoBruto)
                : "No aplica";
        const resumenMotivoRechazoHtml =
            esRechazada && motivoRechazoBruto
                ? `<li class="denuncia-card__summary-item">
                        <span class="denuncia-card__summary-label">Motivo del rechazo</span>
                        <span class="denuncia-card__summary-value">${escapeHtml(
                            motivoRechazoBruto
                        )}</span>
                    </li>`
                : "";
        const rechazoDetalleHtml = esRechazada
            ? `<section class="denuncia-card__detail-group">
                    <h6>Resumen del rechazo</h6>
                    <ul class="denuncia-card__detail-list">
                        <li><span>Motivo del rechazo</span><strong>${motivoRechazoHtml}</strong></li>
                        <li><span>Comentario libre</span><strong>${comentarioLibreDetalle}</strong></li>
                    </ul>
                </section>`
            : "";

        return `
            <header class="denuncia-card__header">
                <div>
                    <div class="denuncia-card__case">
                        <span class="denuncia-card__case-id">Caso #${escapeHtml(
                            denuncia.id
                        )}</span>
                        <span class="denuncia-card__estado" style="background-color: ${escapeAttribute(
                            color
                        )};">${estadoEtiqueta}</span>
                        ${estadoMotivoInline}
                    </div>
                    <div class="denuncia-card__meta">Reportado el ${fecha}</div>
                </div>
            </header>
            <div class="denuncia-card__summary">
                <div>
                    <p class="denuncia-card__description">${descripcion}</p>
                    <ul class="denuncia-card__summary-list">
                        <li class="denuncia-card__summary-item">
                            <span class="denuncia-card__summary-label">Zona</span>
                            <span class="denuncia-card__summary-value">${zona}</span>
                        </li>
                        <li class="denuncia-card__summary-item">
                            <span class="denuncia-card__summary-label">Denunciante</span>
                            <span class="denuncia-card__summary-value">${denuncianteNombre}</span>
                        </li>
                        <li class="denuncia-card__summary-item">
                            <span class="denuncia-card__summary-label">Jefe asignado</span>
                            <span class="denuncia-card__summary-value">${jefeAsignadoTexto}</span>
                        </li>
                        ${resumenMotivoRechazoHtml}
                    </ul>
                </div>
                <div class="denuncia-card__thumb">
                    ${miniaturaHtml}
                </div>
            </div>
            <details class="denuncia-card__details">
                <summary class="denuncia-card__details-toggle"><span>Ver detalles</span></summary>
                <div class="denuncia-card__details-content">
                    <div class="denuncia-card__details-grid">
                        <section class="denuncia-card__detail-group">
                            <h6>Datos del denunciante</h6>
                            <ul class="denuncia-card__detail-list">
                                <li><span>Nombre</span><strong>${denuncianteNombre}</strong></li>
                                <li><span>Rol</span><strong>${denuncianteRol}</strong></li>
                                <li><span>ID usuario</span><strong>${denuncianteId}</strong></li>
                                <li><span>Referencia del denunciante</span><strong>${direccionTextual}</strong></li>
                            </ul>
                        </section>
                        <section class="denuncia-card__detail-group">
                            <h6>Ubicación y coordenadas</h6>
                            <ul class="denuncia-card__detail-list">
                                <li><span>Coordenadas</span><strong>${
                                    coordenadas
                                        ? escapeHtml(coordenadas)
                                        : "Sin coordenadas disponibles"
                                }</strong></li>
                                <li><span>Latitud</span><strong>${latitudTexto}</strong></li>
                                <li><span>Longitud</span><strong>${longitudTexto}</strong></li>
                                <li><span>Referencia textual</span><strong>${direccionTextual}</strong></li>
                            </ul>
                        </section>
                        <section class="denuncia-card__detail-group">
                            <h6>Estado de la denuncia</h6>
                            <ul class="denuncia-card__detail-list">
                                <li><span>Estado actual</span><strong>${estadoEtiqueta}</strong></li>
                                <li><span>Cuadrilla asignada</span><strong>${cuadrilla}</strong></li>
                                <li><span>Jefe designado</span><strong>${jefeAsignadoTexto}</strong></li>
                            </ul>
                        </section>
                        <section class="denuncia-card__detail-group">
                            <h6>Reporte de cuadrilla</h6>
                            ${reporteDetalleHtml}
                        </section>
                    </div>
                    ${galeriaHtml}
                </div>
            </details>
        `;
    }

    function centrarDenunciaEnMapa(denunciaId, { enfocarFormulario = false } = {}) {
        const marker = marcadoresPorId.get(Number(denunciaId));

        if (!marker) {
            mostrarMensajeGlobal(
                "No encontramos la denuncia seleccionada en el mapa actual.",
                "warning"
            );
            return;
        }

        const latLng = marker.getLatLng();
        map.setView(latLng, Math.max(map.getZoom(), 15), { animate: true });
        marker.openPopup();

        if (enfocarFormulario) {
            setTimeout(() => {
                const popup = marker.getPopup();
                if (!popup) {
                    return;
                }
                const popupElement = popup.getElement();
                if (!popupElement) {
                    return;
                }
                const primerCampo = popupElement.querySelector(
                    ".update-form select, .update-form input"
                );
                if (primerCampo) {
                    primerCampo.focus();
                }
            }, 300);
        }
    }

    function actualizarResumenEstado(
        denuncias,
        contenedor,
        plantillaVacia,
        contadorElemento
    ) {
        if (!contenedor) {
            return;
        }

        contenedor.innerHTML = "";

        if (!denuncias.length) {
            if (plantillaVacia) {
                const vacio = plantillaVacia.cloneNode(true);
                vacio.id = "";
                contenedor.appendChild(vacio);
            }
        } else {
            denuncias.forEach((denuncia) => {
                contenedor.appendChild(renderDenuncia(denuncia));
            });
        }

        actualizarContador(contadorElemento, denuncias.length);
    }

    function renderEstado(estado) {
        const coleccion = denunciasPorEstado[estado] || [];
        if (estado === "pendiente") {
            actualizarTablaPendientes(coleccion);
            return;
        }
        const config = resumenEstadoConfig[estado];
        if (!config) {
            return;
        }
        actualizarResumenEstado(
            coleccion,
            config.contenedor,
            config.plantilla,
            config.contador
        );
    }

    function actualizarContador(elemento, total) {
        if (!elemento) {
            return;
        }
        elemento.textContent = `${total}`;
        elemento.setAttribute(
            "title",
            `${total} ${total === 1 ? "caso" : "casos"}`
        );
        elemento.setAttribute(
            "aria-label",
            `${total} ${total === 1 ? "caso" : "casos"}`
        );
    }

    function formatearFecha(fechaIso) {
        if (!fechaIso) {
            return "-";
        }
        const fecha = new Date(fechaIso);
        if (Number.isNaN(fecha.getTime())) {
            return "-";
        }
        return fecha.toLocaleString("es-CL", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatearCoordenadas(latitud, longitud) {
        const lat = Number(latitud);
        const lng = Number(longitud);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            return null;
        }
        return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    }

    function ajustarMapa(bounds) {
        if (!bounds.length) {
            return;
        }
        const leafletBounds = L.latLngBounds(bounds);
        map.fitBounds(leafletBounds, { padding: [10, 10] });
    }

    function actualizarMarcaDeTiempo() {
        if (ultimaActualizacion) {
            ultimaActualizacion.textContent = new Date().toLocaleTimeString("es-CL");
        }
    }

    function mostrarMensajeGlobal(mensaje, tipo = "info") {
        const contenedor = document.createElement("div");
        contenedor.className = `alert alert-${tipo} alert-dismissible fade show mt-3`;
        contenedor.setAttribute("role", "alert");
        contenedor.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;
        mapaElemento.insertAdjacentElement("afterend", contenedor);
        setTimeout(() => {
            contenedor.remove();
        }, 6000);
    }

    function mostrarErrorRechazo(mensaje) {
        if (!rechazoError) {
            return;
        }
        rechazoError.textContent = mensaje;
        rechazoError.classList.remove("d-none");
    }

    function ocultarErrorRechazo() {
        if (!rechazoError) {
            return;
        }
        rechazoError.textContent = "";
        rechazoError.classList.add("d-none");
    }

    function actualizarVisibilidadComentarioRechazo() {
        if (!motivoRechazoSelect || !motivoRechazoComentarioWrapper) {
            return;
        }
        const mostrar = motivoRechazoSelect.value === "otro";
        if (mostrar) {
            motivoRechazoComentarioWrapper.classList.remove("d-none");
            if (motivoRechazoComentario) {
                motivoRechazoComentario.focus();
            }
        } else {
            motivoRechazoComentarioWrapper.classList.add("d-none");
            if (motivoRechazoComentario) {
                motivoRechazoComentario.value = "";
            }
        }
    }

    function construirTextoMotivoRechazo(opcion, comentario) {
        if (!opcion) {
            return "";
        }
        if (opcion === "otro") {
            return (comentario || "").trim();
        }
        return MOTIVOS_RECHAZO_TEXTOS[opcion] || opcion;
    }

    function actualizarMarcadorDenuncia(denuncia) {
        const marker = marcadoresPorId.get(Number(denuncia.id));
        if (!marker) {
            return;
        }
        const color = obtenerColorDenuncia(denuncia);
        marker.setStyle({ fillColor: color });
        const popup = marker.getPopup();
        const nuevoContenido = construirPopup(denuncia);
        if (popup) {
            popup.setContent(nuevoContenido);
        } else {
            marker.bindPopup(nuevoContenido);
        }
    }

    function manejarRechazoLocal(denunciaId, motivoFinal) {
        const id = Number(denunciaId);
        const denuncia = denunciasPorId.get(id);
        if (!denuncia) {
            cargarDenuncias(filtrosActivos);
            return;
        }

        const estadoAnterior = normalizarEstado(denuncia.estado);
        denuncia.estado = "rechazada";
        denuncia.estado_display = "Rechazada";
        denuncia.motivo_rechazo = motivoFinal;
        const configRechazada = obtenerConfigEstado("rechazada");
        if (configRechazada && configRechazada.color) {
            denuncia.color = configRechazada.color;
        } else {
            denuncia.color = DEFAULT_MARKER_COLOR;
        }
        denunciasPorId.set(id, denuncia);

        if (denunciasPorEstado[estadoAnterior]) {
            denunciasPorEstado[estadoAnterior] = denunciasPorEstado[
                estadoAnterior
            ].filter((item) => Number(item.id) !== id);
        }

        denunciasPorEstado.rechazada = denunciasPorEstado.rechazada
            .filter((item) => Number(item.id) !== id);
        denunciasPorEstado.rechazada.push(denuncia);
        ordenarDenunciasPorFecha(denunciasPorEstado.rechazada);

        if (denunciasPorEstado[estadoAnterior]) {
            renderEstado(estadoAnterior);
        }
        renderEstado("rechazada");
        actualizarMarcadorDenuncia(denuncia);
        activarTab("rechazada");
    }

    function abrirModalRechazo(denunciaId) {
        if (!rechazoModal) {
            return;
        }
        denunciaRechazoActual = { id: Number(denunciaId) };
        if (rechazoDenunciaIdElemento) {
            rechazoDenunciaIdElemento.textContent = `#${denunciaRechazoActual.id}`;
        }
        if (rechazoForm) {
            rechazoForm.reset();
        }
        ocultarErrorRechazo();
        actualizarVisibilidadComentarioRechazo();
        rechazoModal.show();
    }

    if (motivoRechazoSelect) {
        motivoRechazoSelect.addEventListener(
            "change",
            actualizarVisibilidadComentarioRechazo
        );
        actualizarVisibilidadComentarioRechazo();
    }

    if (rechazoForm && rechazoModal) {
        rechazoForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!denunciaRechazoActual) {
                mostrarErrorRechazo(
                    "No pudimos identificar la denuncia que deseas rechazar."
                );
                return;
            }
            ocultarErrorRechazo();
            const opcion = motivoRechazoSelect
                ? motivoRechazoSelect.value
                : "";
            const comentario = motivoRechazoComentario
                ? motivoRechazoComentario.value
                : "";
            const motivoFinal = construirTextoMotivoRechazo(
                opcion,
                comentario
            );

            if (!motivoFinal) {
                const mensaje =
                    opcion === "otro"
                        ? "Debes ingresar un comentario para rechazar la denuncia."
                        : "Debes seleccionar un motivo para rechazar la denuncia.";
                mostrarErrorRechazo(mensaje);
                return;
            }

            try {
                const denunciaId = denunciaRechazoActual.id;
                await enviarActualizacionDenuncia(denunciaId, {
                    estado: "rechazada",
                    motivo_rechazo: motivoFinal,
                });
                rechazoModal.hide();
                denunciaRechazoActual = null;
                mostrarMensajeGlobal(
                    "La denuncia fue rechazada correctamente.",
                    "success"
                );
                manejarRechazoLocal(denunciaId, motivoFinal);
            } catch (error) {
                console.error(error);
                const mensaje =
                    error.message ||
                    "No se pudo rechazar la denuncia en este momento.";
                mostrarErrorRechazo(mensaje);
            }
        });
    }

    map.on("popupopen", (event) => {
        const popupElement = event.popup.getElement();
        if (!popupElement) {
            return;
        }

        const contenedor = popupElement.querySelector(".popup-denuncia");
        if (!contenedor) {
            return;
        }

        const formulario = contenedor.querySelector(".update-form");
        const feedback = contenedor.querySelector(".feedback");
        const denunciaId = contenedor.dataset.id;

        if (!formulario) {
            return;
        }

        if (formulario.dataset.listenerAttached === "true") {
            return;
        }
        formulario.dataset.listenerAttached = "true";

        prepararSelectorJefe(contenedor);

        formulario.addEventListener("submit", async (evt) => {
            evt.preventDefault();
            feedback.textContent = "Guardando cambios...";
            feedback.className = "feedback mt-2 text-muted";

            const formData = new FormData(formulario);
            const payload = {
                reporte_cuadrilla: (formData.get("reporte_cuadrilla") || "").trim(),
            };
            const cuadrillaAsignada = formData.get("cuadrilla_asignada");
            if (cuadrillaAsignada !== null) {
                payload.cuadrilla_asignada = (cuadrillaAsignada || "").trim();
            }
            const jefeSeleccionado = formData.get("jefe_cuadrilla_asignado_id");
            if (jefeSeleccionado) {
                payload.jefe_cuadrilla_asignado_id = Number(jefeSeleccionado);
            }

            const estadoObjetivo = formData.get("estado");
            if (estadoObjetivo) {
                payload.estado = estadoObjetivo;
            }

            if (
                esFiscalizador &&
                payload.estado === "en_gestion" &&
                !payload.jefe_cuadrilla_asignado_id
            ) {
                feedback.textContent =
                    "Debes seleccionar un jefe de cuadrilla antes de continuar.";
                feedback.className = "feedback mt-2 text-danger";
                return;
            }

            if (
                esFiscalizador &&
                formulario.dataset.estadoActual === "en_gestion" &&
                payload.estado === "realizado" &&
                !payload.reporte_cuadrilla
            ) {
                feedback.textContent =
                    "Debes adjuntar el reporte de cuadrilla antes de marcar la denuncia como realizada.";
                feedback.className = "feedback mt-2 text-danger";
                return;
            }

            try {
                await enviarActualizacionDenuncia(denunciaId, payload);
                feedback.textContent = "Cambios guardados correctamente";
                feedback.className = "feedback mt-2 text-success";
                cargarDenuncias(filtrosActivos);
            } catch (error) {
                console.error(error);
                feedback.textContent =
                    error.message || "No se pudieron guardar los cambios";
                feedback.className = "feedback mt-2 text-danger";
            }
        });

        const botonRechazo = contenedor.querySelector(
            ".btn-rechazar-denuncia"
        );
        if (botonRechazo && rechazoModal) {
            botonRechazo.addEventListener("click", () => {
                abrirModalRechazo(denunciaId);
            });
        }
    });

    filtrosForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const filtros = {
            estado: filtrosForm.estado.value,
            zona: filtrosForm.zona.value,
            fecha_desde: filtrosForm.fecha_desde.value,
            fecha_hasta: filtrosForm.fecha_hasta.value,
        };
        cargarDenuncias(filtros);
    });

    recargarBtn.addEventListener("click", () => {
        cargarDenuncias(filtrosActivos);
    });

    cargarDenuncias();

    async function extraerMensajeDeError(respuesta) {
        const generico = "No se pudieron guardar los cambios";

        try {
            const data = await respuesta.clone().json();
            if (!data) {
                return generico;
            }

            if (typeof data === "string") {
                return data;
            }

            if (data.detail) {
                return data.detail;
            }

            const valores = Object.values(data)
                .flat()
                .map((item) =>
                    typeof item === "string" ? item : JSON.stringify(item)
                )
                .filter(Boolean);
            if (valores.length) {
                return valores.join(" ");
            }
        } catch (error) {
            console.warn("No fue posible interpretar el error", error);
        }

        return generico;
    }
})();
