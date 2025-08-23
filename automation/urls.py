from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("jobs/", views.jobs_list, name="jobs_list"),
    path("jobs/<uuid:job_id>/", views.job_detail, name="job_detail"),
    path("api/status/<uuid:job_id>/", api.job_status, name="job_status"),
]
