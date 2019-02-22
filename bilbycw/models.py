from django.db import models

from bilbycommon.models import JobCommon
from bilbycommon.utility.display_names import *


class BilbyCWJob(JobCommon):
    """
    BilbyBJob model extending HpcJob
    """

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
        :return: Bilby BilbyBJob instance
        """
        from bilbycommon.utility.job import BilbyJob
        return BilbyJob(job_id=self.pk, light=True)

    def save(self, *args, **kwargs):
        """
        Overriding save method to insert the type GRAVITATIONAL
        :param args: arguments passed to method
        :param kwargs: keyword arguments passed to the method
        """
        self.job_type = CONTINUOUS_WAVE
        super().save(*args, **kwargs)

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


class DataSource(models.Model):
    """
    Model to store Data Source Information
    """
    job = models.ForeignKey(JobCommon, on_delete=models.CASCADE, related_name='g_job_data_source')

    DATA_SOURCES = [
        (REAL_DATA, REAL_DATA_DISPLAY),
        (FAKE_DATA, FAKE_DATA_DISPLAY),
    ]

    data_source = models.CharField(max_length=55, choices=DATA_SOURCES, default=REAL_DATA)

    def __str__(self):
        return '{} ({})'.format(self.data_source, self.job.name)

    def as_json(self):
        return dict(
            id=self.id,
            value=dict(
                job=self.job.id,
                choice=self.data_source,
            ),
        )
