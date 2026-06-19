"""
Fórmulas físicas para el cálculo de desgaste de llantas con 10 factores de ajuste.
Basado en el documento maestro del proyecto.
"""

def factor_presion(psi_actual, psi_recomendado):
    if psi_recomendado <= 0: 
        return 1.0
    # Aumenta el desgaste si hay sub-inflado o sobre-inflado
    return 1 + 0.02 * abs(psi_actual - psi_recomendado) / psi_recomendado

def factor_temperatura(temp_f):
    # El desgaste aumenta exponencialmente por encima de 120°F
    return 1 + 0.005 * max(0, temp_f - 120)

def factor_velocidad(speed_mph):
    # Mayor desgaste a velocidades superiores a 55 mph
    return 1 + 0.01 * max(0, speed_mph - 55)

def factor_carga(carga_actual, carga_nominal):
    if carga_nominal <= 0: 
        return 1.0
    # Sobrecarga aumenta el desgaste de forma no lineal (exponente 1.25)
    return (carga_actual / carga_nominal) ** 1.25

def factor_vibracion(vibration_g):
    # Vibraciones superiores a 0.5G indican problemas mecánicos/balanceo
    return 1 + 2 * max(0, vibration_g - 0.5)

def factor_conduccion(hard_events_per_100mi):
    # Frenazos y aceleraciones bruscas
    return 1 + 0.02 * hard_events_per_100mi

def factor_ambiente(weather_adj=0.0):
    # Ajuste por condiciones climáticas extremas
    return 1.0 + weather_adj

def factor_ruta(route_adj=0.0):
    # Ajuste por tipo de vía (asfalto, concreto, destapada)
    return 1.0 + route_adj

def factor_mantenimiento(maint_adj=0.0):
    # Ajuste positivo (reducción de desgaste) si hay buen mantenimiento
    return 1.0 + maint_adj

def calcular_desgaste(millas_recorridas, tasa_base, **kwargs):
    """
    Calcula el desgaste en 32nds de pulgada basado en los 10 factores.
    
    desgaste_32nds = (millas/1000) * tasa_base * factores...
    """
    fp = factor_presion(kwargs.get('psi_actual', 100), kwargs.get('psi_recomendado', 100))
    ft = factor_temperatura(kwargs.get('temp_f', 100))
    fv = factor_velocidad(kwargs.get('speed_mph', 55))
    fc = factor_carga(kwargs.get('carga_actual', 4000), kwargs.get('carga_nominal', 4000))
    f_vib = factor_vibracion(kwargs.get('vibration_g', 0.1))
    f_cond = factor_conduccion(kwargs.get('hard_events', 0))
    f_amb = factor_ambiente(kwargs.get('weather_adj', 0.0))
    f_rut = factor_ruta(kwargs.get('route_adj', 0.0))
    f_man = factor_mantenimiento(kwargs.get('maint_adj', 0.0))
    
    # Fórmula final
    desgaste = (millas_recorridas / 1000.0) * tasa_base * fp * ft * fv * fc * f_vib * f_cond * f_amb * f_rut * f_man
    
    return desgaste