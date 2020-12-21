# Generated by Django 2.2.13 on 2020-10-13 14:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0034_auto_20200708_1312'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='acompanhamentodocumento',
            options={'ordering': ('id',), 'verbose_name': 'Acompanhamento de Documento', 'verbose_name_plural': 'Acompanhamentos de Documento'},
        ),
        migrations.AlterModelOptions(
            name='anexado',
            options={'ordering': ('id',), 'verbose_name': 'Anexado', 'verbose_name_plural': 'Anexados'},
        ),
        migrations.AlterModelOptions(
            name='documentoacessorioadministrativo',
            options={'ordering': ('id',), 'verbose_name': 'Documento Acessório', 'verbose_name_plural': 'Documentos Acessórios'},
        ),
        migrations.AlterModelOptions(
            name='documentoadministrativo',
            options={'ordering': ('id',), 'verbose_name': 'Documento Administrativo', 'verbose_name_plural': 'Documentos Administrativos'},
        ),
        migrations.AlterModelOptions(
            name='protocolo',
            options={'ordering': ('id',), 'permissions': (('action_anular_protocolo', 'Permissão para Anular Protocolo'),), 'verbose_name': 'Protocolo', 'verbose_name_plural': 'Protocolos'},
        ),
        migrations.AlterModelOptions(
            name='statustramitacaoadministrativo',
            options={'ordering': ('id',), 'verbose_name': 'Status de Tramitação', 'verbose_name_plural': 'Status de Tramitação'},
        ),
        migrations.AlterModelOptions(
            name='tramitacaoadministrativo',
            options={'ordering': ('id',), 'verbose_name': 'Tramitação de Documento Administrativo', 'verbose_name_plural': 'Tramitações de Documento Administrativo'},
        ),
    ]