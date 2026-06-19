
    // Inicializar el mapa centrado en Estados Unidos
    const map = L.map('main-map', {
        zoomControl: false, // Quitamos el default para ponerlo mejor
        preferCanvas: true  // CRÍTICO PARA RENDIMIENTO: Dibuja vectores en HTML5 Canvas en lugar de miles de nodos SVG
    }).setView([39.8283, -98.5795], 4);
    
    // Reposicionar el control de zoom para que no choque con el panel Glassmorphism
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Definición de las URLs de los mapas (Light y Dark mode)
    const mapBoxLightUrl = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    const mapBoxDarkUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    
    const tileOptions = {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    };

    // Crear ambas capas de forma independiente para transición fluida
    let lightLayer = L.tileLayer(mapBoxLightUrl, tileOptions);
    let darkLayer = L.tileLayer(mapBoxDarkUrl, tileOptions);

    // Añadir la capa base inicial
    if (document.documentElement.getAttribute('data-theme') === 'dark') {
        darkLayer.addTo(map);
    } else {
        lightLayer.addTo(map);
    }

    // Escuchar el evento de cambio de tema (creado en base.html)
    window.addEventListener('themeChanged', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        // Estrategia de superposición (Cross-fade) para evitar bloqueos
        // Añadimos la capa nueva por encima, y le damos 1 segundo al navegador para descargar 
        // las imágenes antes de borrar la capa vieja. Así nunca se ve un fondo gris vacío.
        if (isDark) {
            darkLayer.addTo(map);
            setTimeout(() => { if(map.hasLayer(lightLayer)) map.removeLayer(lightLayer); }, 1000);
        } else {
            lightLayer.addTo(map);
            setTimeout(() => { if(map.hasLayer(darkLayer)) map.removeLayer(darkLayer); }, 1000);
        }
    });

    // Crear grupos de marcadores agrupados (Clusters) para alto rendimiento
    // showCoverageOnHover: false desactiva el polígono azul que envuelve el área del clúster
    const clusters = {
        'truck_stops': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'wim': L.markerClusterGroup({ disableClusteringAtZoom: 10, chunkedLoading: true, showCoverageOnHover: false }),
        'tires': L.markerClusterGroup({ disableClusteringAtZoom: 11, chunkedLoading: true, showCoverageOnHover: false }),
        'alt_fuel': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'fuel': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'recycling': L.markerClusterGroup({ disableClusteringAtZoom: 9, chunkedLoading: true, showCoverageOnHover: false }),
        'showers': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'restaurants': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'wifi': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false }),
        'scales': L.markerClusterGroup({ disableClusteringAtZoom: 12, chunkedLoading: true, showCoverageOnHover: false })
    };

    // Agregar todas las capas al mapa inicialmente
    // Usamos condicionales para asegurar que respeten el checkbox si el usuario lo desmarcó rápido
    Object.keys(clusters).forEach(key => {
        const toggleId = 'toggle-' + key.replace('_', '-').replace('stops', 'truck-stops');
        const toggle = document.getElementById(toggleId);
        if (toggle && toggle.checked) {
            map.addLayer(clusters[key]);
        } else if (!toggle) {
            map.addLayer(clusters[key]); // fallback
        }
    });

    // Iconos personalizados usando FontAwesome y Leaflet DivIcon
    function createIcon(iconClass, color) {
        return L.divIcon({
            html: `<div style="background-color: ${color}; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><i class="fa-solid ${iconClass}"></i></div>`,
            className: 'custom-pin-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });
    }

    // Iconos base para capas secundarias
    const icons = {
        'truck_stop': createIcon('fa-bed', '#8b5cf6'),
        'wim': createIcon('fa-satellite-dish', '#3b82f6'),
        'tire_shop': createIcon('fa-wrench', '#eab308'),
        'alt_fuel': createIcon('fa-charging-station', '#10b981'),
        'recycling': createIcon('fa-recycle', '#8b5cf6'),
        'shower': createIcon('fa-shower', '#60a5fa'),
        'restaurant': createIcon('fa-utensils', '#fb923c'),
        'wifi': createIcon('fa-wifi', '#a78bfa'),
        'scale': createIcon('fa-weight-scale', '#94a3b8'),
        'parking': createIcon('fa-square-parking', '#64748b'),
        'fuel': createIcon('fa-gas-pump', '#10b981')
    };

    // Función para obtener el ícono dinámico de Truck Stop según el operador
    function getTruckStopIcon(operator) {
        const op = (operator || '').toLowerCase();
        let color = '#94a3b8'; // Gris por defecto (Paradores Públicos/Generales)
        
        if (op.includes('love')) {
            color = '#ef4444'; // Rojo Love's
        } else if (op.includes('pilot') || op.includes('flying j')) {
            color = '#f97316'; // Naranja Pilot
        } else if (op.includes('ta') || op.includes('petro') || op.includes('travelcenters')) {
            color = '#3b82f6'; // Azul TA/Petro
        }
        
        return createIcon('fa-bed', color);
    }

    // Capa para las rutas NHS
    let routesLayer = null;
    
    // Almacenar todos los marcadores de Truck Stops para poder filtrarlos después
    let allTruckStopMarkers = [];

    // Función principal para cargar datos desde la API de Django
    async function loadLayer(layerName, endpoint) {
        try {
            const response = await fetch(`/api/locations/?type=${endpoint}`);
            const data = await response.json();
            
            data.locations.forEach(loc => {
                const title = loc.name || 'Parada Sin Nombre';
                let popupContent = `<div class="map-popup">
                    <h3 style="margin:0 0 5px 0; color:var(--text-color); font-size:16px;">${title}</h3>`;
                
                // Detalles específicos según el tipo
                if(loc.type === 'truck_stop') {
                    const operator = loc.operator || 'Operador Independiente';
                    const cityState = (loc.city && loc.state) ? `${loc.city}, ${loc.state}` : 'Ubicación no registrada';

                    // Manejo de valores nulos o 0
                    const parkingText = (loc.parking && loc.parking > 0) ? `${loc.parking} Espacios` : 'No Disponible';
                    const dieselText = (loc.diesel && loc.diesel > 0) ? `${loc.diesel} Islas Diésel` : 'No Disponible';

                    popupContent += `<p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-building"></i> ${operator}</p>`;
                    popupContent += `<p style="margin:3px 0 8px 0; font-size:12px; color:var(--text-muted);"><i class="fa-solid fa-location-dot"></i> ${cityState}</p>`;
                    popupContent += `<p style="margin:0; font-size:14px; font-weight:500; color:var(--text-color);"><i class="fa-solid fa-square-parking"></i> ${parkingText} | <i class="fa-solid fa-gas-pump"></i> ${dieselText}</p></div>`;

                    // Añadir el Truck Stop base (solo si el checkbox está activo, validado al final)
                    const baseMarker = L.marker([loc.lat, loc.lon], { icon: getTruckStopIcon(loc.operator) })
                                    .bindPopup(popupContent);
                    clusters['truck_stops'].addLayer(baseMarker);

                    // Generar marcadores independientes para cada amenidad en la misma coordenada
                    if (loc.amenities && loc.amenities.length > 0) {
                        loc.amenities.forEach(am => {
                            let targetLayer = null;
                            let iconType = null;

                            if (am.includes('Shower')) { targetLayer = 'showers'; iconType = 'shower'; }
                            else if (am.includes('Restaurant') || am.includes('Comida:')) { targetLayer = 'restaurants'; iconType = 'restaurant'; }
                            else if (am.includes('WiFi')) { targetLayer = 'wifi'; iconType = 'wifi'; }
                            else if (am.includes('Scale')) { targetLayer = 'scales'; iconType = 'scale'; }
                            else if (am.includes('Tire')) { targetLayer = 'tires'; iconType = 'tire_shop'; }
                            else if (am.includes('Diesel') || am.includes('Fuel')) { targetLayer = 'fuel'; iconType = 'fuel'; }

                            if (targetLayer) {
                                let displayTitle = am.includes(':') ? am.split(':')[1].trim() : am;
                                let displayOperator = `Ubicado en: ${loc.name} (${loc.operator})`;
                                
                                if (loc.name === 'Unknown Truck Stop' && loc.operator === 'Public Rest Stop') {
                                    displayTitle = 'Área de Descanso con ' + displayTitle;
                                    displayOperator = 'Parador Comercial / Público';
                                }

                                let amPopup = `<div class="map-popup">
                                    <h3 style="margin:0 0 5px 0; color:var(--text-color); font-size:16px;">${displayTitle}</h3>
                                    <p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-building"></i> ${displayOperator}</p>
                                </div>`;
                                
                                // Para amenidades, usar un color más neutro en el Spiderfy, o el mismo icono base
                                let customAmIcon = icons[iconType];
                                if (iconType === 'restaurant') {
                                    customAmIcon = createIcon('fa-utensils', '#f97316');
                                }
                                
                                const amMarker = L.marker([loc.lat, loc.lon], { icon: customAmIcon })
                                                .bindPopup(amPopup);
                                clusters[targetLayer].addLayer(amMarker);
                            }
                        });
                    }

                    // Aislamiento visual en modo Spiderfy para los surtidores de combustible (si no están en las amenidades)
                    if (loc.diesel > 0 && (!loc.amenities || !loc.amenities.some(a => a.includes('Diesel')))) {
                        let displayTitle = loc.name;
                        let displayOperator = loc.operator;
                        if (loc.name === 'Unknown Truck Stop' && loc.operator === 'Public Rest Stop') {
                            displayTitle = 'Estación de Combustible';
                            displayOperator = 'Parador Comercial';
                        }
                        let amPopup = `<div class="map-popup">
                            <h3 style="margin:0 0 5px 0; color:var(--text-color); font-size:16px;">${displayTitle}</h3>
                            <p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-building"></i> ${displayOperator}</p>
                            <p style="margin:5px 0 0 0; font-size:13px;"><i class="fa-solid fa-gas-pump"></i> ${loc.diesel} Islas Diésel</p>
                        </div>`;
                        const fuelMarker = L.marker([loc.lat, loc.lon], { icon: icons['fuel'] })
                                        .bindPopup(amPopup);
                        clusters['fuel'].addLayer(fuelMarker);
                    }
                    
                    return; // Terminamos con truck_stops, continuamos con el foreach
                } else if(loc.type === 'alt_fuel') {
                    const cng = (loc.cng_dispensers && loc.cng_dispensers > 0) ? `${loc.cng_dispensers} Surtidores GNC` : '';
                    const ev = (loc.ev_dc_fast && loc.ev_dc_fast > 0) ? `${loc.ev_dc_fast} Cargadores EV Rápidos` : '';
                    const fuelInfo = [cng, ev].filter(Boolean).join(' | ') || 'Estación Alt Fuel';

                    popupContent += `<p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-building"></i> ${loc.operator || 'Operador Independiente'}</p>`;
                    popupContent += `<p style="margin:3px 0 8px 0; font-size:12px; color:var(--text-muted);"><i class="fa-solid fa-location-dot"></i> ${loc.city || 'No Registrada'}, ${loc.state || 'NA'}</p>`;
                    popupContent += `<p style="margin:0; font-size:14px; font-weight:500; color:var(--text-color);"><i class="fa-solid fa-bolt"></i> ${fuelInfo}</p>`;

                    if (loc.amenities && loc.amenities.length > 0) {
                        popupContent += `<div style="margin-top:10px; border-top:1px solid var(--border-color); padding-top:8px;">`;
                        popupContent += `<p style="margin:0; font-size:12px; font-weight:bold; color:var(--text-color);">Amenidades Disponibles:</p>`;
                        const amenitiesList = loc.amenities.map(am => `<span style="display:inline-block; background:var(--bg-color); border:1px solid var(--border-color); padding:2px 6px; border-radius:12px; font-size:11px; margin:2px 2px 0 0; color:var(--text-color);">${am}</span>`).join('');
                        popupContent += `<div style="margin-top:4px;">${amenitiesList}</div></div>`;
                    }

                    popupContent += `</div>`;

                    const marker = L.marker([loc.lat, loc.lon], { icon: icons['alt_fuel'] })
                                    .bindPopup(popupContent);
                    clusters['fuel'].addLayer(marker);
                    return;
                } else if(loc.type === 'wim') {
                    popupContent += `<p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-satellite-dish"></i> Status: ${loc.status}</p>`;
                } else if(loc.type === 'recycling') {
                    popupContent += `<p style="margin:0; font-size:13px; color:var(--text-muted);"><i class="fa-solid fa-weight-scale"></i> ${loc.tons.toLocaleString()} Tons Llantas Recicladas</p>`;
                }

                popupContent += `</div>`;

                const marker = L.marker([loc.lat, loc.lon], { icon: icons[loc.type] })
                                .bindPopup(popupContent);
                
                clusters[layerName].addLayer(marker);
            });
            
        } catch (error) {
            console.error(`Error loading ${layerName}:`, error);
        }
    }

    // Función para cargar las rutas NHS (GeoJSON)
    // El archivo de rutas pesa 544 MB, esto colapsa el navegador en Promise.all
    // Lo sacamos de la promesa general y le ponemos un control de error específico.
    async function loadRoutesLayer() {
        try {
            const routesIndicator = document.createElement('div');
            routesIndicator.id = 'routes-loading';
            routesIndicator.innerHTML = '<i class="fa-solid fa-route fa-spin" style="color:#0ea5e9;"></i> Cargando rutas (Puede tardar varios minutos)...';
            routesIndicator.style.fontSize = '12px';
            routesIndicator.style.color = '#0ea5e9';
            routesIndicator.style.textAlign = 'center';
            routesIndicator.style.marginTop = '10px';
            document.querySelector('.layer-toggles').appendChild(routesIndicator);

            const response = await fetch('/api/routes/');
            if (!response.ok) {
                routesIndicator.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Error API Rutas';
                return;
            }
            
            const data = await response.json();
            if (data.url) {
                // Fetch del archivo de medio gigabyte
                const geojResponse = await fetch(data.url);
                const geojsonData = await geojResponse.json();
                
                // Estilos dinámicos para las rutas según su clasificación (t)
                const routeStyle = function(feature) {
                    let color = '#94a3b8'; // Default / Terciarias
                    let weight = 1.5;
                    let opacity = 0.5;
                    let className = '';

                    if (feature.properties.t === 'I') {
                        color = '#0ea5e9'; // Azul (Interestatal)
                        weight = 3;
                        opacity = 0.8;
                        className = 'neon-route';
                    } else if (feature.properties.t === 'U') {
                        color = '#f59e0b'; // Amarillo (Nacional)
                        weight = 2.5;
                        opacity = 0.7;
                    } else if (feature.properties.t === 'S') {
                        color = '#10b981'; // Verde (Estatal)
                        weight = 2;
                        opacity = 0.6;
                    } else {
                        color = '#8b5cf6'; // Morado (Locales)
                    }

                    return {
                        color: color,
                        weight: weight,
                        opacity: opacity,
                        className: className
                    };
                };

                routesLayer = L.geoJSON(geojsonData, {
                    style: routeStyle,
                    onEachFeature: function (feature, layer) {
                        if (feature.properties) {
                            let typeName = 'Terciaria / Local';
                            if (feature.properties.t === 'I') typeName = 'Interestatal';
                            else if (feature.properties.t === 'U') typeName = 'Nacional (US)';
                            else if (feature.properties.t === 'S') typeName = 'Estatal';

                            let popup = `<div class="map-popup">
                                <h3 style="margin:0 0 5px 0; color:var(--text-color); font-size:16px;">Ruta ${typeName}</h3>`;
                            if (feature.properties.n) popup += `<p style="margin:5px 0 0 0; font-size:13px;"><i class="fa-solid fa-road"></i> ${feature.properties.n}</p>`;
                            popup += `</div>`;
                            layer.bindPopup(popup);
                        }
                    }
                });
                
                routesIndicator.innerHTML = '<i class="fa-solid fa-check"></i> Rutas NHS Listas';
                setTimeout(() => routesIndicator.remove(), 3000);

                // Solo agregar si el checkbox está activo cuando termine de cargar (que será mucho después de los demás)
                if (document.getElementById('toggle-routes').checked) {
                    routesLayer.addTo(map);
                }
            }
        } catch (error) {
            console.error("Error loading NHS routes:", error);
            const ind = document.getElementById('routes-loading');
            if(ind) ind.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color:red;"></i> Error cargando archivo pesado';
        }
    }

    // Cargar todas las capas de manera asíncrona
    async function loadAllData() {
        const indicator = document.getElementById('loading-indicator');
        indicator.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Descargando datos ligeros...';
        
        // Sacamos loadRoutesLayer() del Promise.all porque detiene la ejecución de todo lo demás
        // debido al peso masivo del archivo GeoJSON (544MB). Lo ejecutamos en paralelo pero independiente.
        loadRoutesLayer();

        await Promise.all([
            loadLayer('truck_stops', 'truck_stops'),
            loadLayer('wim', 'wim'),
            loadLayer('tires', 'tires'),
            loadLayer('alt_fuel', 'alt_fuel'),
            loadLayer('recycling', 'recycling')
        ]);
        
        // Validación de estado de checkboxes una vez que todo cargó
        // Si el usuario apagó algún checkbox mientras cargaba, lo quitamos del mapa.
        Object.keys(clusters).forEach(key => {
            const toggleId = 'toggle-' + key.replace('_', '-').replace('stops', 'truck-stops').replace('tires', 'tires').replace('alt_fuel', 'alt-fuel');
            const toggle = document.getElementById(toggleId);
            if (toggle && !toggle.checked) {
                map.removeLayer(clusters[key]);
            }
        });

        // Verificamos si apagaron las rutas NHS
        const routesToggle = document.getElementById('toggle-routes');
        if (routesLayer && (!routesToggle || !routesToggle.checked)) {
            map.removeLayer(routesLayer);
        }
        
        indicator.innerHTML = '<i class="fa-solid fa-check" style="color: #10b981;"></i> Datos cargados';
        setTimeout(() => indicator.style.display = 'none', 3000);
    }

    // Escuchar los checkboxes del panel Glassmorphism
    document.getElementById('toggle-truck-stops').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.truck_stops) : map.removeLayer(clusters.truck_stops);
    });
    document.getElementById('toggle-wim').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.wim) : map.removeLayer(clusters.wim);
    });
    document.getElementById('toggle-tires').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.tires) : map.removeLayer(clusters.tires);
    });
    document.getElementById('toggle-fuel').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.fuel) : map.removeLayer(clusters.fuel);
    });
    document.getElementById('toggle-recycling').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.recycling) : map.removeLayer(clusters.recycling);
    });
    document.getElementById('toggle-routes').addEventListener('change', function(e) {
        if (routesLayer) {
            e.target.checked ? map.addLayer(routesLayer) : map.removeLayer(routesLayer);
        }
    });

    // Listeners para las nuevas capas de comodidades
    document.getElementById('toggle-showers').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.showers) : map.removeLayer(clusters.showers);
    });
    document.getElementById('toggle-restaurants').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.restaurants) : map.removeLayer(clusters.restaurants);
    });
    document.getElementById('toggle-wifi').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.wifi) : map.removeLayer(clusters.wifi);
    });
    document.getElementById('toggle-scales').addEventListener('change', function(e) {
        e.target.checked ? map.addLayer(clusters.scales) : map.removeLayer(clusters.scales);
    });

    // Iniciar carga
    loadAllData();

