from django.contrib import admin
from .models import UploadJob, GeneratedReport

@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ("id","created_at","status","progress","report_count")

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("filename","job","created_at")
