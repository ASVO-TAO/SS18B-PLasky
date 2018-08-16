# Generated by Django 2.0.7 on 2018-08-16 01:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tupakweb', '0002_auto_20180816_1123'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignalParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('mass_1', 'Mass 1 (M☉)'), ('mass_2', 'Mass 2 (M☉)'), ('luminosity_distance', 'Luminosity distance (Mpc)'), ('iota', 'iota'), ('psi', 'psi'), ('phase', 'phase'), ('merger_time', 'Merger time (GPS time)'), ('ra', 'Right ascension'), ('dec', 'Declination')], max_length=20)),
                ('value', models.FloatField(blank=True, null=True)),
                ('signal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='signal_signal_parameter', to='tupakweb.Signal')),
            ],
        ),
        migrations.RemoveField(
            model_name='signalbbhparameter',
            name='prior',
        ),
        migrations.RemoveField(
            model_name='signalbbhparameter',
            name='signal',
        ),
        migrations.DeleteModel(
            name='SignalBbhParameter',
        ),
    ]
