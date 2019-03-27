"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

import itertools

from django import forms

from bilbycommon.utility.validators import (
    validate_positive_integer,
    validate_positive_float,
    validate_non_negative_float,
    validate_greater_than_10_and_less_than_2000,
    validate_from_0_and_to_1,
    validate_less_than_pi,
    validate_less_than_2pi,
    validate_from_zero_to_less_than_2pi,
    validate_from_minus_pi_to_pi,
    validate_less_than_equal_hundred,
    validate_duration_number_with_units,
)

# field types
DURATION = 'duration'
INTEGER = 'integer'
POSITIVE_INTEGER = 'positive-integer'
TEXT = 'text'
FLOAT = 'float'
MULTIPLE_CHOICES = 'multiple-choices'
POSITIVE_FLOAT = 'positive-float'
NON_NEGATIVE_FLOAT = 'non-negative-float'
RANGE_10_TO_2000_FLOAT = 'range-10-to-2000-float'
ZERO_TO_HUNDRED = 'zero-to-hundred'
FROM_ZERO_TO_ONE = 'from-zero-to-one'
ZERO_TO_PI = 'zero-to-pi'
ZERO_TO_2PI = 'zero-to-2pi'
FROM_ZERO_TO_LESS_THAN_2PI = 'from-zero-to-less-than-2pi'
FROM_MINUS_PI_TO_PI = 'from-minus-pi-to-pi'
TEXT_AREA = 'text-area'
SELECT = 'select'
RADIO = 'radio'
CHECKBOX = 'checkbox'


class CustomCharField(forms.CharField):
    """
    Class representing a custom text field
    """

    description = "A custom text field"

    def __init__(self, placeholder=None, help_text='', **kwargs):
        super(CustomCharField, self).__init__(**kwargs)

        # apply bootstrap theme
        extra_attrs = {
            'class': 'form-control',
            'placeholder': placeholder if placeholder else '',
        }

        self.widget = forms.TextInput()
        self.widget.attrs.update(extra_attrs)
        self.help_text = help_text


def get_text_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom text field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom text field
    """
    return CustomCharField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=validators,
        help_text=help_text,
    )


def get_duration_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom text field to support duration field
    currently duration can be of the following formats:
    1. Number: represents the number of seconds
    2. Number(s/m/h/d): number followed by the unit of time (s=seconds, m=minutes, h=hours, d=days)
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom text field to cater duration
    """

    default_validators = [validate_duration_number_with_units, ]

    return CustomCharField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


class CustomFloatField(forms.FloatField):
    """
    Class representing a custom text field
    """

    description = "A custom float field"

    def __init__(self, placeholder=None, help_text='', **kwargs):
        super(CustomFloatField, self).__init__(**kwargs)

        # apply bootstrap theme
        extra_attrs = {
            'class': 'form-control',
            'placeholder': placeholder if placeholder else '',
        }

        self.widget = forms.TextInput()
        self.widget.attrs.update(extra_attrs)
        self.help_text = help_text


def get_float_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom float field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field
    """
    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=validators,
        help_text=help_text,
    )


def get_positive_float_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts only number that is greater than zero
    """
    default_validators = [validate_positive_float, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_non_negative_float_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom non-negative float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts only number that is greater than or equal to zero
    """
    default_validators = [validate_non_negative_float, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_greater_than_10_and_less_than_2000_float_input(label, required, placeholder=None, initial=None, validators=(),
                                                       help_text=''):
    """
    Method to get a custom float number field in the range (10, 2000)
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts only number that falls in the range (10, 2000)
    """
    default_validators = [validate_greater_than_10_and_less_than_2000, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_zero_to_hundred_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts only number that is greater than zero and less than 100
    """
    default_validators = [validate_positive_float, validate_less_than_equal_hundred, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_from_zero_to_one_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts number in the range [0, 1]
    """
    default_validators = [validate_from_0_and_to_1, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_zero_to_pi_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts only number that is greater than zero and less than pi(Math.pi)
    """
    default_validators = [validate_positive_float, validate_less_than_pi, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_zero_to_2pi_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts numbers greater than zero and less or equal to 2pi(Math.pi)
    """
    default_validators = [validate_positive_float, validate_less_than_2pi, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_from_zero_to_less_than_2pi_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive float number field which is less than 2pi
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts numbers in the range [0, 2pi)
    """
    default_validators = [validate_from_zero_to_less_than_2pi, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_from_minus_pi_to_pi_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom float number field whose value is in the range [-pi, +pi]
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom floating number field that accepts numbers in the range [-pi, +pi)
    """
    default_validators = [validate_from_minus_pi_to_pi, ]

    return CustomFloatField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


class CustomTextAreaField(forms.CharField):
    """
    Class representing a custom text-area field
    """

    description = "A custom text-area field"

    def __init__(self, placeholder=None, help_text='', **kwargs):
        super(CustomTextAreaField, self).__init__(**kwargs)

        # apply bootstrap theme
        extra_attrs = {
            'class': 'form-control',
            'placeholder': placeholder if placeholder else '',
        }

        self.widget = forms.Textarea()
        self.widget.attrs.update(extra_attrs)
        self.help_text = help_text


def get_text_area_input(label, required, placeholder=None, initial=None, help_text=''):
    """
    Method to get a custom text-area field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param help_text: tooltip for the input
    :return: A custom text-area field
    """
    return CustomTextAreaField(
        label=label,
        placeholder=placeholder,
        required=required,
        initial=initial,
        help_text=help_text,
    )


class CustomIntegerField(forms.IntegerField):
    """
    Class representing a custom Integer field
    """

    description = "A custom integer field"

    def __init__(self, placeholder=None, help_text='', **kwargs):
        super(CustomIntegerField, self).__init__(**kwargs)

        # apply bootstrap theme
        extra_attrs = {
            'class': 'form-control',
            'placeholder': placeholder if placeholder else '',
        }

        self.widget = forms.TextInput()
        self.widget.attrs.update(extra_attrs)
        self.help_text = help_text


def get_integer_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive integer field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom positive integer field accepts inputs greater than zero
    """
    return CustomIntegerField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=validators,
        help_text=help_text,
    )


def get_positive_integer_input(label, required, placeholder=None, initial=None, validators=(), help_text=''):
    """
    Method to get a custom positive integer field
    :param label: String label of the field
    :param required: Boolean to define whether the field is required or not
    :param placeholder: Placeholder to appear in the field
    :param initial: Default input value for the field
    :param validators: validators that should be attached with the field
    :param help_text: tooltip for the input
    :return: A custom positive integer field accepts inputs greater than zero
    """
    default_validators = [validate_positive_integer, ]

    return CustomIntegerField(
        label=label,
        required=required,
        initial=initial,
        placeholder=placeholder,
        validators=list(itertools.chain(default_validators, validators)),
        help_text=help_text,
    )


def get_select_input(label, choices=None, initial=None, extra_class=None, help_text=''):
    """
    Method to get a choice field with bootstrap theme
    :param label: String label of the field
    :param choices: List of choices to be rendered with the field
    :param initial: Default input value for the field
    :param extra_class: extra css class for styling
    :param help_text: tooltip for the input
    :return: A custom select field
    """

    return forms.ChoiceField(
        label=label,
        widget=forms.Select(
            attrs={
                'class': 'form-control' + (' ' + extra_class if extra_class else ''),
            }
        ),
        choices=choices,
        initial=initial,
        help_text=help_text,
    )


def get_checkbox_input(label, required=False, initial=None, extra_class=None, help_text=''):
    """
    Method to get a checkbox
    :param label: String label of the field
    :param required: Boolean to define whether the input is required or not
    :param initial: Default input value for the field (checked or not)
    :param extra_class: extra css class for styling
    :param help_text: tooltip for the input
    :return: A custom select field
    """
    return forms.BooleanField(
        label=label,
        widget=forms.CheckboxInput(
            attrs={
                'class': extra_class if extra_class else '',
            }
        ),
        required=required,
        initial=initial,
        help_text=help_text,
    )


def get_multiple_choices_input(label, required, choices=None, initial=None, help_text=''):
    """
    Method to get a multiple checkbox field
    :param label: String label of the field
    :param required: Boolean to define whether the input is required or not
    :param initial: Default input value for the field (checked or not)
    :param choices: List of choices to be rendered with the field
    :param help_text: tooltip for the input
    :return: A multiple checkbox field
    """
    return forms.MultipleChoiceField(
        label=label,
        widget=forms.CheckboxSelectMultiple(),
        choices=choices,
        initial=initial,
        required=required,
        help_text=help_text,
    )
