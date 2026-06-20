# Fase 9: Modelos Predictivos de Machine Learning (Analytics)

## Resumen
Se ha implementado el módulo de Inteligencia Artificial de la plataforma PIN. Dado que el dispositivo físico aún no está construido, se asume que las tractomulas de prueba actuarán como si tuvieran el dispositivo instalado, proporcionando los datos (simulados) necesarios para alimentar estos modelos.

## Modelos Implementados (Estructura y Entrenamiento)

Se crearon las clases para los 6 modelos predictivos solicitados en el documento maestro:
1. **`TireWearPredictor`** (Desgaste de llantas - XGBoost)
2. **`TireFailurePredictor`** (Fallo inminente - Red Neuronal LSTM)
3. **`HOSCompliancePredictor`** (Riesgo de violación de fatiga - Random Forest)
4. **`OverweightRiskPredictor`** (Riesgo de sobrepeso - XGBoost)
5. **`DemandForecaster`** (Pronóstico de demanda logística - Gradient Boosting)
6. **`OptimalLocationRecommender`** (Optimización de ubicaciones - K-Means)

## Comandos de Gestión
Se implementó el comando personalizado `python manage.py entrenar_modelos`, el cual entrena y evalúa todos los modelos (actualmente usando lógica de simulación/stubs) y reporta sus métricas de rendimiento (R2, AUC-ROC, Precision, etc.).

## Integración con el Sistema
La aplicación `apps.analytics` incluye el modelo de base de datos `Prediction` para almacenar los resultados (ej. "La llanta FL-1 tiene 15% de probabilidad de fallar en los próximos 7 días") y mostrarlos en los futuros Dashboards (Fase 11).
