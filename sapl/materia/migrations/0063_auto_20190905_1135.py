# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-09-05 13:30
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.translation import ugettext_lazy as _
import django.db.models.deletion

def migra_tipos_turnos_tramitacao(apps, schema_editor):
    TipoTurnoTramitacao = apps.get_model('materia', 'TipoTurnoTramitacao')
    Tramitacao = apps.get_model('materia', 'Tramitacao')

    TURNO_CHOICES = {
        'P': _('Primeiro'),
        'S': _('Segundo'),
        'U': _('Único'),
        'L': _('Suplementar'),
        'F': _('Final'),
        'A': _('Votação Única em Regime de Urgência'),
        'B': _('1ª Votação'),
        'C': _('2ª e 3ª Votações'),
        'D': _('Deliberação'),
        'G': _('1ª e 2ª Votações'),
        'E': _('1ª e 2ª Votações em Regime de Urgência'),
    }
    
    for value in TURNO_CHOICES.values():
        TipoTurnoTramitacao.objects.create(nome=value)

    for t in Tramitacao.objects.all():
        turno_antigo = t.turno
        if turno_antigo:
            try:
                t.tipo_turno = TipoTurnoTramitacao.objects.get(nome=TURNO_CHOICES[turno_antigo])
            except Exception:
                continue
            else:
                t.save()


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0062_auto_20190905_1134')
    ]

    operations = [
        migrations.RunPython(migra_tipos_turnos_tramitacao)
    ]
