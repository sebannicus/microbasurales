(function () {
    const mapaElemento = document.getElementById("mapa-denuncias");
    if (!mapaElemento) {
        return;
    }

    const token = mapaElemento.dataset.token;
    const apiUrl = mapaElemento.dataset.apiUrl;
    const updateUrlTemplate = mapaElemento.dataset.updateUrl || "";
    const updateBaseUrl = updateUrlTemplate.replace(/0\/?$/, "");

    const ultimaActualizacion = document.getElementById("ultima-actualizacion");
    const filtrosForm = document.getElementById("filtros-form");
    const recargarBtn = document.getElementById("recargar-btn");
    const tablaPendientesBody = document.getElementById("denuncias-pendientes-body");
    const sinDenunciasRow = document.getElementById("sin-denuncias-pendientes");
    const contadorPendientes = document.getElementById("contador-pendientes");
    const sinDenunciasTemplate = sinDenunciasRow ? sinDenunciasRow.cloneNode(true) : null;

    const estadoTabs = document.querySelectorAll(".estado-tab");
    const estadoPaneles = document.querySelectorAll(".estado-panel");
    const btnNueva = document.getElementById("btnNueva");
    const btnGestion = document.getElementById("btnGestion");
    const btnFinalizada = document.getElementById("btnFinalizada");

    if (sinDenunciasRow) {
        sinDenunciasRow.remove();
    }

    const listaEnProceso = document.getElementById("denuncias-en-proceso-list");
    const sinEnProcesoElemento = document.getElementById("sin-denuncias-en-proceso");
    const contadorEnProceso = document.getElementById("contador-en-proceso");
    const sinEnProcesoTemplate = sinEnProcesoElemento
        ? sinEnProcesoElemento.cloneNode(true)
        : null;

    if (sinEnProcesoElemento) {
        sinEnProcesoElemento.remove();
    }

    const listaResueltas = document.getElementById("denuncias-resueltas-list");
    const sinResueltasElemento = document.getElementById("sin-denuncias-resueltas");
    const contadorResueltas = document.getElementById("contador-resueltas");
    const sinResueltasTemplate = sinResueltasElemento
        ? sinResueltasElemento.cloneNode(true)
        : null;

    if (sinResueltasElemento) {
        sinResueltasElemento.remove();
    }

    const estadosConfigElement = document.getElementById("estados-config");
    const DEFAULT_ESTADOS_CONFIG = [
        { value: "pendiente", label: "Nueva", color: "#d32f2f" },
        { value: "en_proceso", label: "En gestión", color: "#f57c00" },
        { value: "resuelta", label: "Finalizada", color: "#388e3c" },
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

    function normalizarTextoBasico(texto) {
        if (typeof texto !== "string") {
            return "";
        }

        return texto
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    }

    const estadosMap = new Map(
        estadosConfig.map((estado) => [estado.value, estado])
    );
    const estadoLabelToValue = new Map();
    const estadoValueNormalizedMap = new Map();

    estadosConfig.forEach(({ value, label }) => {
        const labelKey = normalizarTextoBasico(label);
        const valueKey = normalizarTextoBasico(value);

        if (labelKey && !estadoLabelToValue.has(labelKey)) {
            estadoLabelToValue.set(labelKey, value);
        }

        if (valueKey && !estadoValueNormalizedMap.has(valueKey)) {
            estadoValueNormalizedMap.set(valueKey, value);
        }
    });
    const DEFAULT_MARKER_COLOR = "#1d3557";
    const ESTADO_DEFECTO =
        (estadosMap.has("pendiente")
            ? "pendiente"
            : estadosConfig[0] && estadosConfig[0].value) || "pendiente";

    function obtenerConfigEstado(valor) {
        return estadosMap.get(valor);
    }

    function obtenerColorPorEstado(estado) {
        const config = estado ? obtenerConfigEstado(estado) : null;
        return (config && config.color) || DEFAULT_MARKER_COLOR;
    }

    function obtenerColorDenuncia(denuncia) {
        if (denuncia && denuncia.color) {
            return denuncia.color;
        }

        return obtenerColorPorEstado(denuncia ? denuncia.estado : null);
    }

    function iconoSegunEstado(estado) {
        const clave = estado || "__default__";
        if (iconosPorEstado.has(clave)) {
            return iconosPorEstado.get(clave);
        }

        const color = obtenerColorPorEstado(estado);
        const icono = L.divIcon({
            className: "denuncia-marker",
            html: `<span class="marker-estado" style="background-color: ${color};"></span>`,
            iconSize: [22, 22],
            iconAnchor: [11, 22],
            popupAnchor: [0, -22],
        });

        iconosPorEstado.set(clave, icono);
        return icono;
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

    const map = L.map("mapa-denuncias", {
        scrollWheelZoom: true,
    }).setView([-33.4507, -70.6671], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);

    const capaDenuncias = L.layerGroup().addTo(map);
    const marcadoresPorId = new Map();
    const iconosPorEstado = new Map();
    let filtrosActivos = {};

    function obtenerFiltrosDesdeFormulario() {
        if (!filtrosForm) {
            const { _parametrosConsulta, estado_parametro, ...resto } =
                filtrosActivos || {};
            return { ...resto };
        }

        const obtenerValorSeguro = (campo) =>
            campo && "value" in campo ? campo.value : "";

        return {
            estado: obtenerValorSeguro(filtrosForm.estado),
            zona: obtenerValorSeguro(filtrosForm.zona),
            desde: obtenerValorSeguro(filtrosForm.fecha_desde),
            hasta: obtenerValorSeguro(filtrosForm.fecha_hasta),
        };
    }

    function normalizarEstadoValor(estadoEntrada) {
        const entradaLimpia =
            typeof estadoEntrada === "string"
                ? estadoEntrada.trim()
                : estadoEntrada;

        if (!entradaLimpia) {
            return "";
        }

        if (estadosMap.has(entradaLimpia)) {
            return entradaLimpia;
        }

        const claveNormalizada = normalizarTextoBasico(entradaLimpia);

        if (estadoLabelToValue.has(claveNormalizada)) {
            return estadoLabelToValue.get(claveNormalizada);
        }

        if (estadoValueNormalizedMap.has(claveNormalizada)) {
            return estadoValueNormalizedMap.get(claveNormalizada);
        }

        return entradaLimpia;
    }

    function normalizarFiltros(filtros = {}) {
        const limpiar = (valor) =>
            typeof valor === "string" ? valor.trim() : valor;

        const normalizados = { ...filtros };

        delete normalizados._parametrosConsulta;
        delete normalizados.estado_parametro;

        if (!normalizados.desde && normalizados.fecha_desde) {
            normalizados.desde = normalizados.fecha_desde;
        }
        if (!normalizados.hasta && normalizados.fecha_hasta) {
            normalizados.hasta = normalizados.fecha_hasta;
        }

        const estadoEntrada = limpiar(normalizados.estado || "");
        const zona = limpiar(normalizados.zona || "");
        const desde = limpiar(normalizados.desde || "");
        const hasta = limpiar(normalizados.hasta || "");

        const estadoNormalizado = normalizarEstadoValor(estadoEntrada);
        normalizados.estado = estadoNormalizado;
        normalizados.estado_parametro = estadoEntrada || estadoNormalizado;
        normalizados.zona = zona;
        normalizados.desde = desde;
        normalizados.hasta = hasta;

        delete normalizados.fecha_desde;
        delete normalizados.fecha_hasta;

        const parametrosConsulta = {};
        if (normalizados.estado_parametro) {
            parametrosConsulta.estado = normalizados.estado_parametro;
        }
        if (zona) {
            parametrosConsulta.zona = zona;
        }
        if (desde) {
            parametrosConsulta.desde = desde;
        }
        if (hasta) {
            parametrosConsulta.hasta = hasta;
        }

        normalizados._parametrosConsulta = parametrosConsulta;

        return normalizados;
    }

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

    async function cargarMapaConDatos(filtros = {}) {
        const filtrosNormalizados = normalizarFiltros(filtros);
        filtrosActivos = filtrosNormalizados;
        capaDenuncias.clearLayers();
        marcadoresPorId.clear();

        try {
            const parametrosConsulta =
                filtrosNormalizados._parametrosConsulta || {};
            const filtrosValidos = Object.entries(parametrosConsulta).filter(
                ([, value]) =>
                    value !== undefined &&
                    value !== null &&
                    String(value).trim() !== ""
            );

            let paginaUrl = new URL(apiUrl);
            const parametrosBase = new URLSearchParams(paginaUrl.search);

            filtrosValidos.forEach(([clave, valor]) => {
                parametrosBase.set(clave, valor);
            });

            paginaUrl.search = parametrosBase.toString();

            const bounds = [];
            const pendientes = [];
            const enProceso = [];
            const resueltas = [];

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
                    if (denuncia.estado === "pendiente") {
                        pendientes.push(denuncia);
                    } else if (denuncia.estado === "en_proceso") {
                        enProceso.push(denuncia);
                    } else if (denuncia.estado === "resuelta") {
                        resueltas.push(denuncia);
                    }
                });

                if (data.next) {
                    paginaUrl = new URL(data.next);
                } else {
                    paginaUrl = null;
                }
            }

            const comparadorPorFecha = (a, b) => {
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
            };

            pendientes.sort(comparadorPorFecha);
            enProceso.sort(comparadorPorFecha);
            resueltas.sort(comparadorPorFecha);

            ajustarMapa(bounds);
            actualizarMarcaDeTiempo();
            actualizarTablaPendientes(pendientes);
            actualizarResumenEstado(
                enProceso,
                listaEnProceso,
                sinEnProcesoTemplate,
                contadorEnProceso,
                { mostrarEstado: false }
            );
            actualizarResumenEstado(
                resueltas,
                listaResueltas,
                sinResueltasTemplate,
                contadorResueltas,
                { mostrarEstado: true }
            );
            activarTab(filtrosNormalizados.estado);
        } catch (error) {
            console.error(
                "Error al cargar las denuncias con los filtros",
                filtrosNormalizados,
                error
            );
            mostrarMensajeGlobal(
                "No se pudieron cargar las denuncias. Intenta nuevamente.",
                "danger"
            );
            actualizarTablaPendientes([]);
            actualizarResumenEstado(
                [],
                listaEnProceso,
                sinEnProcesoTemplate,
                contadorEnProceso
            );
            actualizarResumenEstado(
                [],
                listaResueltas,
                sinResueltasTemplate,
                contadorResueltas
            );
        }
    }

    function cargarDenunciasPorEstado(estadoDeseado) {
        const estadoNormalizado = normalizarEstadoValor(estadoDeseado);

        if (filtrosForm && filtrosForm.estado) {
            filtrosForm.estado.value = estadoNormalizado;
        }

        const filtrosActuales = obtenerFiltrosDesdeFormulario();
        filtrosActuales.estado = estadoDeseado;

        return cargarMapaConDatos(filtrosActuales);
    }

    function agregarMarcador(denuncia, bounds) {
        if (!denuncia.latitud || !denuncia.longitud) {
            return;
        }

        const marker = L.marker([denuncia.latitud, denuncia.longitud], {
            icon: iconoSegunEstado(denuncia.estado),
            title: `#${denuncia.id} · ${obtenerEtiquetaEstado(denuncia)}`,
        });

        marker.bindPopup(construirPopup(denuncia));
        capaDenuncias.addLayer(marker);
        marcadoresPorId.set(Number(denuncia.id), marker);
        bounds.push([denuncia.latitud, denuncia.longitud]);
    }

    function construirPopup(denuncia) {
        const imagenHtml = denuncia.imagen
            ? `<img src="${denuncia.imagen}" class="img-fluid rounded mb-2" alt="Evidencia">`
            : "";
        const direccion = denuncia.direccion || "Sin dirección registrada";
        const zona = denuncia.zona || "No asignada";
        const cuadrilla = denuncia.cuadrilla_asignada || "";
        const fecha = denuncia.fecha_creacion
            ? new Date(denuncia.fecha_creacion).toLocaleString("es-CL")
            : "Fecha no disponible";

        const options = estadosConfig
            .map(
                ({ value, label }) =>
                    `<option value="${value}" ${
                        denuncia.estado === value ? "selected" : ""
                    }>${label}</option>`
            )
            .join("");

        return `
            <div class="popup-denuncia" data-id="${denuncia.id}">
                ${imagenHtml}
                <p class="mb-1"><strong>Estado actual:</strong> <span class="estado-badge" style="color: ${obtenerColorDenuncia(denuncia)};">${obtenerEtiquetaEstado(denuncia)}</span></p>
                <p class="mb-1"><strong>Descripción:</strong> ${denuncia.descripcion}</p>
                <p class="mb-1"><strong>Dirección:</strong> ${direccion}</p>
                <p class="mb-2"><strong>Zona:</strong> ${zona}</p>
                <form class="update-form">
                    <div class="mb-2">
                        <label class="form-label">Actualizar estado</label>
                        <select class="form-select form-select-sm" name="estado">
                            ${options}
                        </select>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Cuadrilla asignada</label>
                        <input type="text" class="form-control form-control-sm" name="cuadrilla_asignada" value="${cuadrilla}">
                    </div>
                    <button type="submit" class="btn btn-sm btn-background w-100">Guardar cambios</button>
                </form>
                <div class="small text-muted mt-2">Reportado el ${fecha}</div>
                <div class="feedback mt-2"></div>
            </div>
        `;
    }

    function actualizarTablaPendientes(denuncias) {
        if (!tablaPendientesBody) {
            return;
        }

        tablaPendientesBody.innerHTML = "";

        if (!denuncias.length) {
            if (sinDenunciasTemplate) {
                const filaVacia = sinDenunciasTemplate.cloneNode(true);
                filaVacia.id = "";
                tablaPendientesBody.appendChild(filaVacia);
            }
        } else {
            denuncias.forEach((denuncia) => {
                tablaPendientesBody.appendChild(crearFilaPendiente(denuncia));
            });
        }

        actualizarContador(contadorPendientes, denuncias.length);
    }

    function crearFilaPendiente(denuncia) {
        const fila = document.createElement("tr");
        fila.dataset.denunciaId = String(denuncia.id);

        const idTd = document.createElement("td");
        idTd.textContent = `#${denuncia.id}`;

        const fechaTd = document.createElement("td");
        fechaTd.textContent = formatearFecha(denuncia.fecha_creacion);

        const descripcionTd = document.createElement("td");
        descripcionTd.textContent = resumirTexto(denuncia.descripcion);

        const zonaTd = document.createElement("td");
        zonaTd.textContent = denuncia.zona || "No asignada";

        const denuncianteTd = document.createElement("td");
        const nombreUsuario =
            denuncia.usuario && denuncia.usuario.nombre
                ? denuncia.usuario.nombre
                : "Sin registro";
        denuncianteTd.textContent = nombreUsuario;

        const accionesTd = document.createElement("td");
        accionesTd.className = "text-end";

        const btnVisualizar = document.createElement("button");
        btnVisualizar.type = "button";
        btnVisualizar.className = "btn btn-outline-secondary btn-sm btn-action me-2";
        btnVisualizar.textContent = "Visualizar";
        btnVisualizar.addEventListener("click", () => {
            centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: false });
        });

        const btnEditar = document.createElement("button");
        btnEditar.type = "button";
        btnEditar.className = "btn btn-background btn-sm btn-action";
        btnEditar.textContent = "Editar";
        btnEditar.addEventListener("click", () => {
            centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: true });
        });

        accionesTd.appendChild(btnVisualizar);
        accionesTd.appendChild(btnEditar);

        fila.appendChild(idTd);
        fila.appendChild(fechaTd);
        fila.appendChild(descripcionTd);
        fila.appendChild(zonaTd);
        fila.appendChild(denuncianteTd);
        fila.appendChild(accionesTd);

        return fila;
    }

    function crearResumenItem(denuncia, { mostrarEstado = false } = {}) {
        const item = document.createElement("div");
        item.className =
            "list-group-item py-3 gap-3 d-flex flex-column flex-md-row align-items-md-center justify-content-between";
        item.dataset.denunciaId = String(denuncia.id);

        const info = document.createElement("div");
        info.className = "flex-grow-1";

        const encabezado = document.createElement("div");
        encabezado.className = "fw-semibold";
        const fechaFormateada = formatearFecha(denuncia.fecha_creacion);
        const zona = denuncia.zona ? ` · ${denuncia.zona}` : "";
        encabezado.textContent = `#${denuncia.id} · ${fechaFormateada}${zona}`;

        const descripcion = document.createElement("div");
        descripcion.className = "text-muted small";
        descripcion.textContent = resumirTexto(denuncia.descripcion);

        info.appendChild(encabezado);
        info.appendChild(descripcion);

        if (mostrarEstado) {
            const estadoLabel = document.createElement("div");
            estadoLabel.className = "estado-label text-muted";
            estadoLabel.textContent = obtenerEtiquetaEstado(denuncia);
            info.appendChild(estadoLabel);
        }

        const acciones = document.createElement("div");
        acciones.className = "acciones";

        const btnVer = document.createElement("button");
        btnVer.type = "button";
        btnVer.className = "btn btn-outline-secondary btn-sm";
        btnVer.textContent = "Ver en mapa";
        btnVer.addEventListener("click", () => {
            centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: false });
        });

        const btnEditar = document.createElement("button");
        btnEditar.type = "button";
        btnEditar.className = "btn btn-background btn-sm";
        btnEditar.textContent = "Editar";
        btnEditar.addEventListener("click", () => {
            centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: true });
        });

        acciones.appendChild(btnVer);
        acciones.appendChild(btnEditar);

        item.appendChild(info);
        item.appendChild(acciones);

        return item;
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
        contadorElemento,
        opciones = {}
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
                contenedor.appendChild(crearResumenItem(denuncia, opciones));
            });
        }

        actualizarContador(contadorElemento, denuncias.length);
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

    function resumirTexto(texto) {
        if (!texto) {
            return "Sin descripción";
        }
        const limpio = String(texto).trim();
        if (limpio.length <= 80) {
            return limpio;
        }
        return `${limpio.slice(0, 77)}…`;
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

    function ajustarMapa(bounds) {
        if (!bounds.length) {
            return;
        }
        const leafletBounds = L.latLngBounds(bounds);
        map.fitBounds(leafletBounds, { padding: [40, 40] });
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

        formulario.addEventListener("submit", async (evt) => {
            evt.preventDefault();
            feedback.textContent = "Guardando cambios...";
            feedback.className = "feedback mt-2 text-muted";

            const formData = new FormData(formulario);
            const payload = {
                estado: formData.get("estado"),
                cuadrilla_asignada: formData.get("cuadrilla_asignada"),
            };

            try {
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

                feedback.textContent = "Cambios guardados correctamente";
                feedback.className = "feedback mt-2 text-success";
                cargarMapaConDatos(filtrosActivos);
            } catch (error) {
                console.error(error);
                feedback.textContent =
                    error.message || "No se pudieron guardar los cambios";
                feedback.className = "feedback mt-2 text-danger";
            }
        });
    });

    if (filtrosForm) {
        filtrosForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const filtros = obtenerFiltrosDesdeFormulario();
            cargarMapaConDatos(filtros);
        });
    }

    if (recargarBtn) {
        recargarBtn.addEventListener("click", () => {
            cargarMapaConDatos(filtrosActivos);
        });
    }

    if (btnNueva) {
        btnNueva.onclick = () => cargarDenunciasPorEstado("Nueva");
    }

    if (btnGestion) {
        btnGestion.onclick = () => cargarDenunciasPorEstado("En gestión");
    }

    if (btnFinalizada) {
        btnFinalizada.onclick = () => cargarDenunciasPorEstado("Finalizada");
    }

    cargarDenunciasPorEstado("Nueva");

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
