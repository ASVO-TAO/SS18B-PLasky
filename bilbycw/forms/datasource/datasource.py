"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from bilbycommon.utility.display_names import DATA_SOURCE, DATA_SOURCE_DISPLAY
from ...models import DataSource

FIELDS = [DATA_SOURCE, ]

WIDGETS = {
    DATA_SOURCE: forms.Select(
        attrs={'class': 'form-control'},
    ),
}

LABELS = {
    DATA_SOURCE: _(DATA_SOURCE_DISPLAY),
}


class DataSourceForm(forms.ModelForm):
    """
    Data form class
    """
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.job = kwargs.pop('job', None)
        super(DataSourceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = DataSource
        fields = FIELDS
        widgets = WIDGETS
        labels = LABELS

    def save(self, **kwargs):
        """
        Overrides the default save method
        :param kwargs: Dictionary of keyword arguments
        :return: Nothing
        """
        self.full_clean()
        data = self.cleaned_data

        # deleting data object will make sure that there exists no parameter
        # this avoids duplicating parameters
        DataSource.objects.filter(job=self.job).delete()

        DataSource.objects.update_or_create(
            job=self.job,
            defaults={
                DATA_SOURCE: data.get(DATA_SOURCE),
            }
        )
