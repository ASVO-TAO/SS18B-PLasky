# Generated by Django 2.1.5 on 2019-02-18 03:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bilbyweb', '0007_modify_bilbyweb_job_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='b_job_data', to='bilbycommon.JobCommon'),
        ),
        migrations.AlterField(
            model_name='prior',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bilbycommon.JobCommon'),
        ),
        migrations.AlterField(
            model_name='sampler',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bilbycommon.JobCommon'),
        ),
        migrations.AlterField(
            model_name='signal',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bilbycommon.JobCommon'),
        ),
    ]