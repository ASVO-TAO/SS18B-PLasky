"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from collections import OrderedDict

from bilbycommon.forms.dynamic.form import DynamicForm
from bilbycommon.forms.dynamic import field
from bilbycommon.utility.display_names import (
    FREQUENCY,
    FREQUENCY_DISPLAY,
    BAND,
    BAND_DISPLAY,
    A0_SEARCH,
    A0_SEARCH_DISPLAY,
    A0_START_SEARCH,
    A0_START_SEARCH_DISPLAY,
    A0_END_SEARCH,
    A0_END_SEARCH_DISPLAY,
    A0_BINS_SEARCH,
    A0_BINS_SEARCH_DISPLAY,
    ORBIT_TP_SEARCH,
    ORBIT_TP_SEARCH_DISPLAY,
    ORBIT_TP_START_SEARCH,
    ORBIT_TP_START_SEARCH_DISPLAY,
    ORBIT_TP_END_SEARCH,
    ORBIT_TP_END_SEARCH_DISPLAY,
    ORBIT_TP_BINS_SEARCH,
    ORBIT_TP_BINS_SEARCH_DISPLAY,
    ORBIT_P_SEARCH,
    ORBIT_P_SEARCH_DISPLAY,
    ALPHA_SEARCH,
    ALPHA_SEARCH_DISPLAY,
    DELTA_SEARCH,
    DELTA_SEARCH_DISPLAY,
)

from ...models import (
    SearchParameter,
)

FIELDS_PROPERTIES = OrderedDict([
    (FREQUENCY, {
        'type': field.RANGE_10_TO_2000_FLOAT,
        'label': FREQUENCY_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (BAND, {
        'type': field.POSITIVE_FLOAT,
        'label': BAND_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (A0_START_SEARCH, {
        'type': field.NON_NEGATIVE_FLOAT,
        'label': A0_START_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (A0_END_SEARCH, {
        'type': field.NON_NEGATIVE_FLOAT,
        'label': A0_END_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': False,
    }),
    (A0_BINS_SEARCH, {
        'type': field.INTEGER,
        'label': A0_BINS_SEARCH_DISPLAY,
        'placeholder': '500',
        'initial': None,
        'required': False,
    }),
    (ORBIT_TP_START_SEARCH, {
        'type': field.NON_NEGATIVE_FLOAT,
        'label': ORBIT_TP_START_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_TP_END_SEARCH, {
        'type': field.NON_NEGATIVE_FLOAT,
        'label': ORBIT_TP_END_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': False,
    }),
    (ORBIT_TP_BINS_SEARCH, {
        'type': field.INTEGER,
        'label': ORBIT_TP_BINS_SEARCH_DISPLAY,
        'placeholder': '500',
        'initial': None,
        'required': False,
    }),
    (ALPHA_SEARCH, {
        'type': field.FROM_ZERO_TO_LESS_THAN_2PI,
        'label': ALPHA_SEARCH_DISPLAY,
        'placeholder': '7.54',
        'initial': None,
        'required': True,
    }),
    (DELTA_SEARCH, {
        'type': field.FROM_MINUS_PI_TO_PI,
        'label': DELTA_SEARCH_DISPLAY,
        'placeholder': '2.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_P_SEARCH, {
        'type': field.NON_NEGATIVE_FLOAT,
        'label': ORBIT_P_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
])


FIELDSETS = OrderedDict([
    (FREQUENCY_DISPLAY, [FREQUENCY, ]),
    (BAND_DISPLAY, [BAND, ]),
    (A0_SEARCH_DISPLAY, [A0_START_SEARCH, A0_END_SEARCH, A0_BINS_SEARCH, ]),
    (ORBIT_TP_SEARCH_DISPLAY, [ORBIT_TP_START_SEARCH, ORBIT_TP_END_SEARCH, ORBIT_TP_BINS_SEARCH, ]),
    (ALPHA_SEARCH_DISPLAY, [ALPHA_SEARCH, ]),
    (DELTA_SEARCH_DISPLAY, [DELTA_SEARCH, ]),
    (ORBIT_P_SEARCH_DISPLAY, [ORBIT_P_SEARCH, ]),
])


class SearchParameterForm(DynamicForm):
    """
    Simulated Data Parameter Form extending Dynamic Form
    """

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'search-parameter'

        kwargs['fields_properties'] = FIELDS_PROPERTIES
        self.fieldsets = FIELDSETS

        # We need to job to extract job information but job itself is not going to be used for saving form
        self.job = kwargs.pop('job', None)

        super(SearchParameterForm, self).__init__(*args, **kwargs)

    def save(self):
        # Create or update the data parameters
        for name, value in self.cleaned_data.items():
            SearchParameter.objects.update_or_create(
                job=self.job,
                name=name,
                defaults={
                    'value': value,
                }
            )

    def update_from_database(self, job):
        """
        Populates the form field with the values stored in the database
        :param job: instance of job model for which the search parameters belong to
        :return: Nothing
        """

        if not job:
            return

        # iterate over the fields
        for name in FIELDS_PROPERTIES.keys():
            try:
                value = SearchParameter.objects.get(job=job, name=name).value
                # set the field value
                self.fields[name].initial = value

            except SearchParameter.DoesNotExist:
                continue
