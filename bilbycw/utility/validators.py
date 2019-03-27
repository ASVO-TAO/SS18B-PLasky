"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.forms.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from bilbycommon.utility.display_names import (
    O1,
    O1_DISPLAY,
    O2,
    O2_DISPLAY,
)


def validate_start_time_dependent_on_dataset(value, dataset):
    """
    Validates the start_time whether it is within the range specified below:
    dataset = O1	min: 1126623649	max: 1137250595
    dataset = O2	min: 1164562334	max: 1187733592

    :param value: value to validate
    :param dataset: dataset for the real data
    :return: ValidationError object
    """

    try:
        value = int(value)
    except (ValueError, TypeError):
        return None

    if dataset == O1:
        if value < 1126623649 or value > 1137250595:
            return ValidationError(
                _("Allowed range for {dataset} is [1126623649, 1137250595]".format(dataset=O1_DISPLAY))
            )

    if dataset == O2:
        if value < 1164562334 or value > 1187733592:
            return ValidationError(
                _("Allowed range for {dataset} is [1164562334, 1187733592]".format(dataset=O2_DISPLAY))
            )

    return None
