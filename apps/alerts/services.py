from .models import Alert

class AlertEngine:
    @staticmethod
    def create_alert(truck, alert_type, severity, title, message, sensor=None, **kwargs):
        alert = Alert.objects.create(
            truck=truck,
            sensor=sensor,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            **kwargs
        )
        return alert
        
    @staticmethod
    def check_tire_alerts(reading):
        pass # To be implemented
        
    @staticmethod
    def check_hos_alerts(driver):
        pass # To be implemented
        
    @staticmethod
    def check_weight_alerts(truck):
        pass # To be implemented
