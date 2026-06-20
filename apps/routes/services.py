from .models import HighwayRoute

class RouteService:
    @staticmethod
    def get_routes_by_state(state_code):
        return HighwayRoute.objects.filter(state=state_code)
