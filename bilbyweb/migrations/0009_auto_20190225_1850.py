# Generated by Django 2.1.5 on 2019-02-25 07:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bilbyweb', '0008_auto_20190218_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pe_job_data', to='bilbycommon.JobCommon'),
        ),
    ]