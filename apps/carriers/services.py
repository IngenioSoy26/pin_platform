from .models import Carrier

class CarrierService:
    @staticmethod
    def get_top_carriers(limit=10):
        return Carrier.objects.order_by('-num_power_units')[:limit]
