from django.db import models
from django.conf import settings

from django_hpc_job_controller.models import HpcJob
from .utility.display_names import *


class JobCommon(HpcJob):
    """
    BilbyBJob model extending HpcJob
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_job', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        (NONE, NONE_DISPLAY),
        (PUBLIC, PUBLIC_DISPLAY),
    ]

    extra_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=False, default=NONE)
    creation_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    json_representation = models.TextField(null=True, blank=True)

    JOB_TYPES = [
        (BAYESIAN, BAYESIAN_DISPLAY),
        (GRAVITATIONAL, GRAVITATIONAL_DISPLAY),
    ]

    job_type = models.CharField(max_length=20, choices=JOB_TYPES, blank=False, default=BAYESIAN)

    @property
    def status_display(self):
        """
        Finds and return the corresponding status display for a status
        :return: String of status display
        """
        if self.extra_status != NONE:
            return DISPLAY_NAME_MAP[self.extra_status]
        if self.job_status in DISPLAY_NAME_MAP_HPC_JOB:
            return DISPLAY_NAME_MAP[DISPLAY_NAME_MAP_HPC_JOB[self.job_status]]
        return "Unknown"

    @property
    def status(self):
        """
        Finds and return the corresponding status for a status number
        :return: String of status
        """
        if self.extra_status != NONE:
            return self.extra_status
        if self.job_status in DISPLAY_NAME_MAP_HPC_JOB:
            return DISPLAY_NAME_MAP_HPC_JOB[self.job_status]
        return "unknown"

    @property
    def bilby_job(self):
        """
        Creates a LIGHT bilby job instance usually for list actions
        :return: Bilby Job instance
        """
        raise NotImplemented

    def get_actual_job(self):
        from bilbyweb.models import BilbyBJob
        from bilbygw.models import BilbyGJob

        if self.job_type == BAYESIAN:
            job = BilbyBJob.objects.get(id=self.id)
        elif self.job_type == GRAVITATIONAL:
            job = BilbyGJob.objects.get(id=self.id)
        else:
            job = None

        return job

    class Meta:
        unique_together = (
            ('user', 'name'),
        )

    def __str__(self):
        return '{}'.format(self.name)

    def as_json(self):
        return dict(
            id=self.id,
            value=dict(
                name=self.name,
                username=self.user.username,
                status=self.status,
                creation_time=self.creation_time.strftime('%d %b %Y %I:%m %p'),
            ),
        )
