"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from .views.job import job, jobs

urlpatterns = [
    path('new_job/', login_required(job.new_job), name='new_pe_job'),
    path('edit_job/<job_id>/', login_required(jobs.edit_job), name='edit_b_job'),
    path('cancel_job/<job_id>/', login_required(jobs.cancel_job), name='cancel_job'),
    path('copy_job/<job_id>/', login_required(jobs.copy_job), name='copy_job'),
    path('delete_job/<job_id>/', login_required(jobs.delete_job), name='delete_job'),
    path('make_job_private/<job_id>/', login_required(jobs.make_job_private), name='make_job_private'),
    path('make_job_public/<job_id>/', login_required(jobs.make_job_public), name='make_job_public'),
    path('job/<job_id>/', login_required(jobs.view_job), name='job'),

    # BilbyPEJob asset retrieval
    path('download_asset/<int:job_id>/<int:download>/<path:file_path>', login_required(jobs.download_asset),
         name='download_asset'),
]
