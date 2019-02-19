"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from collections import OrderedDict

from bilbycommon.utility.display_names import EMCEE
from bilbycommon.utility.display_names import (
    NUMBER_OF_STEPS,
    NUMBER_OF_STEPS_DISPLAY,
)
from bilbycommon.forms.dynamic import field
from bilbycommon.forms.dynamic.form import DynamicForm
from ...models import SamplerParameter, Sampler

EMCEE_FIELDS_PROPERTIES = OrderedDict([
    (NUMBER_OF_STEPS, {
        'type': field.POSITIVE_INTEGER,
        'label': NUMBER_OF_STEPS_DISPLAY,
        'placeholder': '1000',
        'initial': None,
        'required': True,
    }),
])


class SamplerEmceeParameterForm(DynamicForm):
    """
    Sampler Emcee Parameter Form extending Dynamic Form
    """
    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'data-parameter'
        kwargs['fields_properties'] = EMCEE_FIELDS_PROPERTIES
        self.job = kwargs.pop('job', None)

        super(SamplerEmceeParameterForm, self).__init__(*args, **kwargs)

    def save(self):
        # find the sampler first
        sampler = Sampler.objects.get(job=self.job)
        for name, value in self.cleaned_data.items():
            SamplerParameter.objects.update_or_create(
                sampler=sampler,
                name=name,
                defaults={
                    'value': value,
                }
            )

    def update_from_database(self, job):
        """
        Populates the form field with the values stored in the database
        :param job: instance of job model for which the sampler parameters belong to
        :return: Nothing
        """
        if not job:
            return
        else:

            # check whether the sampler choice is emcee or not
            # if not nothing to populate
            try:
                sampler = Sampler.objects.get(job=job)
                if sampler.sampler_choice != EMCEE:
                    return
            except Sampler.DoesNotExist:
                return

        # iterate over the fields
        for name in EMCEE_FIELDS_PROPERTIES.keys():
            try:
                value = SamplerParameter.objects.get(sampler=sampler, name=name).value
                self.fields[name].initial = value
            except SamplerParameter.DoesNotExist:
                pass
