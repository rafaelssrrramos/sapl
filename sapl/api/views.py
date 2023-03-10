import logging

from django import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.decorators import classonlymethod
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
import django_filters
from django_filters.filters import CharFilter
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.utils import resolve_field
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers as rest_serializers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.fields import SerializerMethodField
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework.views import APIView

from sapl.api.forms import SaplFilterSetMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import ChoiceSerializer, ParlamentarResumeSerializer
from sapl.base.models import Autor, AppConfig, DOC_ADM_OSTENSIVO
from sapl.materia.models import Proposicao, TipoMateriaLegislativa,\
    MateriaLegislativa, Tramitacao
from sapl.norma.models import NormaJuridica
from sapl.painel.models import Cronometro
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo, TramitacaoAdministrativo, Anexado
from sapl.sessao.models import SessaoPlenaria, ExpedienteSessao, SessaoPlenariaPresenca
from sapl.utils import models_with_gr_for_model, choice_anos_com_sessaoplenaria
from sapl.parlamentares.models import Mandato, Parlamentar, Legislatura


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.get(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})


class BusinessRulesNotImplementedMixin:
    def create(self, request, *args, **kwargs):
        raise Exception(_("POST Create n??o implementado"))

    def update(self, request, *args, **kwargs):
        raise Exception(_("PUT and PATCH n??o implementado"))

    def delete(self, request, *args, **kwargs):
        raise Exception(_("DELETE Delete n??o implementado"))


class SaplApiViewSet(ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SaplApiViewSetConstrutor():

    _built_sets = {}

    @classonlymethod
    def get_class_for_model(cls, model):
        return cls._built_sets[model._meta.app_config][model]

    @classonlymethod
    def build_class(cls):
        import inspect
        from sapl.api import serializers

        # Carrega todas as classes de sapl.api.serializers que possuam
        # "Serializer" como Sufixo.
        serializers_classes = inspect.getmembers(serializers)
        serializers_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('Serializer'),
            serializers_classes
        )}

        # Carrega todas as classes de sapl.api.forms que possuam
        # "FilterSet" como Sufixo.
        from sapl.api import forms
        filters_classes = inspect.getmembers(forms)
        filters_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('FilterSet'),
            filters_classes
        )}

        built_sets = {}

        def build(_model):
            object_name = _model._meta.object_name

            # Caso Exista, pega a classe sapl.api.serializers.{model}Serializer
            serializer_name = '{model}Serializer'.format(model=object_name)
            _serializer_class = serializers_classes.get(serializer_name, None)

            # Caso Exista, pega a classe sapl.api.forms.{model}FilterSet
            filter_name = '{model}FilterSet'.format(model=object_name)
            _filter_class = filters_classes.get(filter_name, None)

            def create_class():
                # Define uma classe padr??o para serializer caso n??o tenha sido
                # criada a classe sapl.api.serializers.{model}Serializer
                class SaplSerializer(rest_serializers.ModelSerializer):
                    __str__ = SerializerMethodField()

                    class Meta:
                        model = _model
                        fields = '__all__'

                    def get___str__(self, obj):
                        return str(obj)

                # Define uma classe padr??o para filtro caso n??o tenha sido
                # criada a classe sapl.api.forms.{model}FilterSet
                class SaplFilterSet(SaplFilterSetMixin):
                    class Meta(SaplFilterSetMixin.Meta):
                        model = _model

                # Define uma classe padr??o ModelViewSet de DRF
                class ModelSaplViewSet(SaplApiViewSet):
                    queryset = _model.objects.all()

                    # Utiliza o filtro customizado pela classe
                    # sapl.api.forms.{model}FilterSet
                    # ou utiliza o trivial SaplFilterSet definido acima
                    filter_class = _filter_class \
                        if _filter_class else SaplFilterSet

                    # Utiliza o serializer customizado pela classe
                    # sapl.api.serializers.{model}Serializer
                    # ou utiliza o trivial SaplSerializer definido acima
                    serializer_class = _serializer_class \
                        if _serializer_class else SaplSerializer

                return ModelSaplViewSet

            viewset = create_class()
            viewset.__name__ = '%sModelSaplViewSet' % _model.__name__
            return viewset

        apps_sapl = [apps.apps.get_app_config(
            n[5:]) for n in settings.SAPL_APPS]
        for app in apps_sapl:
            cls._built_sets[app] = {}
            for model in app.get_models():
                cls._built_sets[app][model] = build(model)


SaplApiViewSetConstrutor.build_class()

"""
1. Constroi uma rest_framework.viewsets.ModelViewSet para 
   todos os models de todas as apps do sapl
2. Define DjangoFilterBackend como ferramenta de filtro dos campos
3. Define Serializer como a seguir:
    3.1 - Define um Serializer gen??rico para cada m??del
    3.2 - Recupera Serializer customizado em sapl.api.serializers
    3.3 - Para todo model ?? opcional a exist??ncia de 
          sapl.api.serializers.{model}Serializer.
          Caso n??o seja definido um Serializer customizado, utiliza-se o trivial
4. Define um FilterSet como a seguir:
    4.1 - Define um FilterSet gen??rico para cada m??del
    4.2 - Recupera FilterSet customizado em sapl.api.forms
    4.3 - Para todo model ?? opcional a exist??ncia de 
          sapl.api.forms.{model}FilterSet.
          Caso n??o seja definido um FilterSet customizado, utiliza-se o trivial
    4.4 - todos os campos que aceitam lookup 'exact' 
          podem ser filtrados por default
    
5. SaplApiViewSetConstrutor n??o cria padr??es e/ou exige conhecimento alem dos
    exigidos pela DRF. 
    
6. As rotas s??o criadas seguindo nome da app e nome do model
    http://localhost:9000/api/{applabel}/{model_name}/
    e seguem as varia????es definidas em:
    https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
    
7. Todas as viewsets constru??das por SaplApiViewSetConstrutor e suas rotas
    (paginate list, detail, edit, create, delete)
   bem como testes em ambiente de desenvolvimento podem ser conferidas em:
   http://localhost:9000/api/ 
   desde que settings.DEBUG=True

**SaplApiViewSetConstrutor._built_sets** ?? um dict de dicts de models conforme:
    {
        ...
    
        'audiencia': {
            'tipoaudienciapublica': TipoAudienciaPublicaViewSet,
            'audienciapublica': AudienciaPublicaViewSet,
            'anexoaudienciapublica': AnexoAudienciaPublicaViewSet
            
            ...
            
            },
            
        ...
        
        'base': {
            'casalegislativa': CasaLegislativaViewSet,
            'appconfig': AppConfigViewSet,
            
            ...
            
        }
        
        ...
        
    }
"""

# Toda Classe construida acima, pode ser redefinida e aplicado quaisquer
# das possibilidades para uma classe normal criada a partir de
# rest_framework.viewsets.ModelViewSet conforme exemplo para a classe autor

# decorator para recuperar e transformar o default


class customize(object):
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):

        class _SaplApiViewSet(
            cls,
                SaplApiViewSetConstrutor._built_sets[
                    self.model._meta.app_config][self.model]
        ):
            pass

        if hasattr(_SaplApiViewSet, 'build'):
            _SaplApiViewSet = _SaplApiViewSet.build()

        SaplApiViewSetConstrutor._built_sets[
            self.model._meta.app_config][self.model] = _SaplApiViewSet
        return _SaplApiViewSet


# Customiza????o para AutorViewSet com implementa????o de actions espec??ficas


@customize(Autor)
class _AutorViewSet:
    """
    Neste exemplo de customiza????o do que foi criado em 
    SaplApiViewSetConstrutor al??m do ofertado por 
    rest_framework.viewsets.ModelViewSet, dentre outras customiza????es
    poss??veis, foi adicionado as rotas referentes aos relacionamentos gen??ricos

    * padr??o de ModelViewSet
        /api/base/autor/       POST   - create
        /api/base/autor/       GET    - list     
        /api/base/autor/{pk}/  GET    - detail          
        /api/base/autor/{pk}/  PUT    - update      
        /api/base/autor/{pk}/  PATCH  - partial_update 
        /api/base/autor/{pk}/  DELETE - destroy

    * rotas desta classe local criadas pelo m??todo build:
        /api/base/autor/parlamentar
            devolve apenas autores que s??o parlamentares
        /api/base/autor/comissao
            devolve apenas autores que s??o comiss??es
        /api/base/autor/bloco
            devolve apenas autores que s??o blocos parlamentares
        /api/base/autor/bancada
            devolve apenas autores que s??o bancadas parlamentares        
        /api/base/autor/frente
            devolve apenas autores que s??o Frene parlamentares
        /api/base/autor/orgao
            devolve apenas autores que s??o ??rg??os
    """

    def list_for_content_type(self, content_type):
        qs = self.get_queryset()
        qs = qs.filter(content_type=content_type)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    @classonlymethod
    def build(cls):

        models_with_gr_for_autor = models_with_gr_for_model(Autor)

        for _model in models_with_gr_for_autor:

            @action(detail=False, name=_model._meta.model_name)
            def actionclass(self, request, *args, **kwargs):
                model = getattr(self, self.action)._AutorViewSet__model

                content_type = ContentType.objects.get_for_model(model)
                return self.list_for_content_type(content_type)

            func = actionclass
            func.mapping['get'] = func.kwargs['name']
            func.url_name = func.kwargs['name']
            func.url_path = func.kwargs['name']
            func.__model = _model

            setattr(cls, _model._meta.model_name, func)
        return cls


@customize(Parlamentar)
class _ParlamentarViewSet:
    class ParlamentarPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
            else:
                perm = super().has_permission(request, view)
                return perm
                
    permission_classes = (ParlamentarPermission, )

    @action(detail=True)
    def proposicoes(self, request, *args, **kwargs):
        """
        Lista de proposi????es p??blicas de parlamentar espec??fico

        :param int id: - Identificador do parlamentar que se quer recuperar as proposi????es
        :return: uma lista de proposi????es
        """
        # /api/parlamentares/parlamentar/{id}/proposicoes/
        # recupera proposi????es enviadas e incorporadas do parlamentar
        # deve coincidir com
        # /parlamentar/{pk}/proposicao
        content_type = ContentType.objects.get_for_model(Parlamentar)

        qs = Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=False,
            cancelado=False,
            autor__object_id=kwargs['pk'],
            autor__content_type=content_type
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SaplApiViewSetConstrutor.get_class_for_model(
                Proposicao).serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)
    
    @action(detail=True)
    def parlamentares_by_legislatura(self,request,*args,**kwargs):
        """
        Pega lista de parlamentares pelo id da legislatura.
        """
        try:
            legislatura = Legislatura.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            return Response("") 
        data_atual = timezone.now().date()

        filter_params = {
            'legislatura':legislatura,
            'data_inicio_mandato__gte':legislatura.data_inicio,
            'data_fim_mandato__gte':legislatura.data_fim,
        }

        if legislatura.data_inicio < data_atual < legislatura.data_fim:
            filter_params['data_fim_mandato__gte'] = data_atual

        mandatos = Mandato.objects.filter(**filter_params).order_by('-data_inicio_mandato')  
        parlamentares = Parlamentar.objects.filter(mandato__in=mandatos).distinct()
        serializer_class = ParlamentarResumeSerializer(parlamentares,
                                                        many=True,
                                                        context={'request':request,'legislatura':kwargs['pk']})
        return Response(serializer_class.data)

    @action(detail=False,methods=['GET'])
    def search_parlamentares(self,request,*args,**kwargs):
        nome = request.query_params.get('nome_parlamentar','')
        parlamentares = Parlamentar.objects.filter(nome_parlamentar__icontains=nome)
        serializer_class= ParlamentarResumeSerializer(parlamentares,many=True,context={'request':request})
        return Response(serializer_class.data)


@customize(Proposicao)
class _ProposicaoViewSet():
    """
    list:
        Retorna lista de Proposi????es

        * Permiss??es:

            * Usu??rio Dono:
                * Pode listar todas suas Proposi????es 

            * Usu??rio Conectado ou An??nimo:
                * Pode listar todas as Proposi????es incorporadas

    retrieve:
        Retorna uma proposi????o passada pelo 'id'

        * Permiss??es:

            * Usu??rio Dono:
                * Pode recuperar qualquer de suas Proposi????es 

            * Usu??rio Conectado ou An??nimo:
                * Pode recuperar qualquer das proposi????es incorporadas

    """
    class ProposicaoPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
                # se a solicita????o ?? list ou detail, libera o teste de permiss??o
                # e deixa o get_queryset filtrar de acordo com a regra de
                # visibilidade das proposi????es, ou seja:
                # 1. proposi????o incorporada ?? proposi????o p??blica
                # 2. n??o incorporada s?? o autor pode ver
            else:
                perm = super().has_permission(request, view)
                return perm
                # n??o ?? list ou detail, ent??o passa pelas regras de permiss??o e,
                # depois disso ainda passa pelo filtro de get_queryset

    permission_classes = (ProposicaoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous():
            q |= Q(autor__autoruser__user=self.request.user)

        qs = qs.filter(q)
        return qs


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet:

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.last()

        serializer_class = SaplApiViewSetConstrutor.get_class_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.all()
        return self.list(request, *args, **kwargs)


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                TipoMateriaLegislativa.objects.reposicione(pk, d['pos_fim'])

        return Response(result)


@customize(DocumentoAdministrativo)
class _DocumentoAdministrativoViewSet:

    class DocumentoAdministrativoPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                comportamento = AppConfig.attr('documentos_administrativos')
                if comportamento == DOC_ADM_OSTENSIVO:
                    return True
                    """
                    Diante da l??gica implementada na manuten????o de documentos
                    administrativos:
                    - Se o comportamento ?? doc adm ostensivo, deve passar pelo 
                      teste de permiss??es sem avali??-las
                    - se o comportamento ?? doc adm restritivo, deve passar pelo
                      teste de permiss??es avaliando-as
                    """
            return super().has_permission(request, view)

    permission_classes = (DocumentoAdministrativoPermission, )

    def get_queryset(self):
        """
        mesmo tendo passado pelo teste de permiss??es, deve ser filtrado,
        pelo campo restrito. Sendo este igual a True, disponibilizar apenas
        a um usu??rio conectado. Apenas isso, sem crit??rios outros de permiss??o, 
        conforme implementado em DocumentoAdministrativoCrud
        """
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(restrito=True)
        return qs


@customize(DocumentoAcessorioAdministrativo)
class _DocumentoAcessorioAdministrativoViewSet:

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(TramitacaoAdministrativo)
class _TramitacaoAdministrativoViewSet(BusinessRulesNotImplementedMixin):
    # TODO: Implementar regras de manuten????o das tramita????es de docs adms

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(Anexado)
class _AnexadoViewSet(BusinessRulesNotImplementedMixin):

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(SessaoPlenaria)
class _SessaoPlenariaViewSet:

    @action(detail=False)
    def years(self, request, *args, **kwargs):
        years = choice_anos_com_sessaoplenaria()
        serializer = ChoiceSerializer(years, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def expedientes(self, request, *args, **kwargs):

        sessao = self.get_object()

        page = self.paginate_queryset(sessao.expedientesessao_set.all())
        if page is not None:
            serializer = SaplApiViewSetConstrutor.get_class_for_model(
                ExpedienteSessao).serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['GET'])
    def parlamentares_presentes(self, request, *args, **kwargs):
        sessao = self.get_object()
        parlamentares = Parlamentar.objects.filter(sessaoplenariapresenca__sessao_plenaria=sessao)

        page = self.paginate_queryset(parlamentares)
        if page is not None:
            serializer = SaplApiViewSetConstrutor.get_class_for_model(
                Parlamentar).serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)


@customize(NormaJuridica)
class _NormaJuridicaViewset:

    @action(detail=False, methods=['GET'])
    def destaques(self, request, *args, **kwargs):
        self.queryset = self.get_queryset().filter(norma_de_destaque=True)
        return self.list(request, *args, **kwargs)


@customize(Cronometro)
class _CronometroViewSet:

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()

        try:
            filter_condition = {k:v[0] for (k,v) in self.request.GET.items()}
            qs = qs.filter(**filter_condition)
        except FieldError as e:
            pass
        return qs


class AppVersionView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {
            'name': 'SAPL',
            'description': 'Sistema de Apoio ao Processo Legislativo',
            'version': settings.SAPL_VERSION,
            'user': request.user.username,
            'is_authenticated': request.user.is_authenticated(),
        }
        return Response(content)