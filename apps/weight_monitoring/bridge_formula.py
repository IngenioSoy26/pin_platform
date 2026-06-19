"""
Implementación de la Federal Bridge Gross Weight Formula (23 CFR 658.17).
Fórmula: W = 500 * [ (L * N) / (N - 1) + 12 * N + 36 ]

Donde:
W = Peso máximo permitido (lbs) en un grupo de dos o más ejes.
L = Distancia (en pies) entre los extremos del grupo de ejes.
N = Número de ejes bajo consideración.
"""

def calculate_bridge_formula(distance_ft, num_axles):
    """
    Calcula el peso máximo permitido para un grupo de ejes según la distancia entre ellos.
    Retorna el peso en libras, truncado a los 500 lbs más cercanos como dicta la norma.
    """
    if num_axles < 2:
        return 20000.0  # Límite federal estándar para un solo eje
        
    w = 500 * ( (distance_ft * num_axles) / (num_axles - 1) + (12 * num_axles) + 36 )
    
    # La norma indica redondear a los 500 lbs más cercanos
    w_rounded = round(w / 500.0) * 500.0
    
    # Límite federal absoluto bruto
    if w_rounded > 80000.0 and num_axles >= 5:
        w_rounded = 80000.0
        
    return w_rounded

def validate_axle_group(axle_weights, distance_ft, num_axles):
    """
    Valida si un grupo de ejes excede la fórmula del puente.
    axle_weights: Lista de pesos en lbs de los ejes en el grupo.
    """
    total_weight = sum(axle_weights)
    max_allowed = calculate_bridge_formula(distance_ft, num_axles)
    
    # Excepción especial de la norma: Dos ejes tándem consecutivos espaciados por al menos 36 pies
    # pueden llevar 34,000 lbs cada uno (68,000 lbs total) incluso si la fórmula dice menos.
    if num_axles == 4 and distance_ft >= 36.0 and total_weight <= 68000.0:
        return True, max_allowed
        
    return total_weight <= max_allowed, max_allowed