import django_filters

from crispy_forms.layout import Button, Fieldset, HTML, Layout
from datetime import datetime

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm, widgets
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import (form_actions, to_row, 
                                      SaplFormHelper, SaplFormLayout)
from sapl.materia.forms import MateriaLegislativaFilterSet
from sapl.materia.models import (MateriaLegislativa, StatusTramitacao,
                                 TipoMateriaLegislativa)
from sapl.painel.models import Cronometro
from sapl.parlamentares.models import Parlamentar, Mandato
from sapl.utils import (RANGE_DIAS_MES, RANGE_MESES,
                        MateriaPesquisaOrderingFilter, autor_label,
                        autor_modal, timezone, choice_anos_com_sessaoplenaria,
                        FileFieldCheckMixin, verifica_afastamento_parlamentar)
from sapl.parlamentares.models import Mandato, Parlamentar
from sapl.utils import (autor_label, autor_modal,
                        choice_anos_com_sessaoplenaria,
                        FileFieldCheckMixin,
                        MateriaPesquisaOrderingFilter,
                        RANGE_DIAS_MES, RANGE_MESES,
                        timezone, validar_arquivo)
from .models import (ExpedienteMateria,
                     JustificativaAusencia, OcorrenciaSessao, Orador,
                     OradorExpediente, OradorOrdemDia, OrdemDia,
                     ORDENACAO_RESUMO, PresencaOrdemDia,
                     RegistroLeitura, ResumoOrdenacao, RetiradaPauta,
                     SessaoPlenaria, SessaoPlenariaPresenca,
                     TipoResultadoVotacao, TipoRetiradaPauta,
                     CronometroLista)

MES_CHOICES = RANGE_MESES
DIA_CHOICES = RANGE_DIAS_MES


class SessaoPlenariaForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = SessaoPlenaria
        exclude = ['cod_andamento_sessao']

    def clean(self):
        super(SessaoPlenariaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        instance = self.instance

        num = self.cleaned_data['numero']
        sl = self.cleaned_data['sessao_legislativa']
        leg = self.cleaned_data['legislatura']
        tipo = self.cleaned_data['tipo']
        abertura = self.cleaned_data['data_inicio']
        encerramento = self.cleaned_data['data_fim']

        error = ValidationError(
            "N??mero de Sess??o Plen??ria j?? existente "
            "para a Legislatura, Sess??o Legislativa e Tipo informados. "
            "Favor escolher um n??mero distinto.")

        qs = tipo.queryset_tipo_numeracao(leg, sl, abertura)
        qs &= Q(numero=num)

        if SessaoPlenaria.objects.filter(qs).exclude(pk=instance.pk).exists():
            raise error

        # Condi????es da verifica????o
        abertura_entre_leg = leg.data_inicio <= abertura <= leg.data_fim
        abertura_entre_sl = sl.data_inicio <= abertura <= sl.data_fim
        if encerramento is not None:
            # Verifica se a data de encerramento ?? anterior a data de abertura
            if encerramento < abertura:
                raise ValidationError("A data de encerramento n??o pode ser "
                                      "anterior a data de abertura.")
            encerramento_entre_leg = leg.data_inicio <= encerramento <= leg.data_fim
            encerramento_entre_sl = sl.data_inicio <= encerramento <= sl.data_fim
        else:
            encerramento_entre_leg = True
            encerramento_entre_sl = True


        ## Sess??es Extraordin??rias podem estar fora da sess??o legislativa
        descricao_tipo = tipo.nome.lower()
        if "extraordin??ria" in descricao_tipo or "especial" in descricao_tipo:
            # Ignora checagem de limites para Sess??o Legislativa
            abertura_entre_sl = True
            encerramento_entre_sl = True

        if not (abertura_entre_leg and encerramento_entre_leg):
            raise ValidationError("A data de abertura e encerramento da Sess??o "
                                  "Plen??ria deve estar compreendida entre a "
                                  "data de abertura e encerramento da Legislatura")

        if not (abertura_entre_sl and encerramento_entre_sl):
            raise ValidationError("A data de abertura e encerramento da Sess??o "
                                  "Plen??ria deve estar compreendida entre a "
                                  "data de abertura e encerramento da Sess??o Legislativa")
        

        upload_pauta = self.cleaned_data.get('upload_pauta', False)
        upload_ata = self.cleaned_data.get('upload_ata', False)
        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_pauta:
            validar_arquivo(upload_pauta, "Pauta da Sess??o")
        
        if upload_ata:
            validar_arquivo(upload_ata, "Ata da Sess??o")

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo da Sess??o")

        return self.cleaned_data


class RetiradaPautaForm(ModelForm):

    tipo_de_retirada = forms.ModelChoiceField(required=True,
                                              empty_label='------------',
                                              queryset=TipoRetiradaPauta.objects.all())
    expediente = forms.ModelChoiceField(required=False,
                                        label='Mat??ria do Expediente',
                                        queryset=ExpedienteMateria.objects.all())
    ordem = forms.ModelChoiceField(required=False,
                                   label='Mat??ria da Ordem do Dia',
                                   queryset=OrdemDia.objects.all())
    materia = forms.ModelChoiceField(required=False,
                                     widget=forms.HiddenInput(),
                                     queryset=MateriaLegislativa.objects.all())

    class Meta:
        model = RetiradaPauta
        fields = ['ordem',
                  'expediente',
                  'parlamentar',
                  'tipo_de_retirada',
                  'data',
                  'observacao',
                  'materia']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('tipo_de_retirada', 5),
                       ('parlamentar', 4),
                       ('data', 3)])
        row2 = to_row([('ordem', 6),
                       ('expediente', 6)])
        row3 = to_row([('observacao', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Retirada de Pauta'),
                     row1, row2, row3))

        q = Q(sessao_plenaria=kwargs['initial']['sessao_plenaria'])
        ordens = OrdemDia.objects.filter(q)
        expedientes = ExpedienteMateria.objects.filter(q)
        retiradas_ordem = [
            r.ordem for r in RetiradaPauta.objects.filter(q, ordem__in=ordens)]
        retiradas_expediente = [r.expediente for r in RetiradaPauta.objects.filter(
            q, expediente__in=expedientes)]
        setOrdem = set(ordens) - set(retiradas_ordem)
        setExpediente = set(expedientes) - set(retiradas_expediente)

        super(RetiradaPautaForm, self).__init__(
            *args, **kwargs)

        if self.instance.pk:
            setOrdem = set(ordens)
            setExpediente = set(expedientes)

        presencas = SessaoPlenariaPresenca.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')
        presentes = [p.parlamentar for p in presencas]

        self.fields['expediente'].choices = [
            (None, "------------")] + [(e.id, e.materia) for e in setExpediente]
        self.fields['ordem'].choices = [
            (None, "------------")] + [(o.id, o.materia) for o in setOrdem]
        self.fields['parlamentar'].choices = [
            (None, "------------")] + [(p.id, p) for p in presentes]

    def clean(self):

        super(RetiradaPautaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        sessao_plenaria = self.instance.sessao_plenaria
        if self.cleaned_data['data'] < sessao_plenaria.data_inicio:
            raise ValidationError(
                _("Data de retirada de pauta anterior ?? abertura da Sess??o."))
        if sessao_plenaria.data_fim and self.cleaned_data['data'] > sessao_plenaria.data_fim:
            raise ValidationError(
                _("Data de retirada de pauta posterior ao encerramento da Sess??o."))

        if self.cleaned_data['ordem'] and self.cleaned_data['ordem'].registrovotacao_set.exists():
            raise ValidationError(
                _("Essa mat??ria j?? foi votada, portanto n??o pode ser retirada de pauta."))
        elif self.cleaned_data['expediente'] and self.cleaned_data['expediente'].registrovotacao_set.exists():
            raise ValidationError(
                _("Essa mat??ria j?? foi votada, portanto n??o pode ser retirada de pauta."))

        return self.cleaned_data

    def save(self, commit=False):
        retirada = super(RetiradaPautaForm, self).save(commit=commit)
        if retirada.ordem:
            ordem = retirada.ordem
            retirada.materia = ordem.materia
            ordem.votacao_aberta = False
            ordem.save()
        elif retirada.expediente:
            expediente = retirada.expediente
            retirada.materia = expediente.materia
            expediente.votacao_aberta = False
            expediente.save()
        retirada.save()
        return retirada


class ExpedienteMateriaForm(ModelForm):

    _model = ExpedienteMateria
    data_atual = timezone.now()

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Mat??ria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
        widget=forms.Select(attrs={'autocomplete': 'off'}))

    numero_materia = forms.CharField(
        label='N??mero Mat??ria', required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    ano_materia = forms.CharField(
        label='Ano Mat??ria',
        initial=int(data_atual.year),
        required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    data_ordem = forms.CharField(
        label='Data Sess??o',
        initial=datetime.strftime(timezone.now(), '%d/%m/%Y'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    apenas_leitura = forms.BooleanField(label='Apenas Leitura', required=False)

    class Meta:
        model = ExpedienteMateria
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = ExpedienteMateria.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse n??mero de ordem j?? existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean(self):
        cleaned_data = super(ExpedienteMateriaForm, self).clean()
        if not self.is_valid():
            return cleaned_data

        sessao = self.instance.sessao_plenaria

        try:
            materia = MateriaLegislativa.objects.get(
                numero=self.cleaned_data['numero_materia'],
                ano=self.cleaned_data['ano_materia'],
                tipo=self.cleaned_data['tipo_materia'])
        except ObjectDoesNotExist:
            msg = _('A mat??ria a ser inclusa n??o existe no cadastro'
                    ' de mat??rias legislativas.')
            raise ValidationError(msg)
        else:
            cleaned_data['materia'] = materia

        exists = self._model.objects.filter(
            sessao_plenaria=sessao,
            materia=materia).exists()

        if exists and not self.instance.pk:
            msg = _('Essa mat??ria j?? foi cadastrada.')
            raise ValidationError(msg)

        return cleaned_data

    def save(self, commit=False):
        expediente = super(ExpedienteMateriaForm, self).save(commit)
        expediente.materia = self.cleaned_data['materia']
        expediente.save()
        return expediente


class OrdemDiaForm(ExpedienteMateriaForm):

    _model = OrdemDia

    class Meta:
        model = OrdemDia
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = OrdemDia.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse n??mero de ordem j?? existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean(self):
        cleaned_data = super(OrdemDiaForm, self).clean()
        if not self.is_valid():
            return cleaned_data
        return self.cleaned_data

    def save(self, commit=False):
        ordem = super(OrdemDiaForm, self).save(commit)
        ordem.materia = self.cleaned_data['materia']
        ordem.save()
        return ordem


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class OcorrenciaSessaoForm(ModelForm):
    class Meta:
        model = OcorrenciaSessao
        fields = ['conteudo']


class VotacaoForm(forms.Form):
    votos_sim = forms.IntegerField(label='Sim')
    votos_nao = forms.IntegerField(label='N??o')
    abstencoes = forms.IntegerField(label='Absten????es')
    total_presentes = forms.IntegerField(
        required=False, widget=forms.HiddenInput())
    total_votantes = forms.IntegerField(
        required=False, widget=forms.HiddenInput()
    )
    voto_presidente = forms.IntegerField(
        label='A totaliza????o inclui o voto do Presidente?')
    total_votos = forms.IntegerField(required=False, label='total')
    observacao = forms.CharField(required=False, label='Observa????o')
    resultado_votacao = forms.CharField(label='Resultado da Vota????o')

    def clean(self):
        cleaned_data = super().clean()
        if not self.is_valid():
            return cleaned_data

        votos_sim = cleaned_data['votos_sim']
        votos_nao = cleaned_data['votos_nao']
        abstencoes = cleaned_data['abstencoes']
        qtde_presentes = cleaned_data['total_presentes']
        qtde_votantes = cleaned_data['total_votantes']
        qtde_votos = votos_sim + votos_nao + abstencoes
        voto_presidente = cleaned_data['voto_presidente']

        if qtde_votantes and not voto_presidente:
            qtde_votantes -= 1

        if qtde_votantes and qtde_votos != qtde_votantes:
            raise ValidationError(
                'O total de votos n??o corresponde com a quantidade de votantes!')

        return cleaned_data

    # def save(self, commit=False):
    #     #TODO Verificar se esse c??dido ?? utilizado

    #     votacao = super(VotacaoForm, self).save(commit)
    #     votacao.materia = self.cleaned_data['materia']
    #     votacao.save()
    #     return votacao


class VotacaoNominalForm(forms.Form):
    resultado_votacao = forms.ModelChoiceField(label='Resultado da Vota????o',
                                               required=False,
                                               queryset=TipoResultadoVotacao.objects.all())


class VotacaoEditForm(forms.Form):
    pass


class SessaoPlenariaFilterSet(django_filters.FilterSet):

    data_inicio__year = django_filters.ChoiceFilter(
        required=False,
        label='Ano',
        choices=choice_anos_com_sessaoplenaria
    )
    data_inicio__month = django_filters.ChoiceFilter(required=False,
                                                     label='M??s',
                                                     choices=MES_CHOICES)
    data_inicio__day = django_filters.ChoiceFilter(required=False,
                                                   label='Dia',
                                                   choices=DIA_CHOICES)
    titulo = _('Pesquisa de Sess??o Plen??ria')

    class Meta:
        model = SessaoPlenaria
        fields = ['tipo']

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaFilterSet, self).__init__(*args, **kwargs)

        # pr??-popula o campo do formul??rio com o ano corrente
        self.form.fields['data_inicio__year'].initial = timezone.now().year

        row1 = to_row(
            [('data_inicio__year', 3),
             ('data_inicio__month', 3),
             ('data_inicio__day', 3),
             ('tipo', 3)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(self.titulo,
                     row1,
                     form_actions(label='Pesquisar'))
        )


class AdicionarVariasMateriasFilterSet(MateriaLegislativaFilterSet):

    o = MateriaPesquisaOrderingFilter()
    tramitacao__status = django_filters.ModelChoiceFilter(
        required=False,
        queryset=StatusTramitacao.objects.all(),
        label=_('Status da Mat??ria'))

    class Meta:
        model = MateriaLegislativa
        fields = ['tramitacao__status',
                  'numero',
                  'numero_protocolo',
                  'ano',
                  'tipo',
                  'data_apresentacao',
                  'data_publicacao',
                  'autoria__autor__tipo',
                  # FIXME 'autoria__autor__partido',
                  'relatoria__parlamentar_id',
                  'local_origem_externa',
                  'em_tramitacao',
                  ]

    def __init__(self, *args, **kwargs):
        # Colocar super().__init__(*args, **kwargs) quebra a tela
        # de adicionar v??rias mat??rias em expediente e ordem dia.
        # pois herda da classe AdicionarVariasMateriasFilterSet em
        # vez de MateriaLegislativaFilterSet
        super(MateriaLegislativaFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Mat??ria'
        self.filters['autoria__autor__tipo'].label = 'Tipo de Autor'
        # self.filters['autoria__autor__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = to_row(
            [('tramitacao__status', 12)])
        row2 = to_row(
            [('tipo', 12)])
        row3 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row4 = to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row5 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row6 = to_row(
            [('autoria__autor__tipo', 6),
             # ('autoria__autor__partido', 6)
             ])
        row7 = to_row(
            [('relatoria__parlamentar_id', 6),
             ('local_origem_externa', 6)])
        row8 = to_row(
            [('em_tramitacao', 6),
             ('o', 6)])
        row9 = to_row(
            [('ementa', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Mat??ria'),
                     row1, row2, row3,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4, row5, row6, row7, row8, row9,
                     form_actions(label='Pesquisar'))
        )


class OradorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sessao = SessaoPlenaria.objects.get(id=kwargs['initial']['id_sessao'])
        parlamentares_ativos = Parlamentar.objects.filter(ativo=True).order_by('nome_parlamentar')
        for p in parlamentares_ativos:
            if verifica_afastamento_parlamentar(p, sessao.data_inicio, sessao.data_fim):
                parlamentares_ativos = parlamentares_ativos.exclude(id=p.id)
        
        self.fields['parlamentar'].queryset = parlamentares_ativos
             

    def clean(self):
        super(OradorForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero')
        numero_ordem = cleaned_data['numero_ordem']
        ordem = Orador.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=numero_ordem
        ).exists()

        if ordem and numero_ordem != numero:
            raise ValidationError(_(
                "J?? existe orador nesta posi????o de ordem de pronunciamento"
            ))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = Orador
        exclude = ['sessao_plenaria']


class OradorExpedienteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        id_sessao = int(self.initial['id_sessao'])
        sessao = SessaoPlenaria.objects.get(id=id_sessao)
        legislatura_vigente = sessao.legislatura
        
        parlamentares_ativos = Parlamentar.objects.filter(ativo=True).order_by('nome_parlamentar')
        for p in parlamentares_ativos:
            if verifica_afastamento_parlamentar(p, sessao.data_inicio, sessao.data_fim):
                parlamentares_ativos = parlamentares_ativos.exclude(id=p.id)
        
        self.fields['parlamentar'].queryset = parlamentares_ativos

    def clean(self):
        super(OradorExpedienteForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero', None)
        ordem = OradorExpediente.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=cleaned_data['numero_ordem']
        ).exists()

        if ordem and (cleaned_data['numero_ordem'] != numero):
            raise ValidationError(_(
                'J?? existe orador nesta posi????o da ordem de pronunciamento'))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = OradorExpediente
        exclude = ['sessao_plenaria']


class OradorOrdemDiaForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        id_sessao = int(self.initial['id_sessao'])
        sessao = SessaoPlenaria.objects.get(id=id_sessao)
        legislatura_vigente = sessao.legislatura
        self.fields['parlamentar'].queryset = \
            Parlamentar.objects.filter(mandato__legislatura=legislatura_vigente,
                                       ativo=True).order_by('nome_parlamentar')

    def clean(self):
        super(OradorOrdemDiaForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero')
        numero_ordem = cleaned_data['numero_ordem']
        ordem = OradorOrdemDia.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=numero_ordem
        ).exists()

        if ordem and numero_ordem != numero:
            raise ValidationError(_(
                "J?? existe orador nesta posi????o de ordem de pronunciamento"
            ))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = OradorOrdemDia
        exclude = ['sessao_plenaria']


class PautaSessaoFilterSet(SessaoPlenariaFilterSet):
    titulo = _('Pesquisa de Pauta de Sess??o')


class JustificativaAusenciaForm(ModelForm):

    class Meta:
        model = JustificativaAusencia
        fields = ['parlamentar',
                  'hora',
                  'data',
                  'upload_anexo',
                  'tipo_ausencia',
                  'ausencia',
                  'materias_do_expediente',
                  'materias_da_ordem_do_dia',
                  'observacao'
                  ]

        widgets = {
            'materias_do_expediente': CheckboxSelectMultiple(),
            'materias_da_ordem_do_dia': CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('parlamentar', 12)])
        row2 = to_row(
            [('data', 6),
             ('hora', 6)])
        row3 = to_row(
            [('upload_anexo', 6)])
        row4 = to_row(
            [('tipo_ausencia', 12)])
        row5 = to_row(
            [('ausencia', 12)])
        row6 = to_row(
            [('materias_do_expediente', 12)])
        row7 = to_row(
            [('materias_da_ordem_do_dia', 12)])
        row8 = to_row(
            [('observacao', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Justificativa de Aus??ncia'),
                     row1, row2, row3,
                     row4, row5,
                     row6,
                     row7,
                     row8)
        )
        q = Q(sessao_plenaria=kwargs['initial']['sessao_plenaria'])
        ordens = OrdemDia.objects.filter(q)
        expedientes = ExpedienteMateria.objects.filter(q)
        legislatura = kwargs['initial']['sessao_plenaria'].legislatura
        mandato = Mandato.objects.filter(
            legislatura=legislatura).order_by('parlamentar__nome_parlamentar')
        parlamentares = [m.parlamentar for m in mandato]

        super(JustificativaAusenciaForm, self).__init__(
            *args, **kwargs)

        presencas = SessaoPlenariaPresenca.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')
        presencas_ordem = PresencaOrdemDia.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')

        presentes = [p.parlamentar for p in presencas]
        presentes_ordem = [p.parlamentar for p in presencas_ordem]

        presentes_ambos = set(presentes).intersection(set(presentes_ordem))
        setFinal = set(parlamentares) - presentes_ambos

        self.fields['materias_do_expediente'].choices = [
            (e.id, e.materia) for e in expedientes]

        self.fields['materias_da_ordem_do_dia'].choices = [
            (o.id, o.materia) for o in ordens]

        self.fields['parlamentar'].choices = [
            ("0", "------------")] + [(p.id, p) for p in setFinal]

    def clean(self):
        super(JustificativaAusenciaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        sessao_plenaria = self.instance.sessao_plenaria

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo de Justificativa")

        if not sessao_plenaria.finalizada or sessao_plenaria.finalizada is None:
            raise ValidationError(
                "A sess??o deve estar finalizada para registrar uma Aus??ncia")
        else:
            return self.cleaned_data

    def save(self):

        justificativa = super().save(True)

        if justificativa.ausencia == 2:
            justificativa.materias_do_expediente.clear()
            justificativa.materias_da_ordem_do_dia.clear()
        return justificativa


class OrdemExpedienteLeituraForm(forms.ModelForm):

    observacao = forms.CharField(required=False, label='Observa????o', widget=forms.Textarea,)

    class Meta:
        model = RegistroLeitura
        fields = ['materia',
                  'ordem',
                  'expediente',
                  'observacao',
                  'user', 
                  'ip']
        widgets = {'materia': forms.HiddenInput(),
                   'ordem': forms.HiddenInput(),
                   'expediente': forms.HiddenInput(),
                   'user': forms.HiddenInput(),
                   'ip': forms.HiddenInput()
                   }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        instance = self.initial['instance']
        if instance:
            self.instance = instance.first()
            self.fields['observacao'].initial = self.instance.observacao

        row1 = to_row(
            [('observacao', 12)])   

        actions = [HTML('<a href="{{ view.cancel_url }}"'
                        ' class="btn btn-warning">Cancelar Leitura</a>')]

        self.helper = SaplFormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Fieldset(_('Leitura de Mat??ria'),
                    HTML('''
                        <b>Mat??ria:</b> {{materia}}<br>
                        <b>Ementa:</b> {{materia.ementa}} <br>
                    '''),
                     row1,
                     form_actions(more=actions),
                    )
        )
        

class CronometroListaForm(ModelForm):

    cronometro = forms.ModelChoiceField(
        queryset=Cronometro.objects.all(), 
        label="Cron??metro"
    )

    nome_lista = forms.CharField(
        label='Lista de Discuss??o', 
        widget=widgets.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = CronometroLista
        exclude = []
        widgets = {
            'tipo_lista': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row(
            [('nome_lista', 6),('cronometro', 6),])
        row2 = to_row(
            [('tipo_lista', 6)]
        )

        actions = [HTML('<a href="{{ view.cancel_url }}"'
                        ' class="btn btn-dark">Cancelar</a>')]

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Vincular Cron??metro ?? Lista de Discuss??o'),
                     row1, row2,
                     HTML("&nbsp;"),
                     form_actions(more=actions)
                     )
        )

    def save(self):
        cd = self.cleaned_data
        cronometro = cd['cronometro']
        tipo_lista = cd['tipo_lista']
        cronometro_lista = CronometroLista.objects.create(cronometro=cronometro, tipo_lista=tipo_lista)

        return cronometro_lista 
