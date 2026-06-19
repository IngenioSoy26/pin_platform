import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import TruckStop

print("Iniciando análisis de duplicados en Truck Stops...")

# Buscar coordenadas duplicadas
duplicates = TruckStop.objects.values('latitude', 'longitude').annotate(
    count=Count('id')
).filter(count__gt=1)

print(f"Se encontraron {len(duplicates)} ubicaciones con registros duplicados.")

merged_count = 0
deleted_count = 0

for dup in duplicates:
    # Obtener todos los registros en esa misma coordenada exacta
    stops = list(TruckStop.objects.filter(
        latitude=dup['latitude'], 
        longitude=dup['longitude']
    ).order_by('-parking_spaces', '-diesel_lanes')) # Ordenar para que el primero sea el más completo
    
    if len(stops) <= 1:
        continue
        
    # El primero será nuestro "Master Record"
    master = stops[0]
    
    # Recorrer los demás y fusionar la información que le falte al master
    for duplicate in stops[1:]:
        # Si el master no tiene parqueos, pero el duplicado sí, se lo pasamos
        if (master.parking_spaces == 0 or master.parking_spaces is None) and duplicate.parking_spaces:
            master.parking_spaces = duplicate.parking_spaces
            
        # Si el master no tiene diesel lanes, pero el duplicado sí
        if (master.diesel_lanes == 0 or master.diesel_lanes is None) and duplicate.diesel_lanes:
            master.diesel_lanes = duplicate.diesel_lanes
            
        # Si el master se llama "Unknown" pero el duplicado tiene nombre real
        if "Unknown" in master.name and "Unknown" not in duplicate.name:
            master.name = duplicate.name
            
        # Si el master no tiene operador pero el duplicado sí
        if master.operator in ['Public Rest Stop', 'Operador Independiente', ''] and duplicate.operator not in ['Public Rest Stop', 'Operador Independiente', '']:
            master.operator = duplicate.operator
            
        # Fusionar amenidades
        for amenity in duplicate.amenities.all():
            master.amenities.add(amenity)
            
        # Borrar el duplicado
        duplicate.delete()
        deleted_count += 1
        
    master.save()
    merged_count += 1

print(f"Se consolidaron {merged_count} ubicaciones únicas.")
print(f"Se eliminaron {deleted_count} iconos duplicados que ensuciaban el mapa.")

# Verificación final
valid_parking = TruckStop.objects.filter(parking_spaces__gt=0).count()
print(f"Total de Truck Stops con datos reales de parqueo tras la limpieza: {valid_parking}")
