"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from .views.job import job, jobs

urlpatterns = [
    path('new_job/', login_required(job.new_job), name='new_pe_job'),
    path('edit_job/<job_id>/', login_required(jobs.edit_job), name='edit_b_job'),
    path('job/<job_id>/', login_required(jobs.view_job), name='job'),

    # BilbyPEJob asset retrieval
    path('download_asset/<int:job_id>/<int:download>/<path:file_path>', login_required(jobs.download_asset),
         name='download_asset'),
]
