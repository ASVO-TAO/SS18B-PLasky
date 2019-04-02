"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from collections import OrderedDict

from django import forms

from bilbycommon.forms.dynamic.form import DynamicForm
from bilbycommon.forms.dynamic import field
from bilbycommon.utility.display_names import (
    FREQUENCY,
    FREQUENCY_DISPLAY,
    BAND,
    BAND_DISPLAY,
    A0_SEARCH_DISPLAY,
    A0_START_SEARCH,
    A0_START_SEARCH_DISPLAY,
    A0_END_SEARCH,
    A0_END_SEARCH_DISPLAY,
    A0_BINS_SEARCH,
    A0_BINS_SEARCH_DISPLAY,
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
        'help_text': 'For fixed value use this and leave others empty.',
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
        'help_text': 'For fixed value use this and leave others empty.',
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

    def clean(self):
        """
        Checks the validation of the form. Usually checks the dependent fields like:
        Start, End and Number of Bins.
        :return:
        """

        if not self.fieldsets:
            return

        data = self.cleaned_data

        # validating a0 fields
        a0_start = data.get(A0_START_SEARCH, None)
        a0_end = data.get(A0_END_SEARCH, None)
        a0_bins = data.get(A0_BINS_SEARCH, None)

        if not a0_end and not a0_bins:
            # no problems if both of them are empty. However, None will passed as cleaned data if there are errors
            # in the field. In that case, to show up error in other field
            add_required_to = []
            if A0_END_SEARCH in self.errors.keys() and A0_BINS_SEARCH not in self.errors.keys():
                add_required_to.append(A0_BINS_SEARCH)

            if A0_BINS_SEARCH in self.errors.keys() and A0_END_SEARCH not in self.errors.keys():
                add_required_to.append(A0_END_SEARCH)

            for error_field in add_required_to:
                self.add_error(error_field, forms.ValidationError('Required for range'))

        elif not a0_end or not a0_bins:  # problem with the inputs, one of End or #Bins fields is left blank

            # checking whether there are already errors for those fields, in such cases, we should not add more
            # errors. For example: if the number of bins is not integer, that error is sufficient to stop the
            # form to save the updated values in the database, we will not be showing up further errors until
            # that is fixed. Similar applies for the End field
            if not a0_end and A0_END_SEARCH not in self.errors.keys():
                self.add_error(A0_END_SEARCH, forms.ValidationError('Required for range'))
            if not a0_bins and A0_BINS_SEARCH not in self.errors.keys():
                self.add_error(A0_BINS_SEARCH, forms.ValidationError('Required for range'))

        elif a0_end <= a0_start:
            self.add_error(A0_START_SEARCH, forms.ValidationError('Must be < End'))
            self.add_error(A0_END_SEARCH, forms.ValidationError('Must be > Start'))

        # validating orbitTp fields
        orbit_tp_start = data.get(ORBIT_TP_START_SEARCH, None)
        orbit_tp_end = data.get(ORBIT_TP_END_SEARCH, None)
        orbit_tp_bins = data.get(ORBIT_TP_BINS_SEARCH, None)

        if not orbit_tp_end and not orbit_tp_bins:
            # no problems if both of them are empty. However, None will passed as cleaned data if there are errors
            # in the field. In that case, to show up error in other field
            add_required_to = []
            if ORBIT_TP_BINS_SEARCH in self.errors.keys() and ORBIT_TP_END_SEARCH not in self.errors.keys():
                add_required_to.append(ORBIT_TP_END_SEARCH)

            if ORBIT_TP_END_SEARCH in self.errors.keys() and ORBIT_TP_BINS_SEARCH not in self.errors.keys():
                add_required_to.append(ORBIT_TP_BINS_SEARCH)

            for error_field in add_required_to:
                self.add_error(error_field, forms.ValidationError('Required for range'))

        elif not orbit_tp_end or not orbit_tp_bins:  # problem with the inputs, one of End or #Bins fields is left blank

            # checking whether there are already errors for those fields, in such cases, we should not add more
            # errors. For example: if the number of bins is not integer, that error is sufficient to stop the
            # form to save the updated values in the database, we will not be showing up further errors until
            # that is fixed. Similar applies for the End field
            if not orbit_tp_end and ORBIT_TP_END_SEARCH not in self.errors.keys():
                self.add_error(ORBIT_TP_END_SEARCH, forms.ValidationError('Required for range'))

            if not orbit_tp_bins and ORBIT_TP_BINS_SEARCH not in self.errors.keys():
                self.add_error(ORBIT_TP_BINS_SEARCH, forms.ValidationError('Required for range'))

        elif orbit_tp_end <= orbit_tp_start:
            self.add_error(ORBIT_TP_START_SEARCH, forms.ValidationError('Must be < End'))
            self.add_error(ORBIT_TP_END_SEARCH, forms.ValidationError('Must be > Start'))
