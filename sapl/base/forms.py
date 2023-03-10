import logging
import os


from crispy_forms.bootstrap import FieldWithButtons, InlineRadios, StrictButton, FormActions
from crispy_forms.layout import HTML, Button, Div, Field, Fieldset, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q
from django.forms import Form, ModelForm, widgets
from django.utils import timezone
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.audiencia.models import AudienciaPublica
from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Reuniao, Comissao
from sapl.crispy_layout_mixin import (SaplFormLayout, form_actions, to_column,
                                      to_row, SaplFormHelper)
from sapl.materia.models import (MateriaLegislativa, UnidadeTramitacao, StatusTramitacao,
                                 DocumentoAcessorio, TipoMateriaLegislativa, MateriaEmTramitacao)
from sapl.norma.models import (NormaJuridica, NormaEstatisticas)
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.parlamentares.models import SessaoLegislativa, Partido, HistoricoPartido
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (autor_label, autor_modal, ChoiceWithoutValidationField,
                        choice_anos_com_normas, choice_anos_com_materias,
                        FilterOverridesMetaMixin, FileFieldCheckMixin,
                        intervalos_tem_intersecao,
                        ImageThumbnailFileInput, models_with_gr_for_model,
                        qs_override_django_filter, RangeWidgetOverride,
                        RANGE_ANOS, YES_NO_CHOICES, AnoNumeroOrderingFilter)
from .models import AppConfig, CasaLegislativa, AutorUser
from operator import xor


ACTION_CREATE_USERS_AUTOR_CHOICE = [
    ('A', _('Associar um usu??rio existente')),
    ('N', _('Autor sem Usu??rio de Acesso ao Sapl')),
]


STATUS_USER_CHOICE = [
    ('R', _('Apenas retirar Perfil de Autor do Usu??rio que est?? sendo'
            ' desvinculado')),
    ('D', _('Retirar Perfil de Autor e desativar Usu??rio que est?? sendo'
            ' desvinculado')),
    ('X', _('Excluir Usu??rio')),
]


def get_roles():
    roles = [(g.id, g.name) for g in Group.objects.all().order_by('name')
             if g.name != 'Votante']
    return roles


class UsuarioCreateForm(ModelForm):
    logger = logging.getLogger(__name__)
    firstname = forms.CharField(
        required=True,
        label="Nome",
        max_length=30
    )
    lastname = forms.CharField(
        required=True,
        label="Sobrenome",
        max_length=30
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Senha',
        min_length=6,
        max_length=128
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Confirmar senha',
        min_length=6,
        max_length=128
    )
    user_active = forms.ChoiceField(
        required=True,
        choices=YES_NO_CHOICES,
        label="Usu??rio ativo?",
        initial='True'
    )
    roles = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        choices=get_roles
    )

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD, 'firstname', 'lastname',
            'password1', 'password2', 'user_active', 'roles'
        ] + (['email']
             if get_user_model().USERNAME_FIELD != 'email' else [])

    def clean(self):
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data
        if data['password1'] != data['password2']:
            self.logger.warn('Erro de valida????o. Senhas informadas s??o diferentes.')
            raise ValidationError('Senhas informadas s??o diferentes')

        return data

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        row0 = to_row([('username', 12)])

        row1 = to_row([('firstname', 6),
                       ('lastname', 6)])

        row2 = to_row([('email', 6),
                       ('user_active', 6)])
        row3 = to_row(
            [('password1', 6),
             ('password2', 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row0,
            row1,
            row3,
            row2,
            'roles',
            form_actions(label='Confirmar'))


class UsuarioFilterSet(django_filters.FilterSet):

    username = django_filters.CharFilter(
        label=_('Nome de Usu??rio'),
        lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        super(UsuarioFilterSet, self).__init__(*args, **kwargs)

        row0 = to_row([('username', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Usu??rio'),
                     row0,
                     form_actions(label='Pesquisar'))
        )


class UsuarioEditForm(ModelForm):
    logger = logging.getLogger(__name__)
    # ROLES = [(g.id, g.name) for g in Group.objects.all().order_by('name')]
    ROLES = []

    token = forms.CharField(
        required=False,
        label="Token",
        max_length=40,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    first_name = forms.CharField(
        required=False,
        label="Nome",
        max_length=30)
    last_name = forms.CharField(
        required=False,
        label="Sobrenome",
        max_length=30)
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label='Senha')
    password2 = forms.CharField(
        required=False, widget=forms.PasswordInput,
        label='Confirmar senha')
    user_active = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=True,
        label="Usu??rio ativo?",
        initial='True')
    roles = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        choices=get_roles)

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD,
            "token",
            "first_name",
            "last_name",
            'password1',
            'password2',
            'user_active',
            'roles']

        if get_user_model().USERNAME_FIELD != 'email':
            fields.extend(['email'])

    def __init__(self, *args, **kwargs):
        super(UsuarioEditForm, self).__init__(*args, **kwargs)

        rows = to_row((
            ('first_name', 6),
            ('last_name', 6),
            ('email', 6),
            ('user_active', 6),
            ('password1', 6),
            ('password2', 6),
            ('roles', 12)))

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            'username',
            FieldWithButtons('token', StrictButton('Renovar', id="renovar-token", css_class="btn-outline-primary")),
            rows,
            form_actions(
                more=[
                    HTML("<a href='{% url 'sapl.base:user_detail' object.pk %}' "
                         "class='btn btn-dark'>Cancelar</a>")],
                label='Salvar Altera????es'))

    def clean(self):
        super().clean()
        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data
        if data['password1'] and data['password1'] != data['password2']:
            self.logger.warn("Erro de valida????o. Senhas informadas s??o diferentes.")
            raise ValidationError('Senhas informadas s??o diferentes')

        return data


class SessaoLegislativaForm(FileFieldCheckMixin, ModelForm):
    logger = logging.getLogger(__name__)

    class Meta:
        model = SessaoLegislativa
        exclude = []

    def clean(self):

        cleaned_data = super(SessaoLegislativaForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        flag_edit = True
        data_inicio = cleaned_data['data_inicio']
        data_fim = cleaned_data['data_fim']
        legislatura = cleaned_data['legislatura']
        numero = cleaned_data['numero']
        data_inicio_leg = legislatura.data_inicio
        data_fim_leg = legislatura.data_fim
        pk = self.initial['id'] if self.initial else None
        # Queries para verificar se existem Sess??es Legislativas no per??odo selecionado no form
        # Caso onde a data_inicio e data_fim s??o iguais a de alguma sess??o j??
        # criada
        primeiro_caso = Q(data_inicio=data_inicio, data_fim=data_fim)
        # Caso onde a data_inicio est?? entre o in??cio e o fim de uma Sess??o j??
        # existente
        segundo_caso = Q(data_inicio__lt=data_inicio,
                         data_fim__range=(data_inicio, data_fim))
        # Caso onde a data_fim est?? entre o in??cio e o fim de uma Sess??o j??
        # existente
        terceiro_caso = Q(data_inicio__range=(
            data_inicio, data_fim), data_fim__gt=data_fim)
        sessoes_existentes = SessaoLegislativa.objects.filter(primeiro_caso | segundo_caso | terceiro_caso).\
            exclude(pk=pk)

        if sessoes_existentes:
            raise ValidationError('J?? existe registrado uma Sess??o Legislativa que coincide com a data '
                                  'inserida, favor verificar as Sess??es existentes antes de criar uma '
                                  'nova Sess??o Legislativa')

        #sessoes_legislativas = SessaoLegislativa.objects.filter(legislatura=legislatura).exclude(pk=pk)

        # if sessoes_legislativas:
        #     numeracoes = [n.numero for n in sessoes_legislativas]
        #     numeracoes = sorted(numeracoes)
        #     ult = max(numeracoes)
        #
        # else:
        #     ult = SessaoLegislativa.objects.latest('data_fim')
        #     flag_edit = ult.id != pk
        #     ult = ult.numero

        ult = 0

        if numero <= ult and flag_edit:
            self.logger.warn(
                'O n??mero da SessaoLegislativa ({}) ?? menor ou igual '
                'que o de Sess??es Legislativas passadas ({})'.format(numero, ult)
            )
            raise ValidationError('O n??mero da Sess??o Legislativa n??o pode ser menor ou igual '
                                  'que o de Sess??es Legislativas passadas')

        if data_inicio < data_inicio_leg or \
                data_inicio > data_fim_leg:
            self.logger.warn(
                'A data de in??cio ({}) da SessaoLegislativa est?? compreendida '
                'fora da data in??cio ({}) e fim ({}) da Legislatura '
                'selecionada'.format(data_inicio, data_inicio_leg, data_fim_leg)
            )
            raise ValidationError('A data de in??cio da Sess??o Legislativa deve estar compreendida '
                                  'entre a data in??cio e fim da Legislatura selecionada')

        if data_fim > data_fim_leg or \
                data_fim < data_inicio_leg:
            self.logger.warn(
                'A data de fim ({}) da SessaoLegislativa est?? compreendida '
                'fora da data in??cio ({}) e fim ({}) da Legislatura '
                'selecionada.'.format(data_fim, data_inicio_leg, data_fim_leg)
            )
            raise ValidationError('A data de fim da Sess??o Legislativa deve estar compreendida '
                                  'entre a data in??cio e fim da Legislatura selecionada')

        if data_inicio > data_fim:
            self.logger.warn(
                'Data in??cio ({}) superior ?? data fim ({}).'.format(data_inicio, data_fim)
            )
            raise ValidationError(
                'Data in??cio n??o pode ser superior ?? data fim')

        data_inicio_intervalo = cleaned_data['data_inicio_intervalo']
        data_fim_intervalo = cleaned_data['data_fim_intervalo']

        if data_inicio_intervalo and data_fim_intervalo and \
                data_inicio_intervalo > data_fim_intervalo:
            self.logger.warn(
                'Data in??cio de intervalo ({}) superior ?? '
                'data fim de intervalo ({}).'.format(data_inicio_intervalo, data_fim_intervalo)
            )
            raise ValidationError('Data in??cio de intervalo n??o pode ser '
                                  'superior ?? data fim de intervalo')

        if data_inicio_intervalo:
            if data_inicio_intervalo < data_inicio or \
                    data_inicio_intervalo < data_inicio_leg or \
                    data_inicio_intervalo > data_fim or \
                    data_inicio_intervalo > data_fim_leg:
                self.logger.warn(
                    'A data de in??cio do intervalo ({}) n??o est?? compreendida entre '
                    'as datas de in??cio ({}) e fim ({}) tanto da Legislatura quanto da '
                    'pr??pria Sess??o Legislativa ({} e {}).'.format(
                        data_inicio_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim
                    )
                )
                raise ValidationError('A data de in??cio do intervalo deve estar compreendida entre '
                                      'as datas de in??cio e fim tanto da Legislatura quanto da '
                                      'pr??pria Sess??o Legislativa')
        if data_fim_intervalo:
            if data_fim_intervalo > data_fim or \
                    data_fim_intervalo > data_fim_leg or \
                    data_fim_intervalo < data_inicio or \
                    data_fim_intervalo < data_inicio_leg:
                self.logger.warn(
                    'A data de fim do intervalo ({}) n??o est?? compreendida entre '
                    'as datas de in??cio ({}) e fim ({}) tanto da Legislatura quanto da '
                    'pr??pria Sess??o Legislativa ({} e {}).'.format(
                        data_fim_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim
                    )
                )
                raise ValidationError('A data de fim do intervalo deve estar compreendida entre '
                                      'as datas de in??cio e fim tanto da Legislatura quanto da '
                                      'pr??pria Sess??o Legislativa')
        return cleaned_data


class TipoAutorForm(ModelForm):

    class Meta:
        model = TipoAutor
        fields = ['descricao']

    def __init__(self, *args, **kwargs):

        super(TipoAutorForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(TipoAutorForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data
        lista = ['comiss??o',
                 'comis',
                 'parlamentar',
                 'bancada',
                 'bloco',
                 'comissao',
                 'vereador',
                 '??rg??o',
                 'orgao',
                 'deputado',
                 'senador',
                 'vereadora',
                 'frente']

        for l in lista:
            if l in cd['descricao'].lower():
                raise ValidationError(_('A descri????o colocada n??o pode ser usada '
                                        'por ser equivalente a um tipo j?? existente'))


class AutorForm(ModelForm):
    logger = logging.getLogger(__name__)

    senha = forms.CharField(
        max_length=20,
        label=_('Senha'),
        required=False,
        widget=forms.PasswordInput())

    senha_confirma = forms.CharField(
        max_length=20,
        label=_('Confirmar Senha'),
        required=False,
        widget=forms.PasswordInput())

    email = forms.EmailField(
        required=False,
        label=_('Email'))

    confirma_email = forms.EmailField(
        required=False,
        label=_('Confirmar Email'))

    q = forms.CharField(
        max_length=50, required=False,
        label='Pesquise o nome do Autor com o '
        'tipo Selecionado e marque o escolhido.')

    autor_related = ChoiceWithoutValidationField(label='',
                                                 required=False,
                                                 widget=forms.RadioSelect())

    class Meta:
        model = Autor
        fields = ['tipo',
                  'nome',
                  'cargo',
                  'autor_related',
                  'q',
                  ]

    def __init__(self, *args, **kwargs):

        autor_related = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Pesquisar por poss??veis autores para '
                                    'o Tipo de Autor selecionado.')),
                StrictButton(
                    _('Filtrar'), css_class='btn-outline-primary btn-filtrar-autor',
                    type='button')),
            css_class='hidden',
            data_action='create',
            data_application='AutorSearch',
            data_field='autor_related')

        autor_select = Row(to_column(('tipo', 3)),
                           Div(to_column(('nome', 7)),
                               to_column(('cargo', 5)),
                               css_class="div_nome_cargo row col"),
                           to_column((autor_related, 9)),
                           to_column((Div(
                               Field('autor_related'),
                               css_class='radiogroup-autor-related hidden'),
                               12)))

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(autor_select)

        super().__init__(*args, **kwargs)

        if self.instance.pk:
            if self.instance.autor_related:
                self.fields['autor_related'].choices = [
                    (self.instance.autor_related.pk,
                     self.instance.autor_related)]

                self.fields['q'].initial = ''

            self.fields['autor_related'].initial = self.instance.autor_related
            

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            self.logger.warn(
                'Textos diferentes. ("{}" e "{}")'.format(texto1, texto2)
            )
            raise ValidationError(msg)
        return True

    def clean(self):
        super().clean()
        
        if not self.is_valid():
            return self.cleaned_data

        User = get_user_model()
        cd = self.cleaned_data

        if 'action_user' not in cd or not cd['action_user']:
            self.logger.warn(
                'N??o Informado se o Autor ter?? usu??rio '
                'vinculado para acesso ao Sistema.'
            )
            raise ValidationError(_('Informe se o Autor ter?? usu??rio '
                                    'vinculado para acesso ao Sistema.'))

        if 'status_user' in self.Meta.fields:
            if self.instance.pk and self.instance.user_id:
                if getattr(
                        self.instance.user,
                        get_user_model().USERNAME_FIELD) != cd['username']:
                    if 'status_user' not in cd or not cd['status_user']:
                        self.logger.warn(
                            'Foi trocado ou removido o usu??rio deste Autor ({}), '
                            'mas n??o foi informado como se deve proceder '
                            'com o usu??rio que est?? sendo desvinculado? ({})'.format(
                                cd['username'], get_user_model().USERNAME_FIELD
                            )
                        )
                        raise ValidationError(
                            _('Foi trocado ou removido o usu??rio deste Autor, '
                              'mas n??o foi informado como se deve proceder '
                              'com o usu??rio que est?? sendo desvinculado?'))

        qs_user = User.objects.all()
        qs_autor = Autor.objects.all()

        if self.instance.pk:
            qs_autor = qs_autor.exclude(pk=self.instance.pk)
            if self.instance.user:
                qs_user = qs_user.exclude(pk=self.instance.user.pk)

        if cd['action_user'] == 'A':
            param_username = {get_user_model().USERNAME_FIELD: cd['username']}
            if not User.objects.filter(**param_username).exists():
                self.logger.warn(
                    'N??o existe usu??rio com username "%s". ' % cd['username']
                )
                raise ValidationError(
                    _('N??o existe usu??rio com username "%s". '
                      'Para utilizar esse username voc?? deve selecionar '
                      '"Criar novo Usu??rio".') % cd['username'])

        if cd['action_user'] != 'N':

            if 'username' not in cd or not cd['username']:
                self.logger.warn('Username n??o informado.')
                raise ValidationError(_('O username deve ser informado.'))

            param_username = {
                'user__' + get_user_model().USERNAME_FIELD: cd['username']}

            autor_vinculado = qs_autor.filter(**param_username)
            if autor_vinculado.exists():
                nome = autor_vinculado[0].nome
                error_msg = 'J?? existe um autor para este ' \
                            'usu??rio ({}): {}'.format(cd['username'], nome)
                self.logger.warn(error_msg)
                raise ValidationError(_(error_msg))

        """
        'if' n??o ?? necess??rio por ser campo obrigat??rio e o framework j??
        mostrar a mensagem de obrigat??rio junto ao campo. mas foi colocado
        ainda assim para renderizar um message.danger no topo do form.
        """
        if 'tipo' not in cd or not cd['tipo']:
            self.logger.warn('Tipo do Autor n??o selecionado.')
            raise ValidationError(
                _('O Tipo do Autor deve ser selecionado.'))

        tipo = cd['tipo']
        if not tipo.content_type:
            if 'nome' not in cd or not cd['nome']:
                self.logger.warn('Nome do Autor n??o informado.')
                raise ValidationError(
                    _('O Nome do Autor deve ser informado.'))
            elif qs_autor.filter(nome=cd['nome']).exists():
                raise ValidationError("Autor '%s' j?? existente!" % cd['nome'])
        else:
            if 'autor_related' not in cd or not cd['autor_related']:
                self.logger.warn(
                    'Registro de %s n??o escolhido para ser '
                    'vinculado ao cadastro de Autor' % tipo.descricao
                )
                raise ValidationError(
                    _('Um registro de %s deve ser escolhido para ser '
                      'vinculado ao cadastro de Autor') % tipo.descricao)

            if not tipo.content_type.model_class().objects.filter(
                    pk=cd['autor_related']).exists():
                self.logger.warn(
                    'O Registro definido (%s-%s) n??o est?? na base '
                    'de %s.' % (cd['autor_related'], cd['q'], tipo.descricao)
                )
                raise ValidationError(
                    _('O Registro definido (%s-%s) n??o est?? na base de %s.'
                      ) % (cd['autor_related'], cd['q'], tipo.descricao))

            qs_autor_selected = qs_autor.filter(
                object_id=cd['autor_related'],
                content_type_id=cd['tipo'].content_type_id)
            if qs_autor_selected.exists():
                autor = qs_autor_selected.first()
                self.logger.warn(
                    'J?? existe um autor Cadastrado para '
                    '%s' % autor.autor_related
                )
                raise ValidationError(
                    _('J?? existe um autor Cadastrado para %s'
                      ) % autor.autor_related)

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):
        autor = super().save(commit)

        if not autor.tipo.content_type:
            autor.content_type = None
            autor.object_id = None
            autor.autor_related = None
        else:
            autor.autor_related = autor.tipo.content_type.model_class(
            ).objects.get(pk=self.cleaned_data['autor_related'])
            autor.nome = str(autor.autor_related)

        autor.save()

        return autor


class AutorFilterSet(django_filters.FilterSet):
    nome = django_filters.CharFilter(label=_('Nome do Autor'), lookup_expr='icontains')

    class Meta:
        model = Autor
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row0 = to_row([('nome', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Autor'),
                     row0,
                     form_actions(label='Pesquisar')))


class AutorFormForAdmin(AutorForm):
    status_user = forms.ChoiceField(
        label=_('Bloqueio do Usu??rio Existente'),
        choices=STATUS_USER_CHOICE,
        widget=forms.RadioSelect(),
        required=False,
        help_text=_('Se vc est?? trocando ou removendo o usu??rio deste Autor, '
                    'como o Sistema deve proceder com o usu??rio que est?? sendo'
                    ' desvinculado?'))

    class Meta:
        model = Autor
        fields = ['tipo',
                  'nome',
                  'cargo',
                  'autor_related',
                  'q',
                  ]


class RelatorioDocumentosAcessoriosFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioDocumentosAcessoriosFilterSet, self).qs
        return parent.distinct().order_by('-data')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAcessorio
        fields = ['tipo', 'materia__tipo', 'data']

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['materia__tipo'].label = 'Tipo de Mat??ria do Documento'
        self.filters['data'].label = 'Per??odo (Data Inicial - Data Final)'

        self.form.fields['tipo'].required = True

        row0 = to_row([('tipo', 6),
                       ('materia__tipo', 6)])

        row1 = to_row([('data', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                   <div class="form-check">
                                                       <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                       <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                   </div>
                                               ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa'),
                     row0, row1,
                     buttons)
        )


class RelatorioAtasFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio']

    @property
    def qs(self):
        parent = super(RelatorioAtasFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').exclude(
            upload_ata='').order_by('-data_inicio', 'tipo', 'numero')

    def __init__(self, *args, **kwargs):
        super(RelatorioAtasFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['data_inicio'].label = 'Per??odo de Abertura (Inicial - Final)'
        self.form.fields['data_inicio'].required = False

        row1 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Atas das Sess??es Plen??rias'),
                     row1, buttons, )
        )


def ultimo_ano_com_norma():
    anos_normas = choice_anos_com_normas()

    if anos_normas:
        return anos_normas[0]
    return ''


class RelatorioNormasMesFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    class Meta:
        model = NormaJuridica
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasMesFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True

        row1 = to_row([('ano', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por m??s do ano.'),
                     row1, buttons, )
        )

    @property
    def qs(self):
        parent = super(RelatorioNormasMesFilterSet, self).qs
        return parent.distinct().order_by('data')


class EstatisticasAcessoNormasForm(Form):

    ano = forms.ChoiceField(required=True,
                            label='Ano de acesso',
                            choices=RANGE_ANOS,
                            initial=timezone.now().year)

    class Meta:
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(EstatisticasAcessoNormasForm, self).__init__(
            *args, **kwargs)

        row1 = to_row([('ano', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.helper = SaplFormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Fieldset(_('Normas por acessos nos meses do ano.'),
                     row1, buttons)
        )

    def clean(self):
        super(EstatisticasAcessoNormasForm, self).clean()

        return self.cleaned_data


class RelatorioNormasVigenciaFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    vigencia = forms.ChoiceField(
        label=_('Vig??ncia'),
        choices=[(True, "Vigente"), (False, "N??o vigente")],
        widget=forms.RadioSelect(),
        required=True,
        initial=True)

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasVigenciaFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True
        self.form.fields['vigencia'] = self.vigencia

        row1 = to_row([('ano', 12)])
        row2 = to_row([('vigencia', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por vig??ncia.'),
                     row1, row2,
                     buttons, )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio',
                  'sessao_legislativa',
                  'tipo',
                  'legislatura']

    def __init__(self, *args, **kwargs):
        super(RelatorioPresencaSessaoFilterSet, self).__init__(
            *args, **kwargs)

        self.form.fields['exibir_ordem_dia'] = forms.BooleanField(required=False,
                                                                  label='Exibir presen??a das Ordens do Dia')
        self.form.initial['exibir_ordem_dia'] = True

        self.filters['data_inicio'].label = 'Per??odo (Inicial - Final)'

        self.form.fields['legislatura'].required = True

        tipo_sessao_ordinaria = self.filters['tipo'].queryset.filter(
            nome='Ordin??ria')
        if tipo_sessao_ordinaria:
            self.form.initial['tipo'] = tipo_sessao_ordinaria.first()

        row1 = to_row([('legislatura', 4),
                       ('sessao_legislativa', 4),
                       ('tipo', 4)])
        row2 = to_row([('exibir_ordem_dia', 12)])
        row3 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                    <div class="form-check">
                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                    </div>
                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Presen??a dos parlamentares nas sess??es plen??rias'),
                     row1, row2, row3, buttons, )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__status', 'tramitacao__data_tramitacao',
                  'tramitacao__unidade_tramitacao_local', 'tramitacao__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Mat??ria'
        self.filters['tramitacao__status'].label = _('Status')
        self.filters['tramitacao__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacao__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacao__data_tramitacao', 12)])
        row2 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacao__status', 6)])

        row4 = to_row([
            ('autoria__autor', 0),
            (Button('pesquisar',
                    'Pesquisar Autor',
                    css_class='btn btn-primary btn-sm'), 2),
            (Button('limpar',
                    'Limpar Autor',
                    css_class='btn btn-primary btn-sm'), 2)
        ])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2, row3, row4,
                     HTML(autor_label),
                     HTML(autor_modal),
                     buttons, )
        )


class RelatorioDataFimPrazoTramitacaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioDataFimPrazoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__unidade_tramitacao_local',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status', 'tramitacao__data_fim_prazo']

    def __init__(self, *args, **kwargs):
        super(RelatorioDataFimPrazoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Mat??ria'
        self.filters[
            'tramitacao__unidade_tramitacao_local'].label = 'Unidade Local (Origem)'
        self.filters['tramitacao__unidade_tramitacao_destino'].label = 'Unidade Destino'
        self.filters['tramitacao__status'].label = 'Status de tramita????o'

        row1 = to_row([('tramitacao__data_fim_prazo', 12)])
        row2 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacao__status', 6)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramita????es'),
                     row1, row2, row3,
                     buttons, )
        )


class RelatorioReuniaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioReuniaoFilterSet, self).qs
        return parent.distinct().order_by('-data', 'comissao')

    class Meta:
        model = Reuniao
        fields = ['comissao', 'data',
                  'nome', 'tema']

    def __init__(self, *args, **kwargs):
        super(RelatorioReuniaoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('comissao', 4),
             ('nome', 4),
             ('tema', 4)])

        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Reuni??o de Comiss??o'),
                     row1, row2,
                     buttons, )
        )


class RelatorioAudienciaFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioAudienciaFilterSet, self).qs
        return parent.distinct().order_by('-data', 'tipo')

    class Meta:
        model = AudienciaPublica
        fields = ['tipo', 'data',
                  'nome']

    def __init__(self, *args, **kwargs):
        super(RelatorioAudienciaFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('tipo', 4),
             ('nome', 4)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Audi??ncia P??blica'),
                     row1, row2,
                     buttons, )
        )


class RelatorioMateriasTramitacaoFilterSet(django_filters.FilterSet):

    materia__ano = django_filters.ChoiceFilter(required=True,
                                               label='Ano da Mat??ria',
                                               choices=choice_anos_com_materias)

    tramitacao__unidade_tramitacao_destino = django_filters.ModelChoiceFilter(
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade Atual'))

    tramitacao__status = django_filters.ModelChoiceFilter(
        queryset=StatusTramitacao.objects.all(),
        label=_('Status Atual'))

    materia__autores = django_filters.ModelChoiceFilter(
        label='Autor da Mat??ria',
        queryset=Autor.objects.all())


    @property
    def qs(self):
        parent = super(RelatorioMateriasTramitacaoFilterSet, self).qs
        return parent.distinct().order_by(
            '-materia__ano', 'materia__tipo', '-materia__numero'
        )

    class Meta:
        model = MateriaEmTramitacao
        fields = ['materia__ano', 'materia__tipo',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status','materia__autores']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['materia__tipo'].label = 'Tipo de Mat??ria'

        row1 = to_row([('materia__ano', 12)])
        row2 = to_row([('materia__tipo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_destino', 12)])
        row4 = to_row([('tramitacao__status', 12)])
        row5 = to_row([('materia__autores', 12)])

        buttons = FormActions(
            *[
                HTML('''
                            <div class="form-check">
                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                            </div>
                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Mat??ria em Tramita????o'),
                     row1, row2, row3, row4,row5,
                     buttons,)
        )


class RelatorioMateriasPorAnoAutorTipoFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Mat??ria',
                                      choices=choice_anos_com_materias)

    class Meta:
        model = MateriaLegislativa
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasPorAnoAutorTipoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row(
            [('ano', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                    <div class="form-check">
                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                    </div>
                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Mat??ria por Ano Autor Tipo'),
                     row1,
                     buttons, )
        )


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().order_by('-ano', '-numero', 'tipo', 'autoria__autor', '-autoria__primeiro_autor')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Mat??ria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data_apresentacao', 12)])
        row3 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Mat??ria por Autor'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     buttons, )
        )


class CasaLegislativaForm(FileFieldCheckMixin, ModelForm):

    class Meta:

        model = CasaLegislativa
        fields = ['codigo',
                  'nome',
                  'sigla',
                  'endereco',
                  'cep',
                  'municipio',
                  'uf',
                  'telefone',
                  'fax',
                  'logotipo',
                  'endereco_web',
                  'email',
                  'informacao_geral']

        widgets = {
            'uf': forms.Select(attrs={'class': 'selector'}),
            'cep': forms.TextInput(attrs={'class': 'cep'}),
            'telefone': forms.TextInput(attrs={'class': 'telefone'}),
            # O campo fax foi ocultado porque n??o ?? utilizado.
            'fax': forms.HiddenInput(),
            # 'fax': forms.TextInput(attrs={'class': 'telefone'}),
            'logotipo':  ImageThumbnailFileInput,
            'informacao_geral': forms.Textarea(
                attrs={'id': 'texto-rico'})
        }

    def clean_logotipo(self):
        # chama __clean de FileFieldCheckMixin
        # por estar em clean de campo
        super(CasaLegislativaForm, self)._check()

        logotipo = self.cleaned_data.get('logotipo')
        if logotipo:
            if logotipo.size > MAX_IMAGE_UPLOAD_SIZE:
                raise ValidationError("Imagem muito grande. ( > 2MB )")
        return logotipo


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username", max_length=30,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control', 'name': 'username'}))
    password = forms.CharField(
        label="Password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control', 'name': 'password'}))


class ConfiguracoesAppForm(ModelForm):
    logger = logging.getLogger(__name__)

    mostrar_brasao_painel = forms.BooleanField(
        help_text=_('Sugerimos fortemente que fa??a o upload de imagens com '
                    'o fundo transparente.'),
        label=_('Mostrar bras??o da Casa no painel?'),
        required=False)

    class Meta:
        model = AppConfig
        fields = ['documentos_administrativos',
                  'sequencia_numeracao_protocolo',
                  'sequencia_numeracao_proposicao',
                  'esfera_federacao',
                  # 'painel_aberto', # TODO: a ser implementado na vers??o 3.2
                  'texto_articulado_proposicao',
                  'texto_articulado_materia',
                  'texto_articulado_norma',
                  'proposicao_incorporacao_obrigatoria',
                  'protocolo_manual',
                  'mostrar_brasao_painel',
                  'receber_recibo_proposicao',
                  'assinatura_ata',
                  'estatisticas_acesso_normas',
                  'escolher_numero_materia_proposicao',
                  'tramitacao_materia',
                  'tramitacao_documento']


    def clean(self):
        cleaned_data = super().clean()

        if not self.is_valid():
            return cleaned_data

        mostrar_brasao_painel = self.cleaned_data.get(
            'mostrar_brasao_painel', False)
        casa = CasaLegislativa.objects.first()

        if not casa:
            self.logger.warn('N??o h?? casa legislativa relacionada.')
            raise ValidationError("N??o h?? casa legislativa relacionada.")

        if not casa.logotipo and mostrar_brasao_painel:
            self.logger.warn(
                'N??o h?? logitipo configurado para esta '
                'CasaLegislativa ({}).'.format(casa)
            )
            raise ValidationError("N??o h?? logitipo configurado para esta "
                                  "Casa legislativa.")

        return cleaned_data


class RecuperarSenhaForm(PasswordResetForm):

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        row1 = to_row(
            [('email', 12)])
        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Insira o e-mail cadastrado com a sua conta'),
                     row1,
                     form_actions(label='Enviar'))
        )

        super(RecuperarSenhaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(RecuperarSenhaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        email_existente = User.objects.filter(
            email=self.data['email']).exists()

        if not email_existente:
            msg = 'N??o existe nenhum usu??rio cadastrado com este e-mail.'
            self.logger.warn(
                'N??o existe nenhum usu??rio cadastrado com este e-mail ({}).'.format(self.data['email'])
            )
            raise ValidationError(msg)

        return self.cleaned_data


class NovaSenhaForm(SetPasswordForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(NovaSenhaForm, self).__init__(user, *args, **kwargs)

        row1 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1,
            form_actions(label='Enviar'))


class AlterarSenhaForm(Form):
    logger = logging.getLogger(__name__)

    username = forms.CharField(widget=forms.HiddenInput())

    old_password = forms.CharField(label='Senha atual',
                                   max_length=50,
                                   widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='Nova senha',
                                    max_length=50,
                                    widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='Confirmar senha',
                                    max_length=50,
                                    widget=forms.PasswordInput())

    class Meta:
        fields = ['username', 'old_password', 'new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):

        super(AlterarSenhaForm, self).__init__(*args, **kwargs)

        row1 = to_row([('old_password', 12)])
        row2 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1,
            row2,
            form_actions(label='Alterar Senha'))

    def clean(self):
        super(AlterarSenhaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        new_password1 = data['new_password1']
        new_password2 = data['new_password2']

        if new_password1 != new_password2:
            self.logger.warn("'Nova Senha' diferente de 'Confirmar Senha'")
            raise ValidationError(
                "'Nova Senha' diferente de 'Confirmar Senha'")

        # TODO: colocar mais regras como: tamanho m??nimo,
        # TODO: caracteres alfanum??ricos, mai??sculas (?),
        # TODO: senha atual igual a senha anterior, etc

        if len(new_password1) < 6:
            self.logger.warn(
                'A senha informada n??o tem o m??nimo de 6 caracteres.'
            )
            raise ValidationError(
                "A senha informada deve ter no m??nimo 6 caracteres")

        username = data['username']
        old_password = data['old_password']
        user = User.objects.get(username=username)

        if user.is_anonymous():
            self.logger.warn(
                'N??o ?? poss??vel alterar senha de usu??rio an??nimo ({}).'.format(username)
            )
            raise ValidationError(
                "N??o ?? poss??vel alterar senha de usu??rio an??nimo")

        if not user.check_password(old_password):
            self.logger.warn(
                'Senha atual informada n??o confere '
                'com a senha armazenada.'
            )
            raise ValidationError("Senha atual informada n??o confere "
                                  "com a senha armazenada")

        if user.check_password(new_password1):
            self.logger.warn(
                'Nova senha igual ?? senha anterior.'
            )
            raise ValidationError(
                "Nova senha n??o pode ser igual ?? senha anterior")

        return self.cleaned_data


class PartidoForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = Partido
        exclude = []

    def __init__(self, *args, **kwargs):

        super(PartidoForm, self).__init__(*args, **kwargs)

        # TODO Utilizar esses campos na issue #2161 de altera????o de nomes de partidos
        # if self.instance:
        #     if self.instance.nome:
        #         self.fields['nome'].widget.attrs['readonly'] = True
        #         self.fields['sigla'].widget.attrs['readonly'] = True

        row1 = to_row(
            [('sigla', 2),
             ('nome', 6),
             ('data_criacao', 2),
             ('data_extincao', 2), ])
        row2 = to_row([('observacao', 12)])
        row3 = to_row([('logo_partido', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1, row2, row3,
            form_actions(label='Salvar')
        )

    def clean(self):
        super(PartidoForm,self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_criacao'] and cleaned_data['data_extincao'] and cleaned_data['data_criacao'] > \
                cleaned_data['data_extincao']:
            raise ValidationError("Certifique-se de que a data de cria????o seja anterior ?? data de extin????o.")

        if self.instance.pk:
            partido = Partido.objects.get(pk=self.instance.pk)

            if xor(cleaned_data['sigla'] == partido.sigla, cleaned_data['nome'] == partido.nome):
                raise ValidationError(_('O Partido deve ter um novo nome e uma nova sigla.'))

            cleaned_data.update({'partido': partido})

        return cleaned_data

class PartidoUpdateForm(PartidoForm):

    opcoes = YES_NO_CHOICES

    historico = forms.ChoiceField(initial=False, choices=opcoes)


    class Meta:
        model = Partido
        exclude = []


    def __init__(self, pk=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('sigla', 6),
            ('nome', 6),
            ]
        )
        row2 = to_row([
            ('historico', 2),
            ('data_criacao', 5),
            ('data_extincao', 5),
            ]
        )
        row3 = to_row([('observacao', 12)])
        row4 = to_row([('logo_partido', 12)])

        buttons = FormActions(
           *[
               HTML('''<a href="/sistema/parlamentar/partido/{{object.id}}" class="btn btn-dark btn-close-container">%s</a>''' % _('Cancelar'))
           ],
            Submit('salvar', _('Salvar'), css_class='float-right',
               onclick='return true;'),
            css_class='form-group row justify-content-between'
        )

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1, row2, row3, row4, to_row([(buttons, 12)]),
        )




    def clean(self):
        cleaned_data = super(PartidoUpdateForm,self).clean()
        
        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_criacao'] and cleaned_data['data_extincao']:
            if cleaned_data['data_criacao'] > cleaned_data['data_extincao']:
                raise ValidationError(
                    "Certifique-se de que a data de cria????o seja anterior ?? data de extin????o.")

        return cleaned_data

    def save(self,commit=False):
        partido = self.instance
    
        cleaned_data = self.cleaned_data
        is_historico = cleaned_data['historico'] == 'True'
            
        if not is_historico:
            partido.save(commit)
        else:
            sigla = self.cleaned_data['sigla']
            nome = self.cleaned_data['nome']
            inicio_historico = self.cleaned_data['data_criacao']
            fim_historico = self.cleaned_data['data_extincao']
            logo_partido = self.cleaned_data['logo_partido']
            historico_partido = HistoricoPartido(sigla=sigla,
                                                nome=nome,
                                                inicio_historico=inicio_historico,
                                                fim_historico=fim_historico,
                                                logo_partido=logo_partido,
                                                partido=partido,
                                                )
            historico_partido.save()
        return partido

class RelatorioHistoricoTramitacaoAdmFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoAdmFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAdministrativo
        fields = ['tipo', 'tramitacaoadministrativo__status',
                  'tramitacaoadministrativo__data_tramitacao',
                  'tramitacaoadministrativo__unidade_tramitacao_local',
                  'tramitacaoadministrativo__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoAdmFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['tramitacaoadministrativo__status'].label = _('Status')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacaoadministrativo__data_tramitacao', 12)])
        row2 = to_row([('tramitacaoadministrativo__unidade_tramitacao_local', 6),
                       ('tramitacaoadministrativo__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacaoadministrativo__status', 6)])

        buttons = FormActions(
            *[
                HTML('''
                                                            <div class="form-check">
                                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                            </div>
                                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3,
                     buttons, )
        )


class RelatorioNormasPorAutorFilterSet(django_filters.FilterSet):

    autorianorma__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().filter(autorianorma__primeiro_autor=True)\
            .order_by('autorianorma__autor', '-autorianorma__primeiro_autor', 'tipo', '-ano', '-numero')

    class Meta(FilterOverridesMetaMixin):
        model = NormaJuridica
        fields = ['tipo', 'data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Norma'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data', 12)])
        row3 = to_row(
            [('autorianorma__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relat??rio PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     form_actions(label='Pesquisar'))
        )


class AutorUserForm(ModelForm):

    username = forms.CharField(label=get_user_model()._meta.get_field(
        get_user_model().USERNAME_FIELD).verbose_name.capitalize(),
        required=True,
        max_length=50)

    nome_autor = forms.CharField(
        label='Autor', 
        widget=widgets.TextInput(attrs={'readonly': 'readonly'})
    )
    
    class Meta:
        model = AutorUser
        exclude = ['user']
        widgets = {
            'autor': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row(
            [('nome_autor', 6),('username', 6),])
        row2 = to_row(
            [('autor', 6)]
        )

        actions = [HTML('<a href="{{ view.cancel_url }}"'
                        ' class="btn btn-dark">Cancelar</a>')]

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Vincular Usu??rio ao Autor'),
                     row1, row2,
                     HTML("&nbsp;"),
                     form_actions(more=actions)
                     )
        )

    def clean(self):
        cd = super().clean()
        
        if not self.is_valid():
            return cd

        username = cd['username']
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist as e:
            raise ValidationError("Este usu??rio n??o existe.")
        
        if AutorUser.objects.filter(user=user).exists():
            raise ValidationError("Este usu??rio ({}) j?? est?? vinculado a um Autor ({}).".format(
                username, AutorUser.objects.get(user=user).autor))

    
    def save(self):
        cd = self.cleaned_data
        user = User.objects.get(username=cd['username'])
        autor = cd['autor']
        autor_user = AutorUser.objects.create(autor=autor, user=user)

        # FIXME melhorar captura de grupo de Autor, levando em conta,
        # no m??nimo, a tradu????o.
        grupo = Group.objects.filter(name='Autor')[0]
        user.groups.add(grupo)

        return autor_user