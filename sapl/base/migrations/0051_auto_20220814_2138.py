# Generated by Django 2.2.28 on 2022-08-15 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0050_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfig',
            name='identificacao_de_documentos',
            field=models.CharField(default='{sigla} Nº {numero}/{ano}{-}{complemento} - {nome}', help_text='\n        Como mostrar a identificação dos documentos administrativos?\n        Você pode usar um conjunto de combinações que pretender.\n        Ao fazer sua edição, será mostrado logo abaixo o último documento cadastrado, como exemplo de resultado de sua edição.\n        Em caso de erro, nenhum documento será mostrado e aparecerá apenas o formato padrão mínimo, que é este: "{sigla} Nº {numero}/{ano}{-}{complemento} - {nome}".\n        Muito importante, use as chaves "{}", sem elas, você estará inserindo um texto qualquer e não o valor de um campo.\n        Você pode combinar as seguintes campos: {sigla} {nome} {numero} {ano} {complemento} {assunto}\n        Ainda pode ser usado {/}, {-}, {.} se você quiser que uma barra, traço, ou ponto\n        seja adicionado apenas se o próximo campo que será usado tenha algum conteúdo\n        (não use dois destes destes condicionais em sequência, somente o último será considerado).\n        ', max_length=254, verbose_name='Formato da identificação dos documentos'),
        ),
        migrations.AlterField(
            model_name='appconfig',
            name='protocolo_manual',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Permitir informe manual de data e hora de protocolo?'),
        ),
    ]
