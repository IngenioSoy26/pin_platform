import os
from django.apps import apps

markdown_content = '# Informe Completo de Base de Datos - PIN Platform\n\n'
markdown_content += 'Este documento describe la estructura relacional de la base de datos de la plataforma PIN, incluyendo el diagrama Entidad-Relación (ERD) generado automáticamente y el diccionario de datos detallado de cada módulo y aplicación.\n\n'
markdown_content += '## 1. Diagrama Entidad-Relación (ERD)\n\n'
markdown_content += '*(Nota: Puedes visualizar este diagrama en GitHub o cualquier editor de Markdown compatible con Mermaid.js)*\n\n'
markdown_content += '```mermaid\nerDiagram\n'

# Filtrar modelos propios del proyecto (y mantener el de Usuario para las relaciones)
my_models = [m for m in apps.get_models() if not m.__module__.startswith('django.') or m.__name__ == 'User']
my_models = [m for m in my_models if not m.__module__.startswith('django.contrib.admin') and not m.__module__.startswith('django.contrib.contenttypes') and not m.__module__.startswith('django.contrib.sessions')]

for model in my_models:
    model_name = model.__name__
    markdown_content += f'    {model_name} {{\n'
    for field in model._meta.fields:
        field_type = field.get_internal_type()
        markdown_content += f'        {field_type} {field.name}\n'
    markdown_content += '    }\n'
    
    for field in model._meta.fields:
        if field.is_relation and field.related_model and field.related_model in my_models:
            rel_model_name = field.related_model.__name__
            if field.many_to_one:
                rel = '}o--||'
            elif field.one_to_one:
                rel = '||--||'
            else:
                rel = '}o--||'
            markdown_content += f'    {model_name} {rel} {rel_model_name} : "{field.name}"\n'

markdown_content += '```\n\n'
markdown_content += '---\n\n'
markdown_content += '## 2. Diccionario de Datos (Estructura de Tablas)\n\n'

for model in my_models:
    if model.__name__ == 'User':
        continue # Saltamos la tabla estándar de Django para enfocarnos en las de negocio
    
    markdown_content += f'### Tabla: `{model._meta.db_table}`\n'
    markdown_content += f'- **Modelo (Clase):** `{model.__name__}`\n'
    markdown_content += f'- **Módulo / Aplicación:** `{model._meta.app_label}`\n\n'
    
    markdown_content += '| Atributo / Campo | Tipo de Dato | ¿Nulo? | ¿Único? | Clave Foránea | Descripción |\n'
    markdown_content += '|------------------|--------------|--------|---------|---------------|-------------|\n'
    for field in model._meta.fields:
        fk_info = f'`{field.related_model.__name__}`' if field.is_relation and field.related_model else '-'
        desc = field.verbose_name.capitalize() if field.verbose_name else '-'
        null_val = 'Sí' if field.null else 'No'
        unique_val = 'Sí' if field.unique else 'No'
        markdown_content += f'| `{field.name}` | `{field.get_internal_type()}` | {null_val} | {unique_val} | {fk_info} | {desc} |\n'
    markdown_content += '\n'

with open('docs/INFORME_BASE_DATOS.md', 'w', encoding='utf-8') as f:
    f.write(markdown_content)
print('INFORME GENERADO CORRECTAMENTE')