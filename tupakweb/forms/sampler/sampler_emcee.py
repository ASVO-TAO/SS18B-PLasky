from collections import OrderedDict

from ...utility.display_names import EMCEE
from ..dynamic import field
from ...models import SamplerParameter, Sampler
from ..dynamic.form import DynamicForm

EMCEE_FIELDS_PROPERTIES = OrderedDict([
    ('number_of_steps', {
        'type': field.POSITIVE_INTEGER,
        'label': 'Number of Steps',
        'placeholder': '1000',
        'initial': None,
        'required': True,
    }),
])


class SamplerEmceeParameterForm(DynamicForm):

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
        if not job:
            return
        else:
            try:
                sampler = Sampler.objects.get(job=job)
                if sampler.sampler_choice != EMCEE:
                    return
            except Sampler.DoesNotExist:
                return

        for name in EMCEE_FIELDS_PROPERTIES.keys():
            try:
                value = SamplerParameter.objects.get(sampler=sampler, name=name).value
                self.fields[name].initial = value
            except SamplerParameter.DoesNotExist:
                continue
