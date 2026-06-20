# FASE 6: Control de Peso (Weight Monitoring)

Esta fase implementa la **Fórmula del Puente Federal (Federal Bridge Gross Weight Formula)**, esencial para el control del desgaste de la infraestructura vial y la seguridad de las tractomulas Clase 8.

## Arquitectura de Modelos

1. **`WeightRegulation`**: Tabla maestra que contiene los límites legales (por defecto los federales, pero ajustable por Estado). Registra los límites máximos para ejes simples (20,000 lbs), tándem (34,000 lbs) y el peso bruto (80,000 lbs).
2. **`AxleConfiguration`**: Modela físicamente la disposición de ejes debajo del chasis de la tractomula. Guarda la distancia (en pies) desde el parachoques delantero, dato indispensable para la Fórmula del Puente.
3. **`WeightInspection`**: Registra los pesajes reales de las tractomulas. Se enlaza con las estaciones dinámicas (WIM - Weigh-In-Motion) que vimos en la Fase 4, o con cálculos en vivo (IoT).

## Motor Matemático: La Fórmula del Puente

El corazón de este módulo está en `bridge_formula.py`. Implementa la fórmula exacta dictada por la **23 CFR 658.17**:

```python
W = 500 * ( (L * N) / (N - 1) + (12 * N) + 36 )
```
*Donde:*
*   `W`: Peso máximo permitido en libras.
*   `L`: Distancia en pies entre los extremos de los ejes.
*   `N`: Número de ejes evaluados.

## Motor de Cumplimiento (Compliance Service)

El archivo `services.py` aloja el `WeightComplianceService`. Este motor evalúa la tractomula en tres niveles simultáneos:
1.  **Límite Bruto**: ¿El camión entero pesa más de 80,000 libras?
2.  **Límite de la Fórmula**: Aunque pese menos de 80,000 lbs, ¿sus ejes están demasiado juntos como para soportar ese peso sin destruir el pavimento?
3.  **Límite por Eje**: ¿Un eje en particular está sobrecargado (ej. mal estibado)?

Si se rompe alguna regla, el servicio dispara **Alertas de Sobrepeso**, que a su vez se conectan con la Fase 4 (Llantas) para acelerar el algoritmo de desgaste, ya que el sobrepeso destruye el caucho más rápido.

## 📸 Evidencia Visual

Se implementó el Dashboard Gerencial Frontend con diseño Glassmorphism, que permite auditar:
- La Tasa de Cumplimiento de peso de la flota en los últimos 30 días.
- Historial detallado de todas las inspecciones (dinámicas WIM y estáticas).
- Un panel lateral que actúa como un "Centro de Infracciones" para monitorear en tiempo real a los vehículos que han excedido la Federal Bridge Formula.

---
*Fase 6 completada y auditada según el documento maestro.*