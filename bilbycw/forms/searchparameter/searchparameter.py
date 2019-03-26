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
    ORBIT_TP_SEARCH,
    ORBIT_TP_SEARCH_DISPLAY,
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
        'type': field.FLOAT,
        'label': FREQUENCY_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (BAND, {
        'type': field.FLOAT,
        'label': BAND_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (A0_SEARCH, {
        'type': field.FLOAT,
        'label': A0_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_TP_SEARCH, {
        'type': field.FLOAT,
        'label': ORBIT_TP_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ALPHA_SEARCH, {
        'type': field.FLOAT,
        'label': ALPHA_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (DELTA_SEARCH, {
        'type': field.FLOAT,
        'label': DELTA_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
    (ORBIT_P_SEARCH, {
        'type': field.FLOAT,
        'label': ORBIT_P_SEARCH_DISPLAY,
        'placeholder': '10.54',
        'initial': None,
        'required': True,
    }),
])


class SearchParameterForm(DynamicForm):
    """
    Simulated Data Parameter Form extending Dynamic Form
    """

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'search-parameter'

        kwargs['fields_properties'] = FIELDS_PROPERTIES

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
