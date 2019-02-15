"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import job

urlpatterns = [
    path('new_job/', login_required(job.new_job), name='new_g_job'),
]
