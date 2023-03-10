from django.conf.urls import url, include

from .apps import AppConfig
from .views import (cronometro_painel, get_dados_painel, painel_mensagem_view,
                    painel_parlamentar_view, painel_view, painel_votacao_view,
                    switch_painel, verifica_painel, votante_view, CronometroPainelCrud,
                    PainelConfigCrud, ordena_cronometro, painel_parcial_view, painel_discurso_view,
                    get_dados_painel_discurso)

app_name = AppConfig.name

urlpatterns = [
    url(r'^painel-principal/(?P<pk>\d+)$', painel_view,
        name="painel_principal"),
    url(r'^painel/(?P<pk>\d+)/dados$', get_dados_painel, name='dados_painel'),
    
    url(r'^painel/mensagem$', painel_mensagem_view, name="painel_mensagem"),
    url(r'^painel/parlamentar$', painel_parlamentar_view,
        name='painel_parlamentar'),
    url(r'^painel/switch-painel$', switch_painel,
        name="switch_painel"),
    url(r'^painel/votacao$', painel_votacao_view, name='painel_votacao'),
    url(r'^painel/verifica-painel$', verifica_painel,
        name="verifica_painel"),
    url(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    
    url(r'^sistema/cronometro/', include(CronometroPainelCrud.get_urls())),
    url(r'^sistema/ordena_cronometro/', ordena_cronometro, name='ordena_cronometro'),
    url(r'^sistema/painel-config/', include(PainelConfigCrud.get_urls())),

    url(r'^voto-individual/$', votante_view,
        name='voto_individual'),

    url(r'^painel-parcial/(?P<pk>\d+)/(?P<opcoes>\d+)/$', painel_parcial_view,
        name="painel_parcial"),

    url(r'^painel-discurso/(?P<sessao_pk>\d+)/(?P<lista_pk>\d+)/$', painel_discurso_view,
        name="painel_discurso"),
    url(r'^painel/(?P<pk>\d+)/(?P<lista_pk>\d+)/dados-discurso$', get_dados_painel_discurso, 
        name='dados_painel_discurso'),
]
