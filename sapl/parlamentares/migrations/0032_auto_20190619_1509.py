# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-19 18:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0031_auto_20190614_1203'),
        ('sessao', '0043_auto_20190712_1053'),
    ]

    state_operations = [
        migrations.CreateModel(
            name='Bancada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=80, verbose_name='Nome da Bancada')),
                ('data_criacao', models.DateField(null=True, verbose_name='Data Criação')),
                ('data_extincao', models.DateField(blank=True, null=True, verbose_name='Data Extinção')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('legislatura',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Legislatura',
                                   verbose_name='Legislatura')),
                ('partido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                              to='parlamentares.Partido', verbose_name='Partido')),
            ],
            options={
                'db_table': 'parlamentares_bancada',
                'verbose_name': 'Bancada Parlamentar',
                'verbose_name_plural': 'Bancadas Parlamentares',
                'ordering': ('-legislatura__numero',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CargoBancada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_cargo', models.CharField(max_length=80, verbose_name='Cargo de Bancada')),
                ('cargo_unico', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False,
                                                    verbose_name='Cargo Único ?')),
            ],
            options={
                'db_table': 'parlamentares_cargobancada',
                'verbose_name': 'Cargo de Bancada',
                'verbose_name_plural': 'Cargos de Bancada',
            },
            bases=(models.Model,),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
