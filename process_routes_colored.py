import json
import os

input_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\2026\06\NTAD_National_Highway_System_-2908344783259962276_UVU7pi8.geojson'
output_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\routes_colored_simplified.geojson'

def round_coords(coords):
    if not coords:
        return coords
    if isinstance(coords[0], list):
        return [round_coords(c) for c in coords]
    else:
        # 2 decimales = aprox 1.1 km de precisión. Suficiente para ver toda Norteamérica y reduce el archivo dramáticamente
        return [round(c, 2) for c in coords]

def deduplicate_points(line):
    # Elimina puntos consecutivos que, tras el redondeo, terminaron en la misma coordenada exacta
    if not line: return line
    if isinstance(line[0], (int, float)): return line # Point
    if isinstance(line[0], list) and isinstance(line[0][0], (int, float)): # LineString
        new_line = [line[0]]
        for pt in line[1:]:
            if pt != new_line[-1]:
                new_line.append(pt)
        # Si quedó solo 1 punto, lo duplicamos para que sea una línea válida
        if len(new_line) == 1:
            new_line.append(new_line[0])
        return new_line
    elif isinstance(line[0], list) and isinstance(line[0][0], list): # MultiLineString
        return [deduplicate_points(part) for part in line]
    return line

print("Cargando JSON (544MB)...")
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_features = []
for f in data['features']:
    props = f.get('properties', {})
    signt = props.get('SIGNT1', '')
    
    # Clasificación de Rutas
    t = 'O'
    if signt == 'I': t = 'I'
    elif signt == 'U': t = 'U'
    elif signt == 'S': t = 'S'
    
    new_props = {'t': t}
    if 'LNAME' in props and props['LNAME']:
        new_props['n'] = props['LNAME']
    
    geom = f.get('geometry')
    if geom and geom.get('coordinates'):
        coords = round_coords(geom['coordinates'])
        geom['coordinates'] = deduplicate_points(coords)
        
    new_features.append({
        'type': 'Feature',
        'geometry': geom,
        'properties': new_props
    })

data['features'] = new_features

print("Guardando JSON final...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, separators=(',', ':'))

print(f"Tamaño final: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
