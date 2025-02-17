# Generated by Django 4.0.5 on 2022-10-31 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_newuklonfleet'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewUklonPaymentsOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_from', models.DateTimeField()),
                ('report_to', models.DateTimeField()),
                ('report_file_name', models.CharField(max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('signal', models.CharField(max_length=8)),
                ('total_rides', models.PositiveIntegerField()),
                ('total_distance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount_cach', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount_cach_less', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tips', models.DecimalField(decimal_places=2, max_digits=10)),
                ('bonuses', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fares', models.DecimalField(decimal_places=2, max_digits=10)),
                ('comission', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount_without_comission', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
