from .models import SizeWeightRegulation

class RegulationService:
    @staticmethod
    def get_state_limits(state_code):
        return SizeWeightRegulation.objects.filter(state=state_code).first()
