import json

input_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\2026\06\NTAD_National_Highway_System_-2908344783259962276_UVU7pi8.geojson'
output_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\routes_simplified.geojson'

def round_coords(coords):
    if isinstance(coords[0], list):
        return [round_coords(c) for c in coords]
    else:
        return [round(c, 3) for c in coords]

print("Cargando JSON original...")
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_features = []
for f in data['features']:
    props = f.get('properties', {})
    new_props = {}
    if 'LNAME' in props and props['LNAME']:
        new_props['n'] = props['LNAME'] # shorten key
    
    geom = f.get('geometry')
    if geom and geom.get('coordinates'):
        geom['coordinates'] = round_coords(geom['coordinates'])
        
    new_features.append({
        'type': 'Feature',
        'geometry': geom,
        'properties': new_props
    })

data['features'] = new_features

print("Guardando JSON ultra-simplificado...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, separators=(',', ':'))
