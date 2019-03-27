"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django import forms

from .field import (
    get_text_input,
    get_text_area_input,
    get_select_input,
    get_checkbox_input,
    get_integer_input,
    get_positive_integer_input,
    get_multiple_choices_input,
    get_positive_float_input,
    get_non_negative_float_input,
    get_greater_than_10_and_less_than_2000_float_input,
    get_zero_to_hundred_input,
    get_from_zero_to_one_input,
    get_zero_to_pi_input,
    get_zero_to_2pi_input,
    get_from_zero_to_less_than_2pi_input,
    get_from_minus_pi_to_pi_input,
    get_float_input,
    get_duration_input,
    DURATION,
    INTEGER,
    POSITIVE_INTEGER,
    FLOAT,
    POSITIVE_FLOAT,
    NON_NEGATIVE_FLOAT,
    RANGE_10_TO_2000_FLOAT,
    MULTIPLE_CHOICES,
    ZERO_TO_HUNDRED,
    FROM_ZERO_TO_ONE,
    ZERO_TO_PI,
    ZERO_TO_2PI,
    FROM_ZERO_TO_LESS_THAN_2PI,
    FROM_MINUS_PI_TO_PI,
    TEXT,
    TEXT_AREA,
    SELECT,
    CHECKBOX,
)


class DynamicForm(forms.Form):
    """
    Class that defines a form by generating fields based on a dictionary input of fields.
    It serves a base class for forms that do not know the number of fields and their types beforehand.
    """
    def __init__(self, *args, **kwargs):
        # name of the form
        self.name = kwargs.pop('name', None)
        # dictionary of fields, each containing field_name as key, field_type, placeholder, choices etc. as values
        self.fields_properties = kwargs.pop('fields_properties')

        # request might be needed
        self.request = kwargs.pop('request', None)

        # initializes the form
        super(DynamicForm, self).__init__(*args, **kwargs)

        # generating form fields based on their types
        for name, properties in self.fields_properties.items():

            if properties.get('type') == TEXT:
                self.fields[name] = get_text_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == TEXT_AREA:
                self.fields[name] = get_text_area_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == POSITIVE_FLOAT:
                self.fields[name] = get_positive_float_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == NON_NEGATIVE_FLOAT:
                self.fields[name] = get_non_negative_float_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == RANGE_10_TO_2000_FLOAT:
                self.fields[name] = get_greater_than_10_and_less_than_2000_float_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == ZERO_TO_HUNDRED:
                self.fields[name] = get_zero_to_hundred_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == FROM_ZERO_TO_ONE:
                self.fields[name] = get_from_zero_to_one_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == ZERO_TO_PI:
                self.fields[name] = get_zero_to_pi_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == ZERO_TO_2PI:
                self.fields[name] = get_zero_to_2pi_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == FROM_ZERO_TO_LESS_THAN_2PI:
                self.fields[name] = get_from_zero_to_less_than_2pi_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == FROM_MINUS_PI_TO_PI:
                self.fields[name] = get_from_minus_pi_to_pi_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == INTEGER:
                self.fields[name] = get_integer_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == POSITIVE_INTEGER:
                self.fields[name] = get_positive_integer_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == FLOAT:
                self.fields[name] = get_float_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == DURATION:
                self.fields[name] = get_duration_input(
                    label=properties.get('label', name),
                    placeholder=properties.get('placeholder', None),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    validators=properties.get('validators', ()),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == SELECT:
                self.fields[name] = get_select_input(
                    label=properties.get('label', name),
                    initial=properties.get('initial', None),
                    choices=properties.get('choices'),
                    extra_class=properties.get('extra_class', None),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == CHECKBOX:
                self.fields[name] = get_checkbox_input(
                    label=properties.get('label', name),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    help_text=properties.get('help_text', ''),
                )

            elif properties.get('type') == MULTIPLE_CHOICES:
                self.fields[name] = get_multiple_choices_input(
                    label=properties.get('label', name),
                    initial=properties.get('initial', None),
                    required=properties.get('required', False),
                    choices=properties.get('choices'),
                    help_text=properties.get('help_text', ''),
                )
