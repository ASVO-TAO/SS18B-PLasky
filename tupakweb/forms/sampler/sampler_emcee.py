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
        self.id = kwargs.pop('id', None)
        super(SamplerEmceeForm, self).__init__(*args, **kwargs)

    class Meta:
        model = SamplerEmcee
        fields = FIELDS
        widgets = WIDGETS
        labels = LABELS

    def save(self, **kwargs):
        self.full_clean()
        data = self.cleaned_data

        job = Job.objects.get(id=self.id)

        result = SamplerEmcee.objects.create(
            sampler=job.sampler,
            n_steps=data.get('n_steps'),
        )

        self.request.session['sampler_emcee'] = self.as_array(data)


class EditSamplerEmceeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.job_id = kwargs.pop('job_id', None)
        if self.job_id:
            try:
                self.request.session['sampler_emcee'] = SamplerEmcee.objects.get(job_id=self.job_id).as_json()
            except:
                pass
        super(EditSamplerEmceeForm, self).__init__(*args, **kwargs)

    class Meta:
        model = SamplerEmcee
        fields = FIELDS
        widgets = WIDGETS
        labels = LABELS
