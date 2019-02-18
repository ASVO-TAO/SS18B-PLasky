# Generated by Django 2.1.5 on 2019-02-15 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bilbycommon', '0002_jobcommon_job_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='BilbyGJob',
            fields=[
                ('jobcommon_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='bilbycommon.JobCommon')),
            ],
            bases=('bilbycommon.jobcommon',),
        ),
    ]
