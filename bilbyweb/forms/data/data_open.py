"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

import ast
from collections import OrderedDict

from ...utility.display_names import OPEN_DATA
from ..dynamic import field
from ...models import DataParameter, Data
from ..dynamic.form import DynamicForm
from ...utility.display_names import (
    DETECTOR_CHOICE,
    DETECTOR_CHOICE_DISPLAY,
    SIGNAL_DURATION,
    SIGNAL_DURATION_DISPLAY,
    SAMPLING_FREQUENCY,
    SAMPLING_FREQUENCY_DISPLAY,
    START_TIME,
    START_TIME_DISPLAY,
    HANFORD,
    HANFORD_DISPLAY,
    LIVINGSTON,
    LIVINGSTON_DISPLAY,
    VIRGO,
    VIRGO_DISPLAY,
)

DETECTOR_CHOICES = [
    (HANFORD, HANFORD_DISPLAY),
    (LIVINGSTON, LIVINGSTON_DISPLAY),
    (VIRGO, VIRGO_DISPLAY),
]

DATA_FIELDS_PROPERTIES = OrderedDict([
    (DETECTOR_CHOICE, {
        'type': field.MULTIPLE_CHOICES,
        'label': DETECTOR_CHOICE_DISPLAY,
        'initial': None,
        'required': True,
        'choices': DETECTOR_CHOICES,
    }),
    (SIGNAL_DURATION, {
        'type': field.POSITIVE_INTEGER,
        'label': SIGNAL_DURATION_DISPLAY,
        'placeholder': '2',
        'initial': None,
        'required': True,
    }),
    (SAMPLING_FREQUENCY, {
        'type': field.POSITIVE_INTEGER,
        'label': SAMPLING_FREQUENCY_DISPLAY,
        'placeholder': '2',
        'initial': None,
        'required': True,
    }),
    (START_TIME, {
        'type': field.POSITIVE_FLOAT,
        'label': START_TIME_DISPLAY,
        'placeholder': '2.1',
        'initial': None,
        'required': True,
    }),
])


class OpenDataParameterForm(DynamicForm):
    """
    Open Data Parameter Form extending Dynamic Form
    """

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'data-parameter'
        kwargs['fields_properties'] = DATA_FIELDS_PROPERTIES

        # We need to job to extract job information but job itself is not going to be used for saving form
        self.job = kwargs.pop('job', None)

        super(OpenDataParameterForm, self).__init__(*args, **kwargs)

    def save(self):
        # find the data first
        data = Data.objects.get(job=self.job)

        # Create or update the data parameters
        for name, value in self.cleaned_data.items():
            DataParameter.objects.update_or_create(
                data=data,
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

            # check whether the data choice is open data or not
            # if not nothing to populate
            try:
                data = Data.objects.get(job=job)
                if data.data_choice != OPEN_DATA:
                    return
            except Data.DoesNotExist:
                return

        # iterate over the fields
        for name in DATA_FIELDS_PROPERTIES.keys():
            try:
                value = DataParameter.objects.get(data=data, name=name).value

                # set the field value
                # extra processing required for checkbox type fields
                self.fields[name].initial = ast.literal_eval(value) if name == DETECTOR_CHOICE else value

            except DataParameter.DoesNotExist:
                continue
