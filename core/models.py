
from django.db import models
from django.db.models import Q


# =====================================================
# 1. USUÁRIOS
# =====================================================

class Usuario(models.Model):

    TIPO_CHOICES = [
        ('aluno', 'Aluno'),
        ('professor', 'Professor'),
        ('admin', 'Administrador'),
    ]

    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


# =====================================================
# 2. CURSOS
# =====================================================

class Curso(models.Model):

    nome = models.CharField(max_length=150, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


# =====================================================
# 3. ALUNOS
# =====================================================

class Aluno(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='aluno'
    )

    matricula = models.CharField(
        max_length=50,
        unique=True
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='alunos'
    )

    periodo = models.PositiveSmallIntegerField(default=1)

    foto_perfil = models.CharField(
        max_length=500,
        blank=True
    )

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(periodo__gte=1),
                name='periodo_aluno_maior_que_zero'
            )
        ]

    def __str__(self):
        return self.usuario.nome


# =====================================================
# 4. PROFESSORES
# =====================================================

class Professor(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='professor'
    )

    titulacao = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)

    foto_perfil = models.CharField(
        max_length=500,
        blank=True
    )

    def __str__(self):
        return self.usuario.nome


# =====================================================
# 5. DISCIPLINAS
# =====================================================

class Disciplina(models.Model):

    nome = models.CharField(max_length=150)

    codigo = models.CharField(
        max_length=50,
        unique=True
    )

    descricao = models.TextField(blank=True)

    professor = models.ForeignKey(
        Professor,
        on_delete=models.PROTECT,
        related_name='disciplinas'
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='disciplinas'
    )

    def __str__(self):
        return self.nome


# =====================================================
# 6. MATRÍCULAS EM DISCIPLINAS
# =====================================================

class Matricula(models.Model):

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='matriculas'
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.PROTECT,
        related_name='matriculas'
    )

    ano = models.PositiveSmallIntegerField()

    semestre = models.PositiveSmallIntegerField(
        choices=[
            (1, 'Primeiro semestre'),
            (2, 'Segundo semestre'),
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['aluno', 'disciplina', 'ano', 'semestre'],
                name='unica_matricula_disciplina_periodo'
            ),
        ]

    def __str__(self):
        return f'{self.aluno} - {self.disciplina}'


# =====================================================
# 7. NOTAS
# =====================================================

class Nota(models.Model):

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name='notas'
    )

    avaliacao = models.CharField(max_length=100)

    valor = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    data = models.DateField()

    def __str__(self):
        return f'{self.matricula} - {self.avaliacao}'


# =====================================================
# 8. AVISOS
# =====================================================

class Aviso(models.Model):

    PUBLICO_CHOICES = [
        ('aluno', 'Alunos'),
        ('professor', 'Professores'),
        ('todos', 'Todos'),
    ]

    titulo = models.CharField(max_length=255)
    conteudo = models.TextField()
    data_publicacao = models.DateField()

    publico_alvo = models.CharField(
        max_length=20,
        choices=PUBLICO_CHOICES,
        default='todos'
    )

    def __str__(self):
        return self.titulo


# =====================================================
# 9. TIPOS DE DOCUMENTOS
# =====================================================

class TipoDocumento(models.Model):

    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# =====================================================
# 10. DOCUMENTOS DISPONIBILIZADOS
# =====================================================

class Documento(models.Model):

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='documentos'
    )

    nome = models.CharField(max_length=255)

    tipo_documento = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name='documentos'
    )

    # Campo antigo mantido para preservar endereços já cadastrados.
    arquivo_url = models.CharField(
        max_length=500,
        blank=True
    )

    # Novo campo para upload de arquivos pela secretaria.
    arquivo = models.FileField(
        upload_to='documentos/%Y/%m/',
        blank=True,
        null=True
    )

    data_upload = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nome


# =====================================================
# 11. SOLICITAÇÕES DE DOCUMENTOS
# =====================================================

class SolicitacaoDocumento(models.Model):

    STATUS_CHOICES = [
        ('solicitada', 'Solicitada'),
        ('em_analise', 'Em análise'),
        ('em_atendimento', 'Em atendimento'),
        ('concluida', 'Concluída'),
        ('indeferida', 'Indeferida'),
        ('cancelada', 'Cancelada'),
    ]

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.PROTECT,
        related_name='solicitacoes'
    )

    tipo_documento = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name='solicitacoes'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='solicitada'
    )

    observacao_aluno = models.TextField(blank=True)
    observacao_secretaria = models.TextField(blank=True)

    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_atendidas'
    )

    documento = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes'
    )

    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.aluno} - {self.tipo_documento}'


# =====================================================
# 12. HISTÓRICO DAS SOLICITAÇÕES
# =====================================================

class HistoricoSolicitacao(models.Model):

    solicitacao = models.ForeignKey(
        SolicitacaoDocumento,
        on_delete=models.CASCADE,
        related_name='historico'
    )

    status_anterior = models.CharField(
        max_length=20,
        blank=True
    )

    status_novo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True)

    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    data_alteracao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.solicitacao} - {self.status_novo}'


# =====================================================
# 13. PAGAMENTOS
# Mantido temporariamente por compatibilidade.
# Fora do escopo atual.
# =====================================================

class Pagamento(models.Model):

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='pagamentos'
    )

    descricao = models.CharField(max_length=255)

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    data = models.DateField()
    status = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.descricao} - {self.status}'
