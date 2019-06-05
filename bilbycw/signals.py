"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


from .models import (
    BilbyCWJob,
    EngineParameter,
    ViterbiParameter,
    OutputParameter,
)


@receiver(post_save, sender=BilbyCWJob, dispatch_uid='update_non_form_parameters')
def update_non_form_parameters(instance, **kwargs):
    """
    Signal to update the non form parameters for the Bilby CW Job. It requires few predefined parameters which are
    not modified by the user. This signal method sets those parameter as long as a job is set.
    :param instance: instance of Bilby Job
    :param kwargs: keyward arguments
    :return: Nothing
    """
    if instance.pk:
        EngineParameter.objects.update_or_create(
            job=instance,
            name='implementation',
            defaults={
                'value': 'CJS',
            },
        )
        EngineParameter.objects.update_or_create(
            job=instance,
            name='bandWingSize',
            defaults={
                'value': '1.0',
            },
        )
        EngineParameter.objects.update_or_create(
            job=instance,
            name='atomcache',
            defaults={
                'value': '/atoms',
            },
        )
        ViterbiParameter.objects.update_or_create(
            job=instance,
            name='driftTime',
            defaults={
                'value': '1d',
            }
        )
        OutputParameter.objects.update_or_create(
            job=instance,
            name='dir',
            defaults={
                'value': '/output'
            }
        )
        OutputParameter.objects.update_or_create(
            job=instance,
            name='capture',
            defaults={
                'value': '[\'bestpath\', ]',
            }
        )
