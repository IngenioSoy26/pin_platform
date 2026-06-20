import os
import django
import sys

# Configurar el entorno de Django para poder leer los modelos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.apps import apps

def generate_markdown():
    md = "# 🗄️ Informe Arquitectónico de Base de Datos - PIN Platform\n\n"
    md += "> **Clasificación:** Confidencial / Arquitectura de Software\n"
    md += "> **Descripción:** Este documento técnico detalla la estructura relacional completa de la plataforma logística PIN. Incluye un Diagrama Entidad-Relación (ERD) generado dinámicamente y un diccionario de datos exhaustivo de grado empresarial para auditoría y desarrollo.\n\n"
    md += "---\n\n"
    
    md += "## 📊 1. Diagrama Entidad-Relación (ERD)\n\n"
    md += "> **Nota Visual:** El siguiente diagrama utiliza sintaxis *Mermaid.js*. En visualizadores compatibles (como GitHub, GitLab, Notion o VS Code con extensión de Markdown), se renderizará automáticamente como un gráfico vectorial interactivo y profesional.\n\n"
    md += "```mermaid\n"
    md += "erDiagram\n"

    # Filtrar modelos propios del proyecto (ignorando los genéricos de Django excepto User)
    project_apps = ['core', 'fleet', 'hos_monitoring', 'weight_monitoring', 'iot_ingestion', 'alerts', 'recommendations', 'analytics', 'carriers', 'fuel_alternative', 'recycling', 'regulation', 'routes', 'stations']
    models = []
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('apps.') or app_config.label in project_apps:
            models.extend(app_config.get_models())
    
    # Añadir User de Django para que las relaciones foráneas no queden huérfanas
    from django.contrib.auth.models import User
    if User not in models:
        models.append(User)

    # Generar sintaxis Mermaid ERD
    for model in models:
        md += f"    {model.__name__} {{\n"
        for field in model._meta.fields:
            field_type = field.get_internal_type().replace('Field', '')
            md += f"        {field_type} {field.name}\n"
        md += "    }\n"
        
        for field in model._meta.fields:
            if field.is_relation and field.related_model in models:
                # Determinar tipo de relación (1:N, 1:1)
                rel_type = "}o--||" if field.many_to_one else "||--||" if field.one_to_one else "}o--o{"
                md += f"    {model.__name__} {rel_type} {field.related_model.__name__} : \"{field.name}\"\n"
    
    md += "```\n\n"
    md += "---\n\n"
    md += "## 📖 2. Diccionario de Datos (Estructuras de Tablas)\n\n"
    md += "A continuación se detalla cada tabla de la base de datos relacional, con sus respectivos tipos de datos, restricciones y llaves foráneas.\n\n"

    for model in models:
        if model.__name__ == 'User':
            continue # Saltamos la tabla base de Django para enfocarnos en las de la Maestría

        md += f"### 🗂️ Tabla: `{model._meta.db_table}`\n\n"
        md += f"- **Entidad de Negocio:** `{model.__name__}`\n"
        md += f"- **Módulo / Microservicio:** `{model._meta.app_label.capitalize()}`\n"
        md += f"- **Descripción:** Representa {model._meta.verbose_name.lower()} dentro de la plataforma.\n\n"
        
        # Generación de la tabla Markdown profesional
        md += "| Campo / Atributo | Tipo SQL (Django) | ¿Permite Nulo? | ¿Único? | Relación (Foreign Key) | Descripción de Negocio |\n"
        md += "|------------------|-------------------|----------------|---------|------------------------|------------------------|\n"
        
        for field in model._meta.fields:
            fk = f"🔗 `{field.related_model.__name__}`" if field.is_relation and field.related_model else "-"
            nullable = "✅ Sí" if field.null else "❌ No"
            unique = "✅ Sí" if field.unique else "❌ No"
            f_type = field.get_internal_type().replace('Field', '')
            if f_type == "Char": f_type = f"Varchar({field.max_length})"
            
            desc = field.verbose_name.capitalize()
            if field.primary_key:
                desc = "🔑 Llave Primaria (Primary Key). " + desc
            
            md += f"| **`{field.name}`** | `{f_type}` | {nullable} | {unique} | {fk} | {desc} |\n"
        
        md += "\n<br>\n\n"

    # Guardar en archivo
    os.makedirs('docs', exist_ok=True)
    with open('docs/INFORME_BASE_DATOS.md', 'w', encoding='utf-8') as f:
        f.write(md)

if __name__ == "__main__":
    generate_markdown()
    print("Informe generado exitosamente en docs/INFORME_BASE_DATOS.md")