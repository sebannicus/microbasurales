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

    const ultimaActualizacion = document.getElementById("ultima-actualizacion");
    const filtrosForm = document.getElementById("filtros-form");
    const recargarBtn = document.getElementById("recargar-btn");
    const tablaPendientesBody = document.getElementById("denuncias-pendientes-body");
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

    const estadosConfigElement = document.getElementById("estados-config");
    const DEFAULT_ESTADOS_CONFIG = [
        { value: "pendiente", label: "Pendiente", color: "#d32f2f" },
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

    function normalizarEstado(valor) {
        if (!valor) {
            return valor;
        }
        if (valor === "en_proceso") {
            return "en_gestion";
        }
        if (valor === "resuelta") {
            return "finalizado";
        }
        return valor;
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

    async function cargarDenuncias(filtros = {}) {
        filtrosActivos = filtros;
        markerLayer.clearLayers();
        marcadoresPorId.clear();

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
                    const estadoNormalizado = normalizarEstado(denuncia.estado);
                    if (estadoNormalizado === "pendiente") {
                        pendientes.push(denuncia);
                    } else if (estadoNormalizado === "en_gestion") {
                        enGestion.push(denuncia);
                    } else if (estadoNormalizado === "realizado") {
                        realizados.push(denuncia);
                    } else if (estadoNormalizado === "finalizado") {
                        finalizados.push(denuncia);
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
            enGestion.sort(comparadorPorFecha);
            realizados.sort(comparadorPorFecha);
            finalizados.sort(comparadorPorFecha);

            ajustarMapa(bounds);
            actualizarMarcaDeTiempo();
            actualizarTablaPendientes(pendientes);
            actualizarResumenEstado(
                enGestion,
                listaEnGestion,
                sinEnGestionTemplate,
                contadorEnGestion,
                { mostrarEstado: false }
            );
            actualizarResumenEstado(
                realizados,
                listaRealizado,
                sinRealizadoTemplate,
                contadorRealizados,
                { mostrarEstado: false }
            );
            actualizarResumenEstado(
                finalizados,
                listaFinalizado,
                sinFinalizadoTemplate,
                contadorFinalizados,
                { mostrarEstado: true }
            );
            activarTab(filtros.estado);
        } catch (error) {
            console.error(error);
            mostrarMensajeGlobal(
                "No se pudieron cargar las denuncias. Intenta nuevamente.",
                "danger"
            );
            actualizarTablaPendientes([]);
            actualizarResumenEstado(
                [],
                listaEnGestion,
                sinEnGestionTemplate,
                contadorEnGestion
            );
            actualizarResumenEstado(
                [],
                listaRealizado,
                sinRealizadoTemplate,
                contadorRealizados
            );
            actualizarResumenEstado(
                [],
                listaFinalizado,
                sinFinalizadoTemplate,
                contadorFinalizados
            );
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
        const imagenHtml = denuncia.imagen
            ? `<img src="${denuncia.imagen}" class="img-fluid rounded mb-2" alt="Evidencia">`
            : "";
        const direccion = denuncia.direccion || "Sin dirección registrada";
        const zona = denuncia.zona || "No asignada";
        const cuadrilla = denuncia.cuadrilla_asignada || "";
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
        const reporteCuadrilla = denuncia.reporte_cuadrilla;
        const tieneReporte = Boolean(reporteCuadrilla && reporteCuadrilla.id);
        const reporteDetalleHtml = construirBloqueReporte(reporteCuadrilla);
        const fecha = denuncia.fecha_creacion
            ? new Date(denuncia.fecha_creacion).toLocaleString("es-CL")
            : "Fecha no disponible";

        return `
            <div class="popup-denuncia" data-id="${denuncia.id}">
                ${imagenHtml}
                <p class="mb-1"><strong>Estado actual:</strong> <span class="estado-badge" style="color: ${obtenerColorDenuncia(denuncia)};">${obtenerEtiquetaEstado(denuncia)}</span></p>
                <p class="mb-1"><strong>Descripción:</strong> ${denuncia.descripcion}</p>
                <p class="mb-1"><strong>Dirección:</strong> ${direccion}</p>
                <p class="mb-2"><strong>Zona:</strong> ${zona}</p>
                <form class="update-form" data-estado-actual="${estadoActual}" data-tiene-reporte="${tieneReporte}">
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
                    <div class="mb-2">
                        <label class="form-label">Cuadrilla asignada</label>
                        <input type="text" class="form-control form-control-sm" name="cuadrilla_asignada" value="${escapeAttribute(
                            cuadrilla
                        )}">
                    </div>
                    <div class="mb-2 reporte-cuadrilla-group">
                        <label class="form-label">Reporte de cuadrilla</label>
                        ${reporteDetalleHtml}
                    </div>
                    <button type="submit" class="btn btn-sm btn-background w-100">Guardar cambios</button>
                </form>
                <div class="small text-muted mt-2">Reportado el ${fecha}</div>
                <div class="feedback mt-2"></div>
            </div>
        `;
    }

    function construirBloqueReporte(reporte) {
        if (!reporte) {
            return `<div class="text-muted small">Aún no se adjunta un reporte de cuadrilla.</div>`;
        }

        const comentario = escapeHtml(reporte.comentario || "");
        const jefe = reporte.jefe_cuadrilla
            ? escapeHtml(reporte.jefe_cuadrilla.nombre || "")
            : "";
        const fecha = formatearFecha(reporte.fecha_reporte);
        const foto = reporte.foto_trabajo
            ? `<div class="mt-1"><a href="${reporte.foto_trabajo}" target="_blank" rel="noopener" class="link-primary">Ver evidencia fotográfica</a></div>`
            : "";

        return `
            <div class="reporte-cuadrilla__detalle small">
                <p class="mb-1">${comentario || '<span class="text-muted">Sin comentario</span>'}</p>
                ${jefe ? `<div class="text-muted">Jefe de cuadrilla: ${jefe}</div>` : ""}
                ${fecha ? `<div class="text-muted">Fecha del reporte: ${fecha}</div>` : ""}
                ${foto}
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

    function crearDenunciaCard(denuncia) {
        const card = document.createElement("article");
        card.className = "denuncia-card";
        card.dataset.denunciaId = String(denuncia.id);

        if (denuncia.imagen) {
            const imagenWrapper = document.createElement("div");
            imagenWrapper.className = "denuncia-card__imagen-wrapper";
            const imagen = document.createElement("img");
            imagen.src = denuncia.imagen;
            imagen.alt = `Foto evidencia denuncia #${denuncia.id}`;
            imagenWrapper.appendChild(imagen);
            card.appendChild(imagenWrapper);
        }

        const idElemento = document.createElement("p");
        idElemento.className = "denuncia-card__id mb-0";
        idElemento.textContent = `Denuncia #${denuncia.id}`;
        card.appendChild(idElemento);

        const fechaElemento = document.createElement("p");
        fechaElemento.className = "denuncia-card__fecha mb-0";
        fechaElemento.textContent = formatearFecha(denuncia.fecha_creacion);
        card.appendChild(fechaElemento);

        const descripcionElemento = document.createElement("p");
        descripcionElemento.className = "mb-0";
        descripcionElemento.textContent = denuncia.descripcion || "Sin descripción disponible";
        card.appendChild(descripcionElemento);

        const meta = document.createElement("div");
        meta.className = "denuncia-card__meta";

        if (denuncia.zona) {
            const zonaElemento = document.createElement("p");
            zonaElemento.className = "mb-0";
            zonaElemento.textContent = `Zona: ${denuncia.zona}`;
            meta.appendChild(zonaElemento);
        }

        const nombreUsuario =
            denuncia.usuario && denuncia.usuario.nombre
                ? denuncia.usuario.nombre
                : "";
        if (nombreUsuario) {
            const denuncianteElemento = document.createElement("p");
            denuncianteElemento.className = "mb-0";
            denuncianteElemento.textContent = `Denunciante: ${nombreUsuario}`;
            meta.appendChild(denuncianteElemento);
        }

        if (meta.children.length) {
            card.appendChild(meta);
        }

        const estadoBadge = document.createElement("span");
        estadoBadge.className = "denuncia-card__estado-badge";
        estadoBadge.style.backgroundColor = obtenerColorDenuncia(denuncia);
        estadoBadge.textContent = obtenerEtiquetaEstado(denuncia);
        card.appendChild(estadoBadge);

        const acciones = document.createElement("div");
        acciones.className = "denuncia-card__acciones";

        const btnVer = document.createElement("button");
        btnVer.type = "button";
        btnVer.className = "btn btn-outline-secondary btn-sm";
        btnVer.textContent = "Ver en mapa";
        btnVer.addEventListener("click", () => {
            centrarDenunciaEnMapa(denuncia.id, { enfocarFormulario: false });
        });

        acciones.appendChild(btnVer);
        acciones.appendChild(btnEditar);
        card.appendChild(acciones);

        return card;
    }

    function crearFilaPendiente(denuncia) {
        return crearDenunciaCard(denuncia);
    }

    function crearResumenItem(denuncia, { mostrarEstado = false } = {}) {
        void mostrarEstado;
        return crearDenunciaCard(denuncia);
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
                cuadrilla_asignada: (formData.get("cuadrilla_asignada") || "").trim(),
            };

            const estadoObjetivo = formData.get("estado");
            if (estadoObjetivo) {
                payload.estado = estadoObjetivo;
            }

            if (
                esFiscalizador &&
                formulario.dataset.estadoActual === "en_gestion" &&
                payload.estado === "realizado" &&
                formulario.dataset.tieneReporte !== "true"
            ) {
                feedback.textContent =
                    "Debes adjuntar el reporte de cuadrilla antes de marcar la denuncia como realizada.";
                feedback.className = "feedback mt-2 text-danger";
                return;
            }

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
                cargarDenuncias(filtrosActivos);
            } catch (error) {
                console.error(error);
                feedback.textContent =
                    error.message || "No se pudieron guardar los cambios";
                feedback.className = "feedback mt-2 text-danger";
            }
        });
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