# Generated by Django 2.0.7 on 2018-10-05 05:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('django_hpc_job_controller', '0006_auto_20181005_1232'),
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_choice', models.CharField(choices=[('simulated', 'Simulated'), ('open', 'Open')], default='simulated', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='DataParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('value', models.CharField(blank=True, max_length=100, null=True)),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bilbyweb.Data')),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('hpcjob_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='django_hpc_job_controller.HpcJob')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('queued', 'Queued'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('error', 'Error'), ('saved', 'Saved'), ('wall_time_exceeded', 'Wall Time Exceeded'), ('deleted', 'Deleted'), ('public', 'Public')], default='draft', max_length=20)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True)),
                ('submission_time', models.DateTimeField(blank=True, null=True)),
                ('json_representation', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_job', to=settings.AUTH_USER_MODEL)),
            ],
            bases=('django_hpc_job_controller.hpcjob',),
        ),
        migrations.CreateModel(
            name='Prior',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('prior_choice', models.CharField(blank=True, choices=[('fixed', 'Fixed'), ('uniform', 'Uniform')], default='fixed', max_length=20)),
                ('fixed_value', models.FloatField(blank=True, null=True)),
                ('uniform_min_value', models.FloatField(blank=True, null=True)),
                ('uniform_max_value', models.FloatField(blank=True, null=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_prior', to='bilbyweb.Job')),
            ],
        ),
        migrations.CreateModel(
            name='Sampler',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sampler_choice', models.CharField(choices=[('dynesty', 'Dynesty'), ('nestle', 'Nestle'), ('emcee', 'Emcee')], default='dynesty', max_length=15)),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='job_sampler', to='bilbyweb.Job')),
            ],
        ),
        migrations.CreateModel(
            name='SamplerParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(blank=True, max_length=100, null=True)),
                ('sampler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bilbyweb.Sampler')),
            ],
        ),
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signal_choice', models.CharField(choices=[('skip', 'None'), ('binary_black_hole', 'Binary Black Hole')], default='skip', max_length=50)),
                ('signal_model', models.CharField(choices=[('binary_black_hole', 'Binary Black Hole')], max_length=50)),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='job_signal', to='bilbyweb.Job')),
            ],
        ),
        migrations.CreateModel(
            name='SignalParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('mass_1', 'Mass 1 (M☉)'), ('mass_2', 'Mass 2 (M☉)'), ('luminosity_distance', 'Luminosity Distance (Mpc)'), ('iota', 'iota'), ('psi', 'psi'), ('phase', 'Phase'), ('geocent_time', 'Merger Time (GPS Time)'), ('ra', 'Right Ascension (Radians)'), ('dec', 'Declination (Degrees)')], max_length=20)),
                ('value', models.FloatField(blank=True, null=True)),
                ('signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signal_signal_parameter', to='bilbyweb.Signal')),
            ],
        ),
        migrations.AddField(
            model_name='data',
            name='job',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='job_data', to='bilbyweb.Job'),
        ),
        migrations.AlterUniqueTogether(
            name='prior',
            unique_together={('job', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='job',
            unique_together={('user', 'name')},
        ),
    ]
