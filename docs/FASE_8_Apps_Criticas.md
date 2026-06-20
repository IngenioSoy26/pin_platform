# Fase 8: Motor de Alertas, Recomendaciones e Ingestión IoT

## Resumen
Esta fase implementa el núcleo del sistema PIN: la capacidad de recibir datos telemétricos en tiempo real, procesarlos para detectar anomalías y tomar decisiones inteligentes usando la "biblioteca de conocimiento" de la Fase 7.

## Aplicaciones Construidas

1. **`apps.iot_ingestion`**:
   - Expone el endpoint crítico `POST /api/iot/reading/`.
   - Recibe la telemetría del camión (GPS, velocidad, batería) y de sus 18 sensores de llantas.
   - Actúa como el puente entre el hardware físico (Fase 3) y el backend analítico.

2. **`apps.alerts`**:
   - Implementa el `AlertEngine` (Motor de Alertas).
   - Genera alertas automáticas (ej. "Baja Presión", "Exceso de Peso", "Violación HOS") clasificadas por severidad (INFO hasta CRITICAL).

3. **`apps.recommendations`**:
   - Implementa el `RecommendationEngine` (Motor de Recomendaciones o "Copiloto Logístico").
   - Utiliza las alertas generadas y los servicios geoespaciales de la Fase 7 para proponer soluciones.
   - Ejemplo: Ante una alerta de llanta pinchada, recomienda la estación con servicio de vulcanizadora más cercana.

## Pruebas Realizadas
- Creación de modelos y migraciones exitosas.
- El endpoint `POST /api/iot/reading/` responde correctamente y está listo para recibir la ráfaga de datos del simulador (que se construirá en fases posteriores).
