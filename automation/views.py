from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadJob
from .tasks import process_upload_job

def upload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        job = UploadJob.objects.create(original_file=request.FILES["file"])
        job.add_log("info","File received")
        process_upload_job.delay(str(job.id))
        return redirect("job_detail", job_id=job.id)
    return render(request, "automation/upload.html")

def jobs_list(request):
    jobs = UploadJob.objects.order_by("-created_at")[:50]
    return render(request, "automation/jobs_list.html", {"jobs": jobs})

def job_detail(request, job_id):
    job = get_object_or_404(UploadJob, pk=job_id)
    return render(request, "automation/job_detail.html", {"job": job})
