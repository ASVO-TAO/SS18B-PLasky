# Generated by Django 2.1.5 on 2019-02-14 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bilbycommon', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobcommon',
            name='job_type',
            field=models.CharField(choices=[('bayesian', 'Bayesian'), ('gravitational', 'Gravitational')], default='bayesian', max_length=20),
        ),
    ]
