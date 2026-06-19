from apps.weight_monitoring.bridge_formula import calculate_bridge_formula, validate_axle_group
from apps.weight_monitoring.models import WeightRegulation, AxleConfiguration, WeightInspection

class WeightComplianceService:
    """
    Servicio para validar pesos de tractomulas contra regulaciones federales y estatales.
    """

    @staticmethod
    def check_weight_compliance(truck, state_code=None):
        """
        Valida el peso actual del vehículo contra los límites legales.
        Retorna un diccionario con los resultados de la validación.
        """
        axles = truck.axles.all().order_by('axle_number')
        if not axles.exists():
            return {"error": "El camión no tiene configuración de ejes registrada."}

        gross_weight = sum(axle.current_weight for axle in axles)
        num_axles = axles.count()
        
        # Calcular distancia total (L) - desde el primer eje hasta el último
        first_axle = axles.first()
        last_axle = axles.last()
        total_distance = last_axle.position_ft - first_axle.position_ft if first_axle and last_axle else 0
        
        # Obtener regulaciones del estado (o federales por defecto)
        regulation = None
        if state_code:
            regulation = WeightRegulation.objects.filter(state=state_code).first()
            
        max_gross = regulation.state_gross_limit if regulation else 80000.0
        
        # Validación de Peso Bruto (Gross Weight)
        is_gross_overweight = gross_weight > max_gross
        
        # Validación Federal Bridge Formula para todo el vehículo
        bridge_allowed = calculate_bridge_formula(total_distance, num_axles)
        is_bridge_overweight = gross_weight > bridge_allowed
        
        # Validación por ejes individuales o grupos (Simplificada para el reporte)
        axle_violations = []
        for axle in axles:
            axle_limit = regulation.single_axle_limit if regulation else 20000.0
            if axle.axle_type == 'TANDEM':
                axle_limit = regulation.tandem_axle_limit if regulation else 34000.0
                
            if axle.current_weight > axle_limit:
                axle_violations.append({
                    "axle_number": axle.axle_number,
                    "type": axle.axle_type,
                    "weight": axle.current_weight,
                    "limit": axle_limit
                })
                
        is_compliant = not is_gross_overweight and not is_bridge_overweight and len(axle_violations) == 0
        
        return {
            "is_compliant": is_compliant,
            "gross_weight": gross_weight,
            "max_gross_allowed": min(max_gross, bridge_allowed),
            "is_gross_overweight": is_gross_overweight,
            "is_bridge_overweight": is_bridge_overweight,
            "bridge_formula_limit": bridge_allowed,
            "axle_violations": axle_violations
        }

    @staticmethod
    def get_overweight_alerts(truck):
        """
        Genera alertas si la tractomula está excediendo los límites de peso,
        ya que esto incrementa drásticamente el desgaste de las llantas.
        """
        compliance_data = WeightComplianceService.check_weight_compliance(truck)
        alerts = []
        
        if compliance_data.get("error"):
            return alerts
            
        if compliance_data["is_gross_overweight"] or compliance_data["is_bridge_overweight"]:
            alerts.append({
                "type": "OVERWEIGHT_GROSS",
                "severity": "CRITICAL",
                "message": f"Peso bruto de {compliance_data['gross_weight']} lbs excede el límite permitido de {compliance_data['max_gross_allowed']} lbs."
            })
            
        for violation in compliance_data.get("axle_violations", []):
            alerts.append({
                "type": "OVERWEIGHT_AXLE",
                "severity": "HIGH",
                "message": f"El Eje {violation['axle_number']} ({violation['type']}) pesa {violation['weight']} lbs, excediendo el límite de {violation['limit']} lbs."
            })
            
        return alerts