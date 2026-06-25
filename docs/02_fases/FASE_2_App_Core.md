# 🧩 FASE 2: App Core - Modelos Base

## 🎯 Objetivo de la Fase
Crear los modelos de datos fundamentales que servirían como la base transversal para el resto de la plataforma, permitiendo la herencia de propiedades y la estandarización de las locaciones geográficas.

## 🛠️ Logros y Componentes Construidos

1. **App Core (`apps/core`)**:
   - Inicialización de la aplicación central del sistema.
   - Configuración de la base de datos relacional.

2. **Modelo `Location` (Clase Padre)**:
   - Se construyó el modelo abstracto / base que maneja coordenadas (`latitude`, `longitude`), dirección, ciudad y estado.
   - Evita la duplicación de código en estaciones de servicio, básculas y otros puntos de interés.

3. **Modelo `Amenity` (Servicios Dinámicos)**:
   - Sistema *Many-to-Many* para asignar múltiples servicios a una ubicación (Duchas, WiFi, Restaurantes, Parqueos).
   - Capacidad para crear categorías dinámicas (ej. "Restaurante Específico").

4. **Modelos Heredados**:
   - `TruckStop`: Estaciones de descanso.
   - `WIMStation`: Estaciones de pesaje en movimiento.
   - `AlternativeFuelStation`: Estaciones de carga eléctrica y GNC.

## 📊 Diagrama Entidad-Relación (Base)

```mermaid
erDiagram
    LOCATION ||--o{ AMENITY : "ofrece"
    LOCATION {
        decimal latitude
        decimal longitude
        string city
        string state
    }
    AMENITY {
        string name
        string category
    }
    TRUCK_STOP {
        int parking_spaces
        int diesel_lanes
    }
    WIM_STATION {
        string status
        int number_of_lanes
    }
    LOCATION <|-- TRUCK_STOP : "Hereda"
    LOCATION <|-- WIM_STATION : "Hereda"
```

## 📸 Evidencia Visual

> **[ 🖼️ ESPACIO PARA IMAGEN: Captura del Panel de Administración de Django mostrando los registros de Truck Stops o Amenidades ]**

---
*Fase completada y auditada según el documento maestro.*