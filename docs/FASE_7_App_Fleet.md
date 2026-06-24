# FASE 7: Gestión de Flotas (Fleet Management)

Esta fase implementa la arquitectura gerencial y operativa de la plataforma. Convierte los datos de hardware y monitoreo en un sistema logístico funcional, permitiendo asignar viajes y conectar todos los actores del ecosistema (Tractomula, Conductor, Despachador y Empresa).

## Arquitectura de Modelos

1. **`CarrierCompany` (Existente en `core`)**: La empresa dueña de la flota o contratista, identificada por su número DOT y MC.
2. **`FleetManager`**: El perfil del usuario despachador. Se conecta al sistema de autenticación de Django (`User`) y está ligado directamente a una `CarrierCompany`.
3. **`Trip` (Viaje o Despacho)**: Es el modelo transaccional central. Actúa como un *hub* que entrelaza:
   - ¿Qué empresa lo realiza? (`company`)
   - ¿Qué vehículo se usa? (`truck` de la Fase 3)
   - ¿Quién maneja? (`driver` de la Fase 5)
   - ¿Quién despachó el viaje? (`dispatcher`)
   - ¿De dónde a dónde van? (`origin`, `destination`)
   - ¿Cuál es el estado? (PENDING, IN_TRANSIT, COMPLETED, CANCELLED)

## Integración Transversal

La creación de este módulo marca un punto de inflexión porque amarra las fases anteriores:
*   **Con la Fase 3 (Dispositivos):** El camión (`Truck`) asignado al `Trip` es el que estará transmitiendo los datos telemétricos de velocidad y vibración.
*   **Con la Fase 5 (HOS):** El conductor (`Driver`) asignado al `Trip` es a quien se le descontarán sus 11 horas de conducción legales.
*   **Con la Fase 6 (Peso):** Si el `Trip` pasa por una estación WIM, el pesaje quedará registrado en el historial de ese vehículo específico.

## [Capturas o Diagramas]
*(Espacio reservado para diagramas Entidad-Relación o capturas del panel de despacho)*