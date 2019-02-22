"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from bilbycommon.utility.constants import set_dict_indices


from ..models import (
    BilbyCWJob,
    DataSource,
)

from ..forms.start import StartJobForm
from ..forms.submit import SubmitJobForm
from ..forms.datasource.datasource import DataSourceForm


# BilbyCWJob Creation/Edit/Summary related
START = 'start'
DATA_SOURCE = 'data-source'
LAUNCH = 'launch'


# Number of TABs to show up in the UI. We currently have 6 TABs
TABS = [
    START,
    DATA_SOURCE,
    LAUNCH,
]
TABS_INDEXES = set_dict_indices(TABS)


# Tab Forms, defines the forms of a Tab. Based on this, forms are saved when Next or Previous buttons are pressed.
TAB_FORMS = {
    START: [START, DATA_SOURCE],
    LAUNCH: [LAUNCH, ]
}


# Form Dictionary, Maps the form key to the actual form class
FORMS_NEW = {
    START: StartJobForm,
    DATA_SOURCE: DataSourceForm,
    LAUNCH: SubmitJobForm,
}


# Maps models to form keys for models that use Django Model Forms.
MODELS = {
    START: BilbyCWJob,
    DATA_SOURCE: DataSource,
}
