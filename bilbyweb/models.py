from django.conf import settings
from django.db import models

from django_hpc_job_controller.models import HpcJob
from .utility.display_names import *


class Job(HpcJob):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_job', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        (NONE, NONE_DISPLAY),
        (PUBLIC, PUBLIC_DISPLAY),
    ]

    extra_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=False, default=NONE)

    @property
    def status_display(self):
        if self.extra_status != NONE:
            return DISPLAY_NAME_MAP[self.extra_status]
        if self.job_status in DISPLAY_NAME_MAP_HPC_JOB:
            return DISPLAY_NAME_MAP[DISPLAY_NAME_MAP_HPC_JOB[self.job_status]]
        return "Unknown"

    @property
    def status(self):
        if self.extra_status != NONE:
            return self.extra_status
        if self.job_status in DISPLAY_NAME_MAP_HPC_JOB:
            return DISPLAY_NAME_MAP_HPC_JOB[self.job_status]
        return "unknown"

    @property
    def bilby_job(self):
        from bilbyweb.utility.job import BilbyJob
        return BilbyJob(job_id=self.pk, light=True)

    creation_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    json_representation = models.TextField(null=True, blank=True)

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


class Data(models.Model):
    job = models.OneToOneField(Job, related_name='job_data', on_delete=models.CASCADE)

    DATA_CHOICES = [
        (SIMULATED_DATA, SIMULATED_DATA_DISPLAY),
        (OPEN_DATA, OPEN_DATA_DISPLAY),
    ]

    data_choice = models.CharField(max_length=20, choices=DATA_CHOICES, default=SIMULATED_DATA)

    def __str__(self):
        return '{} ({})'.format(self.data_choice, self.job.name)

    def as_json(self):
        return dict(
            id=self.id,
            value=dict(
                job=self.job.id,
                choice=self.data_choice,
            ),
        )


class DataParameter(models.Model):
    data = models.ForeignKey(Data, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, blank=False, null=False)
    value = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return '{} - {} ({})'.format(self.name, self.value, self.data)


class Signal(models.Model):
    job = models.OneToOneField(Job, related_name='job_signal', on_delete=models.CASCADE)

    SIGNAL_CHOICES = [
        (SKIP, SKIP_DISPLAY),
        (BINARY_BLACK_HOLE, BINARY_BLACK_HOLE_DISPLAY),
    ]

    signal_choice = models.CharField(max_length=50, choices=SIGNAL_CHOICES, default=SKIP)
    signal_model = models.CharField(max_length=50, choices=SIGNAL_CHOICES[1:])

    def __str__(self):
        return '{} - ({}[{}])'.format(self.signal_choice, self.job.name, self.job.user.username)


class SignalParameter(models.Model):
    signal = models.ForeignKey(Signal, related_name='signal_signal_parameter', on_delete=models.CASCADE)

    NAME_CHOICES = [
        (MASS1, MASS1_DISPLAY),
        (MASS2, MASS2_DISPLAY),
        (LUMINOSITY_DISTANCE, LUMINOSITY_DISTANCE_DISPLAY),
        (IOTA, IOTA_DISPLAY),
        (PSI, PSI_DISPLAY),
        (PHASE, PHASE_DISPLAY),
        (GEOCENT_TIME, GEOCENT_TIME_DISPLAY),
        (RA, RA_DISPLAY),
        (DEC, DEC_DISPLAY),
    ]

    name = models.CharField(max_length=20, choices=NAME_CHOICES, blank=False, null=False)
    value = models.FloatField(null=True, blank=True)

    def __str__(self):
        return '{}: {} ({})'.format(self.name, self.value, self.signal)


class Prior(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_prior')
    name = models.CharField(max_length=50, blank=False, null=False)
    CHOICES = [
        (FIXED, FIXED_DISPLAY),
        (UNIFORM, UNIFORM_DISPLAY),
    ]
    prior_choice = models.CharField(max_length=20, choices=CHOICES, default=FIXED, blank=True)
    fixed_value = models.FloatField(blank=True, null=True)
    uniform_min_value = models.FloatField(blank=True, null=True)
    uniform_max_value = models.FloatField(blank=True, null=True)

    def get_display_value(self):
        if self.prior_choice == FIXED:
            return '{}'.format(self.fixed_value)
        elif self.prior_choice == UNIFORM:
            return '[{}, {}]'.format(self.uniform_min_value, self.uniform_max_value)

    class Meta:
        unique_together = (
            ('job', 'name'),
        )


class Sampler(models.Model):
    job = models.OneToOneField(Job, related_name='job_sampler', on_delete=models.CASCADE)

    SAMPLER_CHOICES = [
        (DYNESTY, DYNESTY_DISPLAY),
        (NESTLE, NESTLE_DISPLAY),
        (EMCEE, EMCEE_DISPLAY),
    ]

    sampler_choice = models.CharField(max_length=15, choices=SAMPLER_CHOICES, default=DYNESTY)

    def __str__(self):
        return '{} ({})'.format(self.sampler_choice, self.job.name)

    def as_json(self):
        return dict(
            id=self.id,
            value=dict(
                job=self.job.id,
                choice=self.sampler_choice,
            ),
        )


class SamplerParameter(models.Model):
    sampler = models.ForeignKey(Sampler, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False, null=False)
    value = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return '{} - {} ({})'.format(self.name, self.value, self.sampler)
