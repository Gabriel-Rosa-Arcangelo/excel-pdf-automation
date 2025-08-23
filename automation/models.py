import uuid
from django.db import models

class UploadJob(models.Model):
    STATUS_CHOICES = [
        ("pending","pending"),("processing","processing"),
        ("done","done"),("failed","failed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    original_file = models.FileField(upload_to="uploads/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.PositiveIntegerField(default=0)  # 0..100
    log = models.JSONField(default=list, blank=True)
    report_count = models.PositiveIntegerField(default=0)

    def add_log(self, level, msg, extra=None):
        entry = {"level": level, "msg": msg}
        if extra:
            entry["extra"] = extra
        self.log = (self.log or []) + [entry]
        self.save(update_fields=["log"])

class GeneratedReport(models.Model):
    job = models.ForeignKey(UploadJob, on_delete=models.CASCADE, related_name="reports")
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="reports/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
