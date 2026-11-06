
from django.contrib import admin
from django.contrib.auth.hashers import make_password, identify_hasher

from .models import (
    Usuario,
    Aluno,
    Professor,
    Disciplina,
    Matricula,
    Nota,
    Pagamento,
    Aviso,
    TipoDocumento,
    Documento,
    SolicitacaoDocumento,
    HistoricoSolicitacao,
)


# =====================================================
# USUÁRIOS
# =====================================================

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):

    list_display = ('nome', 'email', 'tipo', 'data_criacao')
    search_fields = ('nome', 'email')
    list_filter = ('tipo',)

    def save_model(self, request, obj, form, change):
        try:
            identify_hasher(obj.senha)
        except (ValueError, TypeError):
            obj.senha = make_password(obj.senha)

        super().save_model(request, obj, form, change)


# =====================================================
# TIPOS DE DOCUMENTOS
# =====================================================

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):

    list_display = ('nome', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)


# =====================================================
# DOCUMENTOS DOS ALUNOS
# =====================================================

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'aluno',
        'tipo_documento',
        'arquivo',
        'data_upload',
    )

    search_fields = (
        'nome',
        'aluno__usuario__nome',
        'aluno__matricula',
    )

    list_filter = (
        'tipo_documento',
        'data_upload',
    )


# =====================================================
# SOLICITAÇÕES DE DOCUMENTOS
# =====================================================

@admin.register(SolicitacaoDocumento)
class SolicitacaoDocumentoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'aluno',
        'tipo_documento',
        'status',
        'responsavel',
        'data_solicitacao',
        'data_atualizacao',
    )

    search_fields = (
        'aluno__usuario__nome',
        'aluno__matricula',
        'tipo_documento__nome',
    )

    list_filter = (
        'status',
        'tipo_documento',
        'data_solicitacao',
    )

    readonly_fields = (
        'data_solicitacao',
        'data_atualizacao',
    )

    fieldsets = (
        ('Dados da solicitação', {
            'fields': (
                'aluno',
                'tipo_documento',
                'status',
                'observacao_aluno',
            )
        }),

        ('Atendimento da secretaria', {
            'fields': (
                'observacao_secretaria',
                'responsavel',
                'documento',
            )
        }),

        ('Datas', {
            'fields': (
                'data_solicitacao',
                'data_atualizacao',
            )
        }),
    )

    class Media:
        css = {
            'all': ('core/css/admin.css',)
        }

    def save_model(self, request, obj, form, change):

        status_anterior = None

        # Recupera o status anterior antes de salvar.
        if change and obj.pk:
            status_anterior = (
                SolicitacaoDocumento.objects
                .filter(pk=obj.pk)
                .values_list('status', flat=True)
                .first()
            )

        # Identifica o responsável pelo atendimento.
        responsavel = obj.responsavel

        if responsavel is None and request.user.email:
            responsavel = Usuario.objects.filter(
                email__iexact=request.user.email
            ).first()

            if responsavel:
                obj.responsavel = responsavel

        # Salva a solicitação.
        super().save_model(request, obj, form, change)

        # Registra a mudança de status no histórico.
        if (
            status_anterior is not None
            and status_anterior != obj.status
        ):
            comentario = (
                obj.observacao_secretaria.strip()
                or 'Status alterado pela secretaria.'
            )

            HistoricoSolicitacao.objects.create(
                solicitacao=obj,
                status_anterior=status_anterior,
                status_novo=obj.status,
                comentario=comentario,
                responsavel=responsavel,
            )


# =====================================================
# HISTÓRICO DAS SOLICITAÇÕES
# =====================================================

@admin.register(HistoricoSolicitacao)
class HistoricoSolicitacaoAdmin(admin.ModelAdmin):

    list_display = (
        'solicitacao',
        'status_anterior',
        'status_novo',
        'responsavel',
        'data_alteracao',
    )

    search_fields = (
        'solicitacao__aluno__usuario__nome',
        'comentario',
    )

    list_filter = (
        'status_novo',
        'data_alteracao',
    )

    readonly_fields = (
        'solicitacao',
        'status_anterior',
        'status_novo',
        'comentario',
        'responsavel',
        'data_alteracao',
    )


# =====================================================
# DEMAIS MODELOS
# =====================================================

admin.site.register(Aluno)
admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Matricula)
admin.site.register(Nota)
admin.site.register(Pagamento)
admin.site.register(Aviso)
