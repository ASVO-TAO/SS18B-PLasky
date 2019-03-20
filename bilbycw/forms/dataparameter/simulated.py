"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

import ast
import random

from collections import OrderedDict

from bilbycommon.forms.dynamic.form import DynamicForm
from bilbycommon.forms.dynamic import field
from bilbycommon.utility.display_names import (
    H0,
    H0_DISPLAY,
    A0,
    A0_DISPLAY,
    ORBIT_TP,
    ORBIT_TP_DISPLAY,
    ORBIT_P,
    ORBIT_P_DISPLAY,
    SIGNAL_FREQUENCY,
    SIGNAL_FREQUENCY_DISPLAY,
    PSI,
    PSI_DISPLAY,
    COSI,
    COSI_DISPLAY,
    ALPHA,
    ALPHA_DISPLAY,
    DELTA,
    DELTA_DISPLAY,
    RAND_SEED,
    RAND_SEED_DISPLAY,
    IFO,
    IFO_DISPLAY,
    NOISE_LEVEL,
    NOISE_LEVEL_DISPLAY,
    START_TIME_CW,
    START_TIME_CW_DISPLAY,
    DURATION,
    DURATION_DISPLAY,
    HANFORD,
    HANFORD_DISPLAY,
    LIVINGSTON,
    LIVINGSTON_DISPLAY,
    FAKE_DATA,
)

from ...models import (
    DataSource,
    DataParameter,
)

IFO_CHOICES = [
    (HANFORD, HANFORD_DISPLAY),
    (LIVINGSTON, LIVINGSTON_DISPLAY),
]

FIELDS_PROPERTIES = OrderedDict([
    (H0, {
        'type': field.FLOAT,
        'label': H0_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (A0, {
        'type': field.FLOAT,
        'label': A0_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_TP, {
        'type': field.FLOAT,
        'label': ORBIT_TP_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (SIGNAL_FREQUENCY, {
        'type': field.FLOAT,
        'label': SIGNAL_FREQUENCY_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (PSI, {
        'type': field.FLOAT,
        'label': PSI_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (COSI, {
        'type': field.FLOAT,
        'label': COSI_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ALPHA, {
        'type': field.FLOAT,
        'label': ALPHA_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (DELTA, {
        'type': field.FLOAT,
        'label': DELTA_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_P, {
        'type': field.FLOAT,
        'label': ORBIT_P_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (RAND_SEED, {
        'type': field.INTEGER,
        'label': RAND_SEED_DISPLAY,
        'placeholder': '897359',
        'initial': None,
        'required': True,
    }),
    (IFO, {
        'type': field.MULTIPLE_CHOICES,
        'label': IFO_DISPLAY,
        'choices': IFO_CHOICES,
        'initial': None,
        'required': True,
    }),
    (NOISE_LEVEL, {
        'type': field.FLOAT,
        'label': NOISE_LEVEL_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
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


class DataParameterSimulatedForm(DynamicForm):
    """
    Simulated Data Parameter Form extending Dynamic Form
    """

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'data-parameter'

        # update the randseed value
        FIELDS_PROPERTIES[RAND_SEED].update({
            'initial': random.randint(-2147483648, 2147483647),
        })

        kwargs['fields_properties'] = FIELDS_PROPERTIES

        # We need to job to extract job information but job itself is not going to be used for saving form
        self.job = kwargs.pop('job', None)

        super(DataParameterSimulatedForm, self).__init__(*args, **kwargs)

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
                if data_source.data_source != FAKE_DATA:
                    return
            except DataSource.DoesNotExist:
                return

        # iterate over the fields
        for name in FIELDS_PROPERTIES.keys():
            try:
                value = DataParameter.objects.get(data_source=data_source, name=name).value
                # set the field value
                # extra processing required for checkbox type fields
                self.fields[name].initial = ast.literal_eval(value) if name == IFO else value

            except DataParameter.DoesNotExist:
                continue
