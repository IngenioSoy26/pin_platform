# Fase 10: Simulador IoT Completo

## Resumen
Dado que los dispositivos físicos de hardware aún están en fase de desarrollo o ensamblaje, se ha construido un **Simulador IoT (Gemelo Digital)**. Este script actúa exactamente como si 12 (o más) tractomulas estuvieran equipadas con el sistema PIN (1 Maestro + 18 Sensores de Llantas) y estuvieran conduciendo en tiempo real por Estados Unidos.

## Características del Simulador
El archivo se encuentra en `scripts/simulador_iot.py` y cuenta con las siguientes capacidades:

1. **Generación de Física Realista**:
   - Calcula variables dinámicas basándose en la velocidad. Si la tractomula va más rápido, la temperatura y vibración de las llantas suben matemáticamente.
   - Crea lecturas para las 18 posiciones obligatorias de llantas (STEER, DRIVE, TRAILER).

2. **Inyección de Escenarios (State Machine)**:
   Posee un reloj interno de 40 minutos que somete a los vehículos a diferentes pruebas de estrés para validar los motores de alerta de la Fase 8:
   - *Minuto 0-10*: Operación NORMAL 🟢
   - *Minuto 10-15*: DESGASTE GRADUAL (Pérdida de presión lenta) 🟡
   - *Minuto 15-16*: PINCHAZO (Caída de 30 PSI súbita) 🔴
   - *Minuto 16-20*: RECALENTAMIENTO (Frenos pegados, sube a 180°F) 🔴
   - *Minuto 20-25*: FRENAZO (Acelerómetro detecta fuerza G negativa) 🟡
   - *Minuto 25-30*: OFFLINE (Un sensor pierde comunicación Bluetooth) 🔴
   - *Minuto 30-40*: Simulaciones de HOS y Peso.

3. **Conexión API**:
   Empaqueta todas las lecturas en formato JSON y hace peticiones HTTP POST hacia `http://127.0.0.1:8000/api/iot/reading/` cada 30 segundos, replicando la red 5G.

## Modos de Ejecución
- **Modo Demo (Por defecto)**: `python scripts/simulador_iot.py --modo demo` (Simula 12 tractomulas).
- **Modo Estrés**: `python scripts/simulador_iot.py --modo stress --tractomulas 1000` (Para pruebas de carga del servidor).
- **Forzar Escenario**: `python scripts/simulador_iot.py --escenario PINCHAZO` (Para probar un fallo específico inmediatamente).
