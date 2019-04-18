"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import job, jobs

urlpatterns = [
    path('new_job/', login_required(job.new_job), name='new_cw_job'),
    path('job/<job_id>/', login_required(jobs.view_job), name='view_cw_job'),
]
