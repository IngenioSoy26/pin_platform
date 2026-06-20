import os
import time
import json
import random
import argparse
import requests
from datetime import datetime, timezone

# Configuraciones
API_URL = "http://127.0.0.1:8000/api/iot/reading/"
POSITIONS = [
    "FL-1", "FL-2", "FR-1", "FR-2",          # STEER
    "RL-1", "RL-2", "RL-3", "RL-4",          # DRIVE LEFT
    "RR-1", "RR-2", "RR-3", "RR-4",          # DRIVE RIGHT
    "TL-1", "TL-2", "TL-3", "TL-4",          # TRAILER LEFT
    "TR-1", "TR-2", "TR-3", "TR-4"           # TRAILER RIGHT
]

class TruckSimulator:
    def __init__(self, device_code):
        self.device_code = device_code
        self.base_lat = 41.8781 + random.uniform(-0.5, 0.5)
        self.base_lon = -87.6298 + random.uniform(-0.5, 0.5)
        self.speed_mph = random.uniform(55.0, 70.0)
        self.tires = {pos: self._init_tire() for pos in POSITIONS}
        self.elapsed_minutes = 0

    def _init_tire(self):
        return {
            "pressure_psi": random.uniform(95.0, 105.0),
            "temperature_f": random.uniform(100.0, 115.0),
            "vibration_g": random.uniform(0.1, 0.3),
            "battery_level": random.uniform(80.0, 100.0),
            "is_offline": False
        }

    def update_physics(self, elapsed_minutes, force_scenario=None):
        self.elapsed_minutes = elapsed_minutes
        
        # Movimiento base
        self.base_lat += random.uniform(-0.005, 0.005)
        self.base_lon += random.uniform(-0.005, 0.005)
        
        # Física normal
        for pos, tire in self.tires.items():
            if not tire["is_offline"]:
                tire["pressure_psi"] += random.uniform(-0.5, 0.5)
                tire["temperature_f"] = 110.0 + (self.speed_mph * 0.2) + random.uniform(-2, 2)
                tire["vibration_g"] = 0.2 + (self.speed_mph * 0.005) + random.uniform(-0.05, 0.05)

        # Inyección de escenarios basados en tiempo o forzados
        escenario_actual = force_scenario or self._determine_scenario()
        self._apply_scenario(escenario_actual)
        
        return escenario_actual

    def _determine_scenario(self):
        # Ciclo de 40 minutos
        minuto_ciclo = self.elapsed_minutes % 40
        
        if 10 <= minuto_ciclo < 15: return "DESGASTE_GRADUAL"
        if 15 <= minuto_ciclo < 16: return "PINCHAZO"
        if 16 <= minuto_ciclo < 20: return "RECALENTAMIENTO"
        if 20 <= minuto_ciclo < 25: return "FRENAZO"
        if 25 <= minuto_ciclo < 30: return "OFFLINE"
        if 30 <= minuto_ciclo < 35: return "HOS_VIOLATION"
        if 35 <= minuto_ciclo < 40: return "OVERWEIGHT"
        return "NORMAL"

    def _apply_scenario(self, scenario):
        if scenario == "DESGASTE_GRADUAL":
            # FL-1 pierde presión lentamente
            self.tires["FL-1"]["pressure_psi"] -= 0.5
        elif scenario == "PINCHAZO":
            # RR-2 pierde 30 PSI de golpe
            self.tires["RR-2"]["pressure_psi"] = max(0, self.tires["RR-2"]["pressure_psi"] - 30)
        elif scenario == "RECALENTAMIENTO":
            # RL-3 sube temperatura drásticamente
            self.tires["RL-3"]["temperature_f"] = 180.0
        elif scenario == "FRENAZO":
            # Acelerómetro registra fuerza G negativa
            self.speed_mph = max(0, self.speed_mph - 20)
            for pos in self.tires:
                self.tires[pos]["vibration_g"] = 2.5
        elif scenario == "OFFLINE":
            # TL-2 deja de transmitir
            self.tires["TL-2"]["is_offline"] = True
        else:
            # Restaurar sensores offline
            self.tires["TL-2"]["is_offline"] = False

    def generate_payload(self):
        tire_readings = []
        for pos, tire in self.tires.items():
            if not tire["is_offline"]:
                tire_readings.append({
                    "position": pos,
                    "pressure_psi": round(tire["pressure_psi"], 2),
                    "temperature_f": round(tire["temperature_f"], 2),
                    "vibration_g": round(tire["vibration_g"], 2),
                    "battery_level": round(tire["battery_level"], 2)
                })

        return {
            "device_code": self.device_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vehicle_data": {
                "latitude": round(self.base_lat, 6),
                "longitude": round(self.base_lon, 6),
                "speed_mph": round(self.speed_mph, 1),
                "heading": random.randint(0, 359),
                "rpm": random.randint(1200, 1800),
                "battery_level": 98.5,
                "signal_strength": random.randint(-80, -50)
            },
            "tire_readings": tire_readings
        }

def print_log(device, scenario, success):
    colors = {
        "NORMAL": "\033[92m",             # Verde
        "DESGASTE_GRADUAL": "\033[93m",   # Amarillo
        "PINCHAZO": "\033[91m",           # Rojo
        "RECALENTAMIENTO": "\033[91m",    # Rojo
        "FRENAZO": "\033[93m",            # Amarillo
        "OFFLINE": "\033[91m",            # Rojo
        "HOS_VIOLATION": "\033[91m",      # Rojo
        "OVERWEIGHT": "\033[91m",         # Rojo
    }
    reset = "\033[0m"
    color = colors.get(scenario, reset)
    status = "OK" if success else "FAIL"
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {device} | Escenario: {scenario:16} | API: {status}{reset}")

def main():
    parser = argparse.ArgumentParser(description="Simulador IoT PIN Platform")
    parser.add_argument("--modo", choices=["demo", "stress"], default="demo")
    parser.add_argument("--tractomulas", type=int, default=12)
    parser.add_argument("--escenario", type=str, help="Forzar escenario específico")
    args = parser.parse_args()

    print("🚀 Iniciando Simulador IoT PIN Platform...")
    print(f"Modo: {args.modo} | Tractomulas: {args.tractomulas} | Intervalo: 30s")
    print("-" * 50)

    trucks = [TruckSimulator(f"PIN-MASTER-{str(i).zfill(3)}") for i in range(1, args.tractomulas + 1)]
    elapsed_minutes = 0

    try:
        while True:
            for truck in trucks:
                scenario = truck.update_physics(elapsed_minutes, args.escenario)
                payload = truck.generate_payload()
                
                try:
                    response = requests.post(API_URL, json=payload, timeout=2)
                    success = response.status_code in [200, 201]
                except requests.exceptions.RequestException:
                    success = False
                    
                print_log(truck.device_code, scenario, success)
                
            elapsed_minutes += 0.5 # Avanza medio minuto en la simulación
            time.sleep(30) # Espera 30 segundos reales
            
    except KeyboardInterrupt:
        print("\n🛑 Simulador detenido por el usuario.")

if __name__ == "__main__":
    main()
