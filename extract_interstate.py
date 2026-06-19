import re

input_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\2026\06\NTAD_National_Highway_System_-2908344783259962276_UVU7pi8.geojson'
output_file = r'C:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\media\datasets\routes_interstate.geojson'

print("Iniciando extracción por streaming...")

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8') as fout:
    # Escribir el inicio del FeatureCollection
    fout.write('{"type":"FeatureCollection","features":[')
    
    buffer = ""
    first_feature = True
    
    # Procesar línea por línea o en bloques
    while True:
        chunk = fin.read(1024 * 1024 * 10) # 10MB chunks
        if not chunk:
            break
        
        buffer += chunk
        
        # Buscar features completos: {"type":"Feature", ... }
        # Una forma simple es dividir por '{"type":"Feature"'
        parts = buffer.split('{"type":"Feature"')
        
        # El último elemento podría estar incompleto, lo dejamos en el buffer
        buffer = parts.pop()
        
        for p in parts:
            if not p.strip():
                continue
                
            # Reconstruir el feature
            feature_str = '{"type":"Feature"' + p
            
            # Limpiar la coma final si existe
            if feature_str.endswith(','):
                feature_str = feature_str[:-1]
                
            # Filtrar: solo mantener si es Interstate (SIGNT1: "I") o si el nombre contiene "I-"
            # O mejor, para que sea ligero, extraer solo una fracción de las rutas.
            if '"SIGNT1":"I"' in feature_str or '"SIGNT1": "I"' in feature_str:
                if not first_feature:
                    fout.write(',')
                fout.write(feature_str)
                first_feature = False

    # Escribir el feature final si quedó en el buffer y es válido
    if buffer.strip() and '"SIGNT1":"I"' in buffer:
        feature_str = '{"type":"Feature"' + buffer
        # Quitar el ']}' del final del archivo original si está ahí
        feature_str = feature_str.replace(']}', '')
        if feature_str.endswith(','):
            feature_str = feature_str[:-1]
        if not first_feature:
            fout.write(',')
        fout.write(feature_str)

    fout.write(']}')

import os
print("Terminado.")
print(f"Tamaño nuevo: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
