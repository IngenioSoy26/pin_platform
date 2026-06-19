from django.contrib import admin

from apps.hos_monitoring.models import Driver, DriverLog, HOSAlert, HOSCompliance


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "license_number", "license_state", "status")
    search_fields = ("first_name", "last_name", "license_number")
    list_filter = ("status", "license_state", "cdl_class")


@admin.register(DriverLog)
class DriverLogAdmin(admin.ModelAdmin):
    list_display = ("driver", "truck", "status", "timestamp", "odometer")
    search_fields = ("driver__first_name", "driver__last_name", "location")
    list_filter = ("status",)
    date_hierarchy = "timestamp"


@admin.register(HOSCompliance)
class HOSComplianceAdmin(admin.ModelAdmin):
    list_display = ("driver", "cycle_type", "driving_time_today", "on_duty_time_today", "is_compliant")
    list_filter = ("cycle_type", "is_compliant", "is_short_haul", "adverse_conditions")


@admin.register(HOSAlert)
class HOSAlertAdmin(admin.ModelAdmin):
    list_display = ("driver", "alert_type", "severity", "status", "timestamp")
    list_filter = ("severity", "status", "alert_type")
    search_fields = ("driver__first_name", "driver__last_name", "title", "message")
