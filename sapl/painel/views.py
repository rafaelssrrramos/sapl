import html
import json
import logging
import os

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.base.models import CasaLegislativa
from sapl.crud.base import Crud, CrudAux
from sapl.painel.apps import AppConfig
from sapl.parlamentares.models import Legislatura, Parlamentar, Votante
from sapl.sessao.models import (ExpedienteMateria, OradorExpediente, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar, CronometroLista, ListaDiscurso,
                                ParlamentarLista, RegistroLeitura)
from sapl.utils import filiacao_data, get_client_ip, sort_lista_chave

from .forms import CronometroForm, ConfiguracoesPainelForm
from .models import Cronometro, PainelConfig

VOTACAO_NOMINAL = 2

class CronometroPainelCrud(CrudAux):
    model = Cronometro

    class ListView(CrudAux.ListView):
        template_name = "painel/cronometro_list.html"
        
    class BaseMixin(CrudAux.BaseMixin):
        form_class = CronometroForm

def ordena_cronometro(request):
    ordem = request.POST.getlist("ordem", [])
    for index, o in enumerate(ordem, 1):
        c = Cronometro.objects.get(id=o)
        c.ordenacao = index
        c.save()
    return JsonResponse({'type':'success','msg':'Ordem alterada com sucesso.'})

class PainelConfigCrud(CrudAux):
    model = PainelConfig

    class BaseMixin(CrudAux.BaseMixin):
        form_class = ConfiguracoesPainelForm
        list_url = ''
        create_url = ''

    class CreateView(CrudAux.CreateView):

        def get(self, request, *args, **kwargs):
            painel_config = PainelConfig.objects.first()

            if not painel_config:
                painel_config = PainelConfig()
                painel_config.save()

            return HttpResponseRedirect(
                reverse('sapl.painel:painelconfig_update',
                        kwargs={'pk': painel_config.pk}))

        def post(self, request, *args, **kwargs):
            return self.get(request, *args, **kwargs)

    class ListView(CrudAux.ListView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))

    class DetailView(CrudAux.DetailView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))

    class DeleteView(CrudAux.DeleteView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))


# FIXME mudar l??gica


def check_permission(user):
    return user.has_module_perms(AppConfig.label)


def votacao_aberta(request):
    '''
    Fun????o que verifica se h?? somente 1 uma mat??ria aberta ou
    nenhuma. ?? utilizada como uma fun????o auxiliar para a view
    votante_view.
    '''
    logger = logging.getLogger(__name__)
    username = request.user.username

    votacoes_abertas = SessaoPlenaria.objects.filter(
        Q(ordemdia__votacao_aberta=True) |
        Q(expedientemateria__votacao_aberta=True)).distinct()

    if len(votacoes_abertas) > 1:
        msg_abertas = []
        for v in votacoes_abertas:
            msg_abertas.append('''<li><a href="%s">%s</a></li>''' % (
                reverse('sapl.sessao:sessaoplenaria_detail',
                        kwargs={'pk': v.id}),
                v.__str__()))
        logger.info('user=' + username + '. Existe mais de uma vota????es aberta. Elas se encontram '
                    'nas seguintes Sess??es: ' + ', '.join(msg_abertas) + '. '
                    'Para votar, pe??a para que o Operador feche-as.')
        msg = _('Existe mais de uma vota????es aberta. Elas se encontram '
                'nas seguintes Sess??es: ' + ', '.join(msg_abertas) + '. '
                'Para votar, pe??a para que o Operador feche-as.')
        messages.add_message(request, messages.INFO, msg)
        return None, msg

    elif len(votacoes_abertas) == 1:
        ordens = OrdemDia.objects.filter(
            sessao_plenaria=votacoes_abertas.first(),
            votacao_aberta=True)
        expedientes = ExpedienteMateria.objects.filter(
            sessao_plenaria=votacoes_abertas.first(),
            votacao_aberta=True)

        numero_materias_abertas = len(ordens) + len(expedientes)
        if numero_materias_abertas > 1:
            logger.info('user=' + username + '. Existe mais de uma vota????o aberta na Sess??o: ' +
                        ('''<li><a href="%s">%s</a></li>''' % (
                        reverse('sapl.sessao:sessaoplenaria_detail',
                                kwargs={'pk': votacoes_abertas.first().id}),
                        votacoes_abertas.first().__str__())))
            msg = _('Existe mais de uma vota????o aberta na Sess??o: ' +
                    ('''<li><a href="%s">%s</a></li>''' % (
                        reverse('sapl.sessao:sessaoplenaria_detail',
                                kwargs={'pk': votacoes_abertas.first().id}),
                        votacoes_abertas.first().__str__())) +
                    'Para votar, pe??a para que o Operador as feche.')
            messages.add_message(request, messages.INFO, msg)
            return None, msg

    return votacoes_abertas.first(), None


def votacao(context,context_vars):
    logger = logging.getLogger(__name__)
    parlamentar = context_vars['votante'].parlamentar
    parlamentar_presente = False
    if parlamentar.id in context_vars['presentes']:
        parlamentar_presente = True
        context_vars.update({'parlamentar': parlamentar})
    else:
        context.update({'error_message':
                        'N??o h?? presentes na Sess??o com a '
                        'mat??ria em vota????o.'})

    if parlamentar_presente:
        voto = []
        if context_vars['ordem_dia']:
            voto = VotoParlamentar.objects.filter(
                ordem=context_vars['ordem_dia'])
        elif context_vars['expediente']:
            voto = VotoParlamentar.objects.filter(
                expediente=context_vars['expediente'])

        if voto:
            try:
                logger.debug("Tentando obter objeto VotoParlamentar com parlamentar={}.".format(context_vars['parlamentar']))
                voto = voto.get(parlamentar=context_vars['parlamentar'])
                context.update({'voto_parlamentar': voto.voto})
            except ObjectDoesNotExist:
                logger.error("Voto do parlamentar {} n??o computado.".format(context_vars['parlamentar']))
                context.update(
                    {'voto_parlamentar': 'Voto n??o '
                     'computado.'})
    else:
        logger.error("Parlamentar com id={} n??o est?? presente na "
                    "Ordem do Dia/Expediente em vota????o.".format(parlamentar.id))
        context.update({'error_message':
                        'Voc?? n??o est?? presente na '
                        'Ordem do Dia/Expediente em vota????o.'})
    return context, context_vars

def sessao_votacao(context,context_vars):
    pk = context_vars['sessao'].pk
    context.update({'sessao_id': pk})
    context.update({'sessao': context_vars['sessao'],
                    'data': context_vars['sessao'].data_inicio,
                    'hora': context_vars['sessao'].hora_inicio})

    # Inicializa presentes
    presentes = []
    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)
    errors_msgs = {'materia':'N??o h?? nenhuma mat??ria aberta.',
            'registro':'A vota????o para esta mat??ria j?? encerrou.',
            'tipo':'A mat??ria aberta n??o ?? do tipo vota????o nominal.'}

    materia_aberta = None
    if ordem_dia:
        materia_aberta = ordem_dia
        presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=pk).values_list(
            'parlamentar_id', flat=True).distinct()
    elif expediente:
        materia_aberta = expediente
        presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=pk).values_list(
            'parlamentar_id', flat=True).distinct()

    context_vars.update({'ordem_dia': ordem_dia,
                        'expediente':expediente,
                        'presentes': presentes})

    # Verifica vota????o aberta
    # Se aberta, verifica se ?? nominal. ID nominal == 2
    erro = None
    if not materia_aberta:
        erro = 'materia'
    elif materia_aberta.registro_aberto:
        erro = 'registro'
    elif materia_aberta.tipo_votacao != VOTACAO_NOMINAL:
        erro = 'tipo'

    if not erro:
        context.update({'materia': materia_aberta.materia,
                        'ementa': materia_aberta.materia.ementa})
        context, context_vars = votacao(context, context_vars)
    else:
        context.update({'error_message': errors_msgs[erro]})

    return context, context_vars


def can_vote(context, context_vars, request):
    context.update({'permissao': True})

    # Pega sess??o
    sessao, msg = votacao_aberta(request)
    context_vars.update({'sessao':sessao})
    if sessao and not msg:
        context, context_vars = sessao_votacao(context, context_vars)
    elif not sessao and msg:
        return HttpResponseRedirect('/')
    else:
        context.update(
            {'error_message': 'N??o h?? nenhuma sess??o com mat??ria aberta.'})
    return context, context_vars


def votante_view(request):
    logger = logging.getLogger(__name__)
    username = request.user.username

    # Pega o votante relacionado ao usu??rio
    template_name = 'painel/voto_nominal.html'
    context = {}
    context_vars = {}

    try:
        logger.debug('user=' + username + '. Tentando obter objeto Votante com user={}.'.format(request.user))
        votante = Votante.objects.get(user=request.user)
    except ObjectDoesNotExist:
        logger.error("user=" + username + ". Usu??rio (user={}) n??o cadastrado como votante na tela de parlamentares. " 
                     "Contate a administra????o de sua Casa Legislativa!".format(request.user))
        msg = _("Usu??rio n??o cadastrado como votante na tela de parlamentares. Contate a administra????o de sua Casa Legislativa!")
        context.update({
            'error_message':msg
        })

        return render(request, template_name, context)
    context_vars = {'votante': votante}
    context = {'head_title': str(_('Vota????o Individual'))}

    # Verifica se usu??rio possui permiss??o para votar
    if 'parlamentares.can_vote' in request.user.get_all_permissions():
        context, context_vars = can_vote(context, context_vars, request)
        logger.debug("user=" + username + ". Verificando se usu??rio {} possui permiss??o para votar.".format(request.user))
    else:
        logger.error("user=" + username + ". Usu??rio {} sem permiss??o para votar.".format(request.user))
        context.update({'permissao': False,
                        'error_message': 'Usu??rio sem permiss??o para votar.'})

    # Salva o voto
    if request.method == 'POST':
        if context_vars['ordem_dia']:
            try:
                logger.info("user=" + username + ". Tentando obter objeto VotoParlamentar para parlamentar={} e ordem={}."
                            .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto = VotoParlamentar.objects.get(
                    parlamentar=context_vars['parlamentar'],
                    ordem=context_vars['ordem_dia'])
            except ObjectDoesNotExist:
                logger.error("user=" + username + ". Erro ao obter VotoParlamentar para parlamentar={} e ordem={}. Criando objeto."
                             .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto = VotoParlamentar.objects.create(
                    parlamentar=context_vars['parlamentar'],
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    ordem=context_vars['ordem_dia'])
            else:
                logger.info("user=" + username + ". VotoParlamentar para parlamentar={} e ordem={} obtido com sucesso."
                            .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        elif context_vars['expediente']:
            try:
                logger.info("user=" + username + ". Tentando obter objeto VotoParlamentar para parlamentar={} e expediente={}."
                            .format(context_vars['parlamentar'], context_vars['expediente']))
                voto = VotoParlamentar.objects.get(
                    parlamentar=context_vars['parlamentar'],
                    expediente=context_vars['expediente'])
            except ObjectDoesNotExist:
                logger.error("user=" + username + ". Erro ao obter VotoParlamentar para parlamentar={} e expediente={}. Criando objeto."
                             .format(context_vars['parlamentar'], context_vars['expediente']))
                voto = VotoParlamentar.objects.create(
                    parlamentar=context_vars['parlamentar'],
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    expediente=context_vars['expediente'])
            else:
                logger.info("user=" + username + ". VotoParlamentar para parlamentar={} e expediente={} obtido com sucesso."
                            .format(context_vars['parlamentar'], context_vars['expediente']))
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual'))

    return render(request, template_name, context)


@user_passes_test(check_permission)
def painel_view(request, pk):
    exibicao = {
        'parlamentares': True,
        'oradores': True,
        'cronometros': True,
        'resultado': True,
        'materia': True
    }
    now = timezone.localtime(timezone.now())
    utc_offset = now.utcoffset().total_seconds() / 60
    context = {'head_title': str(_('Painel Plen??rio')), 
               'sessao_id': pk, 
               'cronometros': Cronometro.objects.filter(ativo=True).order_by('ordenacao'),
               'painel_config': PainelConfig.objects.first(),
               'casa': CasaLegislativa.objects.last(),
               'exibicao': exibicao,
               'utc_offset': utc_offset,
               }
    return render(request, 'painel/index.html', context)

def bit_is_set(number, bit):
    return (number & (1 << bit)) != 0

@user_passes_test(check_permission)
def painel_parcial_view(request, pk, opcoes):
    opcoes = int(opcoes)
    exibicao = {
        'parlamentares': bit_is_set(opcoes,0),
        'oradores': bit_is_set(opcoes,1),
        'cronometros': bit_is_set(opcoes, 2),
        'resultado': bit_is_set(opcoes, 3),
        'materia': bit_is_set(opcoes, 4)
    }
    now = timezone.localtime(timezone.now())
    utc_offset = now.utcoffset().total_seconds() / 60
    context = {'head_title': str(_('Painel Plen??rio')), 
               'sessao_id': pk, 
               'cronometros': Cronometro.objects.filter(ativo=True).order_by('ordenacao'),
               'painel_config': PainelConfig.objects.first(),
               'casa': CasaLegislativa.objects.last(),
               'exibicao': exibicao,
               'utc_offset': utc_offset,
               }
    return render(request, 'painel/index.html', context)


@user_passes_test(check_permission)
def switch_painel(request):
    sessao = SessaoPlenaria.objects.get(id=request.POST['pk_sessao'])
    switch = json.loads(request.POST['aberto'])

    if switch:
        sessao.painel_aberto = True
    else:
        sessao.painel_aberto = False

    sessao.save()
    return JsonResponse({})


@user_passes_test(check_permission)
def verifica_painel(request):
    sessao = SessaoPlenaria.objects.get(id=request.GET['pk_sessao'])
    status = sessao.painel_aberto

    CRONOMETRO_STATUS = {
        'I': 'start',
        'R': 'reset',
        'S': 'stop',
        'C': 'increment'
    }

    dict_status_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'status'))

    for key, value in dict_status_cronometros.items():
        dict_status_cronometros[key] = CRONOMETRO_STATUS[dict_status_cronometros[key]]
    
    dict_duracao_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'duracao_cronometro'))
    
    for key, value in dict_duracao_cronometros.items():
        dict_duracao_cronometros[key] = value.seconds

    resposta = JsonResponse(dict(status=status, 
                                 cronometros=dict_status_cronometros, 
                                 duracao_cronometros=dict_duracao_cronometros)
                            )
    return resposta


@user_passes_test(check_permission)
def painel_mensagem_view(request):
    return render(request, 'painel/mensagem.html')


@user_passes_test(check_permission)
def painel_parlamentar_view(request):
    return render(request, 'painel/parlamentares.html')


@user_passes_test(check_permission)
def painel_votacao_view(request):
    return render(request, 'painel/votacao.html')


CRONOMETRO_STATUS = {
        'start': 'I',
        'reset': 'R',
        'stop': 'S',
        'increment': 'C'
}

@user_passes_test(check_permission)
def cronometro_painel(request):
    acao = request.GET['action']
    cronometro_id = request.GET['tipo'].split('cronometro_')[1]
    cronometro = Cronometro.objects.get(id=cronometro_id)
    cronometro.status = CRONOMETRO_STATUS[acao]
    cronometro.ultima_alteracao_status = timezone.now()
    # Caso n??o seja stop, last_time vir?? como 0
    cronometro.last_stop_duration = request.GET.get('last_time')
    cronometro.save()
    return HttpResponse({})


def get_materia_aberta(pk):
    return OrdemDia.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_presentes(pk, response, materia):
    if type(materia) == OrdemDia:
        presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=pk)
    else:
        presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=pk)
    
    sessao = SessaoPlenaria.objects.get(id=pk)
    num_presentes = len(presentes)
    data_sessao = sessao.data_inicio
    oradores = OradorExpediente.objects.filter(
        sessao_plenaria_id=pk).order_by('numero_ordem')

    oradores_list = []
    for o in oradores:

        oradores_list.append(
            {
                'nome': o.parlamentar.nome_parlamentar,
                'numero': o.numero_ordem
            })

    presentes_list = []
    for p in presentes:
        legislatura = sessao.legislatura
        # Recupera os mandatos daquele parlamentar
        mandatos = p.parlamentar.mandato_set.filter(legislatura=legislatura)

        if p.parlamentar.ativo and mandatos:
            filiacao = filiacao_data(p.parlamentar, data_sessao, data_sessao)
            if not filiacao:
                partido = 'Sem Registro'
            else:
                partido = filiacao

            presentes_list.append(
                {'id': p.id,
                 'parlamentar_id': p.parlamentar.id,
                 'nome': p.parlamentar.nome_parlamentar,
                 'partido': partido,
                 'voto': ''
                 })

        elif not p.parlamentar.ativo or not mandatos:
            num_presentes += -1

    if materia:
        if materia.tipo_votacao == 1:
            tipo_votacao = 'Simb??lica'
        elif materia.tipo_votacao == 2:
            tipo_votacao = 'Nominal'
        elif materia.tipo_votacao == 3:
            tipo_votacao = 'Secreta'
        elif materia.tipo_votacao == 4:
            tipo_votacao = 'Leitura'
        
        ementa = materia.ementa if len(materia.ementa) < 320 else materia.ementa[:320] + '...'

        response.update({
            'tipo_resultado': materia.resultado,
            'observacao_materia': html.unescape(materia.observacao),
            'materia_ementa' : ementa,
            'tipo_votacao': tipo_votacao,
            'materia_legislativa_texto': str(materia.materia)
        })

    presentes_list = sort_lista_chave(presentes_list, 'nome')

    response.update({
        'presentes': presentes_list,
        'num_presentes': num_presentes,
        'oradores': oradores_list,
        'msg_painel': str(_('Vota????o aberta!')),
    })

    return response


def get_materia_expediente_aberta(pk):
    return ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def response_nenhuma_materia(response):
    response.update({
        'msg_painel': str(_('Nenhuma mat??ria disponivel para vota????o.'))})
    return JsonResponse(response)


def get_votos(response, materia):
    logger = logging.getLogger(__name__)
    if type(materia) == OrdemDia:
        if materia.tipo_votacao != 4:
            registro = RegistroVotacao.objects.filter(
                ordem=materia, materia=materia.materia).order_by('data_hora').last()
            leitura = None
        else:
            leitura = RegistroLeitura.objects.filter(
                ordem=materia, materia=materia.materia).order_by('data_hora').last()
            registro = None
        tipo = 'ordem'
    elif type(materia) == ExpedienteMateria:
        if materia.tipo_votacao != 4:
            registro = RegistroVotacao.objects.filter(
                expediente=materia, materia=materia.materia).order_by('data_hora').last()
            leitura = None
        else:
            leitura = RegistroLeitura.objects.filter(
                expediente=materia, materia=materia.materia).order_by('data_hora').last()
            registro = None
        tipo = 'expediente'

    if not registro and not leitura:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'registro': None,
            'total_votos': 0,
            'tipo_resultado': 'Ainda n??o foi votada.',
        })

        if materia.tipo_votacao == 2:
            if tipo == 'ordem':
                votos_parlamentares = VotoParlamentar.objects.filter(
                    ordem_id=materia.id).order_by(
                        'parlamentar__nome_parlamentar')
            else:
                votos_parlamentares = VotoParlamentar.objects.filter(
                    expediente_id=materia.id).order_by(
                        'parlamentar__nome_parlamentar')
            
            if PainelConfig.attr('mostrar_votos_antecedencia'):
                response['numero_votos_sim'] = votos_parlamentares.filter(voto="Sim").count()
                response['numero_votos_nao'] = votos_parlamentares.filter(voto="N??o").count()
                response['numero_abstencoes'] = votos_parlamentares.filter(voto="Absten????o").count()
                response['total_votos'] = response['numero_votos_sim'] + response['numero_votos_nao'] + \
                                          response['numero_abstencoes']

            for i, p in enumerate(response['presentes']):
                try:
                    logger.info("Tentando obter votos do parlamentar (id={}).".format(p['parlamentar_id']))
                    vot_parl = votos_parlamentares.get(parlamentar_id=p['parlamentar_id']).voto
                    if vot_parl:
                        response['presentes'][i]['voto'] = vot_parl
                    else:
                        response['presentes'][i]['voto'] = ''
                except ObjectDoesNotExist:
                    logger.error("Votos do parlamentar (id={}) n??o encontrados. Retornado vazio."
                                 .format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = ''
    elif leitura:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'registro': True,
            'total_votos': 0,
            'tipo_resultado': 'Mat??ria lida.',
        })
    else:
        total = (registro.numero_votos_sim +
                 registro.numero_votos_nao +
                 registro.numero_abstencoes)

        if materia.tipo_votacao == 2:
            votos_parlamentares = VotoParlamentar.objects.filter(
                votacao_id=registro.id).order_by(
                    'parlamentar__nome_parlamentar')

            for i, p in enumerate(response['presentes']):
                try:
                    logger.debug("Tentando obter votos do parlamentar (id={}).".format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = votos_parlamentares.get(
                        parlamentar_id=p['parlamentar_id']).voto
                except ObjectDoesNotExist:
                    logger.error("Votos do parlamentar (id={}) n??o encontrados. Retornado None.".format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = None

        response.update({
            'numero_votos_sim': registro.numero_votos_sim,
            'numero_votos_nao': registro.numero_votos_nao,
            'numero_abstencoes': registro.numero_abstencoes,
            'registro': True,
            'total_votos': total,
            'tipo_resultado': registro.tipo_resultado_votacao.nome,
        })

    return response


@user_passes_test(check_permission)
def get_dados_painel(request, pk):
    sessao = SessaoPlenaria.objects.get(id=pk)

    casa = CasaLegislativa.objects.first()

    app_config = ConfiguracoesAplicacao.objects.first()

    brasao = None
    if casa and app_config and (bool(casa.logotipo)):
        brasao = casa.logotipo.url \
            if app_config.mostrar_brasao_painel else None
    
    CRONOMETRO_STATUS = {
        'I': 'start',
        'R': 'reset',
        'S': 'stop',
        'C': 'increment'
    }

    dict_status_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'status'))

    for key, value in dict_status_cronometros.items():
        dict_status_cronometros[key] = CRONOMETRO_STATUS[dict_status_cronometros[key]]
    
    dict_duracao_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'duracao_cronometro'))
    
    for key, value in dict_duracao_cronometros.items():
        dict_duracao_cronometros[key] = value.seconds

    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'cronometros': dict_status_cronometros,
        'duracao_cronometros': dict_duracao_cronometros,
        'sessao_solene': sessao.tipo.nome == "Solene",
        'sessao_finalizada': sessao.finalizada,
        'tema_solene': sessao.tema_solene,
        'status_painel': sessao.painel_aberto,
        'brasao': brasao
    }

    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)

    # Caso tenha alguma mat??ria com vota????o aberta, ela ?? mostrada no painel
    # com prioridade para Ordem do Dia.
    if ordem_dia:
        return JsonResponse(get_votos(
            get_presentes(pk, response, ordem_dia),
            ordem_dia))
    elif expediente:
        return JsonResponse(get_votos(
            get_presentes(pk, response, expediente),
            expediente))

    # Caso n??o tenha nenhuma aberta,
    # a mat??ria a ser mostrada no Painel deve ser a ??ltima votada
    last_ordem_voto = RegistroVotacao.objects.filter(
        ordem__sessao_plenaria=sessao).order_by('data_hora').last()
    last_expediente_voto = RegistroVotacao.objects.filter(
        expediente__sessao_plenaria=sessao).order_by('data_hora').last()

    last_ordem_leitura = RegistroLeitura.objects.filter(
        ordem__sessao_plenaria=sessao).order_by('data_hora').last()
    last_expediente_leitura = RegistroLeitura.objects.filter(
        expediente__sessao_plenaria=sessao).order_by('data_hora').last()

    # Obt??m ??ltima mat??ria que foi votada, atrav??s do timestamp mais recente
    ordem_expediente = None
    ultimo_timestamp = None
    if last_ordem_voto:
        ordem_expediente = last_ordem_voto.ordem
        ultimo_timestamp = last_ordem_voto.data_hora
    if (last_expediente_voto and ultimo_timestamp and last_expediente_voto.data_hora > ultimo_timestamp) or \
        (not ultimo_timestamp and last_expediente_voto):
        ordem_expediente = last_expediente_voto.expediente
        ultimo_timestamp = last_expediente_voto.data_hora
    if (last_ordem_leitura and ultimo_timestamp and last_ordem_leitura.data_hora > ultimo_timestamp) or \
        (not ultimo_timestamp and last_ordem_leitura):
        ordem_expediente = last_ordem_leitura.ordem
        ultimo_timestamp = last_ordem_leitura.data_hora
    if (last_expediente_leitura and ultimo_timestamp and last_expediente_leitura.data_hora > ultimo_timestamp) or \
        (not ultimo_timestamp and last_expediente_leitura):
        ordem_expediente = last_expediente_leitura.expediente
        ultimo_timestamp = last_expediente_leitura.data_hora
    
    if ordem_expediente:
        return JsonResponse(get_votos(
                            get_presentes(pk, response, ordem_expediente),
                            ordem_expediente))

    # Retorna que n??o h?? nenhuma mat??ria j?? votada ou aberta
    return response_nenhuma_materia(get_presentes(pk, response, None))


@user_passes_test(check_permission)
def painel_discurso_view(request, sessao_pk, lista_pk):
    cronometros_ids = CronometroLista.objects.filter(tipo_lista_id=lista_pk).values_list('cronometro', flat=True)
    cronometros = Cronometro.objects.filter(id__in=cronometros_ids)
    lista = ListaDiscurso.objects.get(tipo_id=lista_pk, sessao_plenaria_id=sessao_pk)
    
    context = {
                'head_title': str(_('Painel de Discurso')), 
                'sessao_id': sessao_pk, 
                'lista': lista,
                'cronometros': cronometros,
                'casa': CasaLegislativa.objects.last(),
                'painel_config': PainelConfig.objects.first(),
            }
    return render(request, 'painel/painel_discurso.html', context)


@user_passes_test(check_permission)
def get_dados_painel_discurso(request, pk, lista_pk):
    sessao = SessaoPlenaria.objects.get(id=pk)

    casa = CasaLegislativa.objects.first()

    app_config = ConfiguracoesAplicacao.objects.first()

    brasao = None
    if casa and app_config and (bool(casa.logotipo)):
        brasao = casa.logotipo.url \
            if app_config.mostrar_brasao_painel else None
    
    CRONOMETRO_STATUS = {
        'I': 'start',
        'R': 'reset',
        'S': 'stop',
        'C': 'increment'
    }

    cronometros = Cronometro.objects.filter(cronometrolista__tipo_lista_id=lista_pk)

    dict_status_cronometros = dict(cronometros.order_by('ordenacao').values_list('id', 'status'))

    for key, value in dict_status_cronometros.items():
        dict_status_cronometros[key] = CRONOMETRO_STATUS[dict_status_cronometros[key]]
    
    dict_duracao_cronometros = dict(cronometros.values_list('id', 'duracao_cronometro'))
    
    for key, value in dict_duracao_cronometros.items():
        dict_duracao_cronometros[key] = value.seconds

    lista = ListaDiscurso.objects.get(tipo_id=lista_pk, sessao_plenaria_id=pk)
    orador = lista.orador_atual
    oradores = ParlamentarLista.objects.filter(lista=lista).order_by('ordenacao').values_list('parlamentar__nome_parlamentar', flat=True)
    
    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'cronometros': dict_status_cronometros,
        'duracao_cronometros': dict_duracao_cronometros,
        'sessao_finalizada': sessao.finalizada,
        'brasao': brasao,
        'orador': orador.nome_parlamentar if orador else '',
        'orador_img': orador.fotografia.url if orador and os.path.isfile(orador.fotografia.path) else None,
        'oradores': list(oradores)
    }

    return JsonResponse(response)
