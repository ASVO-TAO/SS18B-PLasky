"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from collections import OrderedDict

from bilbycommon.forms.dynamic.form import DynamicForm
from bilbycommon.forms.dynamic import field
from bilbycommon.utility.display_names import (
    GLOB,
    GLOB_DISPLAY,
    START_TIME_CW,
    START_TIME_CW_DISPLAY,
    DURATION,
    DURATION_DISPLAY,
    O1,
    O1_DISPLAY,
    O2,
    O2_DISPLAY,
    REAL_DATA,
)

from ...models import (
    DataSource,
    DataParameter,
)

GLOB_CHOICES = [
    (O1, O1_DISPLAY),
    (O2, O2_DISPLAY),
]

FIELDS_PROPERTIES = OrderedDict([
    (GLOB, {
        'type': field.SELECT,
        'label': GLOB_DISPLAY,
        'initial': None,
        'required': True,
        'choices': GLOB_CHOICES,
    }),
    (START_TIME_CW, {
        'type': field.INTEGER,
        'label': START_TIME_CW_DISPLAY,
        'placeholder': '10',
        'initial': None,
        'required': True,
    }),
    (DURATION, {
        'type': field.DURATION,
        'label': DURATION_DISPLAY,
        'placeholder': '5/10m/2h/30d',
        'initial': None,
        'required': True,
    }),
])


class DataParameterRealForm(DynamicForm):
    """
    Open Data Parameter Form extending Dynamic Form
    """

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'data-parameter'
        kwargs['fields_properties'] = FIELDS_PROPERTIES

        # We need to job to extract job information but job itself is not going to be used for saving form
        self.job = kwargs.pop('job', None)

        super(DataParameterRealForm, self).__init__(*args, **kwargs)

    def save(self):
        # find the data source first
        data_source = DataSource.objects.get(job=self.job)

        # Create or update the data parameters
        for name, value in self.cleaned_data.items():
            DataParameter.objects.update_or_create(
                data_source=data_source,
                name=name,
                defaults={
                    'value': value,
                }
            )

    def update_from_database(self, job):
        """
        Populates the form field with the values stored in the database
        :param job: instance of job model for which the data parameters belong to
        :return: Nothing
        """

        if not job:
            return
        else:

            # check whether the data source is real data or not
            # if not nothing to populate
            try:
                data_source = DataSource.objects.get(job=job)
                if data_source.data_source != REAL_DATA:
                    return
            except DataSource.DoesNotExist:
                return

        # iterate over the fields
        for name in FIELDS_PROPERTIES.keys():
            try:
                value = DataParameter.objects.get(data_source=data_source, name=name).value
                # set the field value
                self.fields[name].initial = value

            except DataParameter.DoesNotExist:
                continue
