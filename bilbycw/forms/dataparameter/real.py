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
        'type': field.INTEGER,
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
