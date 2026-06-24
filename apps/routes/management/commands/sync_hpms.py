from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.data_ingestion.etl import run_etl_job
from apps.data_ingestion.models import DataSource, ETLJob
from apps.routes.services import RouteService


class Command(BaseCommand):
    help = "Sincroniza HPMS con PIN: carga el CSV maestro, descubre esquemas remotos y genera matches con rutas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default=str(settings.DATA_DIR / "Highway_Performance_Monitoring_System__HPMS_.csv"),
            help="Ruta al CSV maestro de HPMS dentro de la carpeta data.",
        )
        parser.add_argument(
            "--discover",
            action="store_true",
            help="Intenta descubrir capas y campos desde los FeatureServer remotos.",
        )
        parser.add_argument(
            "--match",
            action="store_true",
            help="Genera matches heurísticos entre HighwayRoute y segmentos HPMS.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Límite de estados a descubrir cuando se usa --discover.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            raise CommandError(f"No se encontró el CSV maestro de HPMS en {csv_path}")

        source, _ = DataSource.objects.update_or_create(
            name=csv_path.name,
            defaults={
                "file_path": str(csv_path),
                "file_type": "CSV",
                "schema": {"type": "hpms_inventory_index"},
            },
        )
        job = ETLJob.objects.create(dataset=source, status="PENDING")
        run_etl_job(job)
        job.refresh_from_db()
        if job.status != "COMPLETED":
            raise CommandError(f"Falló la carga del CSV HPMS:\n{job.error_log}")

        self.stdout.write(self.style.SUCCESS("Inventario HPMS cargado correctamente."))

        if options["discover"]:
            results = RouteService.discover_all_hpms_sources(limit=options["limit"])
            for result in results:
                if result.get("error"):
                    self.stdout.write(self.style.WARNING(f"{result['source']}: {result['error']}"))
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{result['source']}: capas={result['discovered_layers']} campos={result['discovered_fields']}"
                        )
                    )

        if options["match"]:
            result = RouteService.match_segments_to_routes()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Matches generados: nuevos={result['matched_routes']} total={result['total_matches']}"
                )
            )

        summary = RouteService.summarize_hpms()
        self.stdout.write(self.style.SUCCESS(f"Resumen HPMS: {summary}"))
