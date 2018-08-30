from django import forms
from django.utils.translation import ugettext_lazy as _
from ...models import Job, SamplerEmcee

FIELDS = [
    'n_steps',
]

WIDGETS = {
    'n_steps': forms.TextInput(
        attrs={'class': 'form-control'},
    ),
}

LABELS = {
    'n_steps': _('Number of live points'),
}


class SamplerEmceeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.job = kwargs.pop('job', None)
        super(SamplerEmceeForm, self).__init__(*args, **kwargs)

    class Meta:
        model = SamplerEmcee
        fields = FIELDS
        widgets = WIDGETS
        labels = LABELS

    def save(self, **kwargs):
        self.full_clean()
        data = self.cleaned_data

        result = SamplerEmcee.objects.create(
            sampler=self.job.sampler,
            n_steps=data.get('n_steps'),
        )
