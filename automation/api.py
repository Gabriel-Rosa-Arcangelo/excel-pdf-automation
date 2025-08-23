from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import UploadJob

@api_view(["GET"])
def job_status(request, job_id):
    job = get_object_or_404(UploadJob, pk=job_id)
    reports = [{"filename": r.filename, "url": r.file.url} for r in job.reports.all()]
    return Response({
        "id": str(job.id),
        "status": job.status,
        "progress": job.progress,
        "report_count": job.report_count,
        "log": job.log[-5:],
        "reports": reports,
    })
