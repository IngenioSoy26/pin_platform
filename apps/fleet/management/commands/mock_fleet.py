from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.core.models import CarrierCompany
from apps.devices.models import Truck
from apps.hos_monitoring.models import Driver, HOSCompliance, HOSAlert
from apps.weight_monitoring.models import WeightInspection
from apps.fleet.models import Trip

class Command(BaseCommand):
    help = 'Genera o elimina datos ficticios de flota (Conductores, Tractomulas, Viajes) para pruebas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['generate', 'clear'],
            default='generate',
            help='Acción a realizar: "generate" (crear datos falsos) o "clear" (borrar datos falsos).'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Cantidad de registros a generar por cada entidad (solo para action=generate).'
        )

    def handle(self, *args, **kwargs):
        action = kwargs['action']
        count = kwargs['count']

        if action == 'clear':
            self.clear_mock_data()
        elif action == 'generate':
            self.generate_mock_data(count)

    def clear_mock_data(self):
        self.stdout.write("Eliminando datos ficticios...")
        
        # Eliminar HOS Alerts simuladas
        HOSAlert.objects.filter(title__startswith="[SIMULADO]").delete()
        
        # Eliminar Weight Inspections simuladas
        WeightInspection.objects.filter(location__startswith="[SIMULADO]").delete()
        
        # Eliminar viajes simulados
        trips_deleted, _ = Trip.objects.filter(origin_address__startswith="[SIMULADO]").delete()
        
        # Eliminar tractomulas simuladas
        trucks_deleted, _ = Truck.objects.filter(plate__startswith="SIM-").delete()
        
        # Eliminar conductores simulados
        drivers_deleted, _ = Driver.objects.filter(license_number__startswith="SIM-CDL-").delete()
        
        # Eliminar empresas simuladas
        companies_deleted, _ = CarrierCompany.objects.filter(legal_name__startswith="[SIMULADO]").delete()

        self.stdout.write(self.style.SUCCESS(
            f"Limpieza completada: {trips_deleted} viajes, {trucks_deleted} tractomulas, {drivers_deleted} conductores, {companies_deleted} empresas."
        ))

    def generate_mock_data(self, count):
        self.stdout.write("Generando datos ficticios...")

        # 1. Crear empresa simulada
        company, created = CarrierCompany.objects.get_or_create(
            dot_number="9999999",
            defaults={
                'legal_name': '[SIMULADO] Logistics Test Corp',
                'dba_name': 'Logistics Test',
                'status': 'Active'
            }
        )
        if created:
            self.stdout.write(f"Empresa creada: {company.legal_name}")

        # 2. Crear Conductores
        nombres = ['Juan', 'Pedro', 'Luis', 'Carlos', 'Miguel', 'Andrés', 'Diego', 'Fernando', 'Jorge', 'Ricardo']
        apellidos = ['García', 'Rodríguez', 'Martínez', 'Hernández', 'López', 'González', 'Pérez', 'Sánchez', 'Ramírez', 'Torres']
        estados = ['TX', 'CA', 'FL', 'NY', 'IL']
        
        drivers = []
        for i in range(count):
            driver, _ = Driver.objects.get_or_create(
                license_number=f"SIM-CDL-{1000 + i}",
                defaults={
                    'first_name': random.choice(nombres),
                    'last_name': random.choice(apellidos),
                    'license_state': random.choice(estados),
                    'cdl_class': 'A',
                    'hire_date': timezone.now().date() - timedelta(days=random.randint(100, 1000)),
                    'status': 'ACTIVE'
                }
            )
            drivers.append(driver)
            
            # 2.1 Crear cumplimiento HOS simulado para cada conductor
            is_compliant = random.random() > 0.3 # 70% compliant
            
            driving_mins = random.randint(300, 600) if is_compliant else random.randint(661, 720)
            on_duty_mins = driving_mins + random.randint(30, 120)
            if not is_compliant and random.random() > 0.5:
                on_duty_mins = random.randint(841, 900)
                
            HOSCompliance.objects.update_or_create(
                driver=driver,
                defaults={
                    'cycle_start': timezone.now() - timedelta(days=random.randint(1, 6)),
                    'cycle_type': '70_8',
                    'driving_time_today': driving_mins,
                    'on_duty_time_today': on_duty_mins,
                    'consecutive_driving_time': random.randint(100, 400),
                    'hours_8days': random.randint(2000, 4100) if is_compliant else random.randint(4201, 4300),
                    'is_compliant': is_compliant
                }
            )
            
            # 2.2 Si no es compliant, generamos una alerta
            if not is_compliant:
                HOSAlert.objects.get_or_create(
                    driver=driver,
                    title="[SIMULADO] Límite Excedido",
                    defaults={
                        'alert_type': random.choice(['VIOLATION_11H', 'VIOLATION_14H', 'VIOLATION_60_70H']),
                        'severity': 'VIOLATION',
                        'message': "El conductor ha superado los límites establecidos por la FMCSA.",
                        'current_value': driving_mins / 60.0,
                        'threshold_value': 11.0,
                        'status': 'ACTIVE'
                    }
                )
                
        self.stdout.write(f"Conductores verificados/creados: {len(drivers)}")

        # 3. Crear Tractomulas
        marcas = ['Freightliner', 'Kenworth', 'Peterbilt', 'Volvo', 'Mack', 'International']
        modelos = ['Cascadia', 'T680', '579', 'VNL', 'Anthem', 'LT Series']
        
        trucks = []
        for i in range(count):
            # Coordenadas aleatorias dentro de Estados Unidos para visualización inicial
            lat = random.uniform(30.0, 45.0)
            lon = random.uniform(-115.0, -80.0)
            
            truck, _ = Truck.objects.get_or_create(
                vin=f"SIM1FTWW31A{100000 + i}",
                defaults={
                    'plate': f"SIM-{100 + i}",
                    'brand': random.choice(marcas),
                    'model': random.choice(modelos),
                    'year': random.randint(2018, 2024),
                    'num_tires': 18,
                    'carrier': company,
                    'status': 'ACTIVE',
                    'latitude': lat,
                    'longitude': lon
                }
            )
            trucks.append(truck)
        self.stdout.write(f"Tractomulas verificadas/creadas: {len(trucks)}")

        # 4. Crear Viajes
        ciudades = [
            'Los Angeles, CA', 'Dallas, TX', 'Houston, TX', 'Chicago, IL', 
            'Miami, FL', 'Atlanta, GA', 'New York, NY', 'Phoenix, AZ', 
            'Denver, CO', 'Seattle, WA'
        ]
        
        estados_viaje = ['PENDING', 'IN_TRANSIT', 'COMPLETED']
        
        for i in range(count):
            origen = random.choice(ciudades)
            destino = random.choice([c for c in ciudades if c != origen])
            
            # Fechas
            start_date = timezone.now() + timedelta(days=random.randint(-5, 5))
            end_date = start_date + timedelta(days=random.randint(1, 4))
            
            trip_status = random.choice(estados_viaje)
            
            Trip.objects.create(
                company=company,
                truck=random.choice(trucks),
                driver=random.choice(drivers),
                origin_address=f"[SIMULADO] {origen}",
                destination_address=f"[SIMULADO] {destino}",
                scheduled_start=start_date,
                scheduled_end=end_date,
                status=trip_status
            )
            
        # 5. Crear Inspecciones de Peso Simuladas
        tipos_pesaje = ['WIM', 'STATIC', 'ESTIMATED']
        for i in range(count * 2): # Generamos el doble de pesajes
            is_overweight = random.random() > 0.85 # 15% de probabilidad de sobrepeso
            
            base_weight = random.uniform(60000.0, 79000.0)
            if is_overweight:
                base_weight = random.uniform(80500.0, 85000.0)
                
            WeightInspection.objects.create(
                truck=random.choice(trucks),
                timestamp=timezone.now() - timedelta(days=random.randint(0, 15), hours=random.randint(1, 23)),
                location=f"[SIMULADO] Báscula {random.choice(ciudades)}",
                inspection_type=random.choice(tipos_pesaje),
                gross_weight=base_weight,
                axle_weights={"steer": 12000, "drive": 34000, "trailer": base_weight - 46000},
                is_overweight=is_overweight
            )
            
        self.stdout.write(self.style.SUCCESS(f"¡Se generaron {count} viajes y {count*2} pesajes de prueba exitosamente!"))
