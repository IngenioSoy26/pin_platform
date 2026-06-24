from __future__ import annotations

import json
from pathlib import Path

from .tire_wear_model import TireWearPredictor
from .tire_failure_model import TireFailurePredictor
from .hos_predictor import HOSCompliancePredictor
from .overweight_predictor import OverweightRiskPredictor
from .demand_forecaster import DemandForecaster
from .location_optimizer import OptimalLocationRecommender

class TrainingManager:
    @staticmethod
    def train_all_models():
        print("Iniciando entrenamiento de modelos de Machine Learning...")
        artifacts_dir = Path(__file__).resolve().parents[2] / "ml_models"
        artifacts_dir.mkdir(exist_ok=True)

        models = [
            ("tire_wear", TireWearPredictor(), [{"estimated_tread_depth": 10}] * 500),
            ("tire_failure", TireFailurePredictor(), [{"pressure_psi": 95}] * 500),
            ("hos_compliance", HOSCompliancePredictor(), [{"driving_hours_today": 8}] * 500),
            ("overweight_risk", OverweightRiskPredictor(), [{"gross_weight": 76000}] * 500),
            ("demand_forecast", DemandForecaster(), [{"active_trucks": 100}] * 500),
            ("location_optimizer", OptimalLocationRecommender(), [{"corridor_center": {"lat": 39.5, "lon": -98.35}}] * 500),
        ]

        for model_name, predictor, training_data in models:
            metrics = predictor.train(training_data)
            artifact_path = artifacts_dir / f"{model_name}.json"
            artifact_path.write_text(
                json.dumps({"model": model_name, "metrics": metrics}, indent=2),
                encoding="utf-8",
            )
            print(f"Entrenando {predictor.__class__.__name__}... Listo. Metricas: {metrics}")
        return True
