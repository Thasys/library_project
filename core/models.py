from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class Usuario(AbstractUser):
    cpf = models.CharField('CPF', max_length=11, unique=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    token_verificacao = models.CharField(max_length=64, blank=True, null=True)
    token_adm = models.CharField(max_length=64, blank=True, null=True)
    bloqueio_ate = models.DateTimeField('Bloqueio até', null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name="grupos",
        blank=True,
        help_text='Grupos de permissões deste usuário.',
        related_name='core_usuario_set',
        related_query_name='usuario',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='permissões de usuário',
        blank=True,
        help_text='Permissões específicas deste usuário.',
        related_name='core_usuario_perm_set',
        related_query_name='usuario_perm',
    )

    class Meta:
        db_table = 'usuarios'


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self',
                               on_delete=models.RESTRICT,
                               related_name='subcategories',
                               blank=True, null=True)
    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nome


class LivroBase(models.Model):
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    sinopse = models.TextField(blank=True, null=True)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    capa_url = models.CharField(max_length=255, blank=True, null=True)
    categorias = models.ManyToManyField(Categoria, through='LivroCategoria')

    class Meta:
        db_table = 'livros_base'

    def __str__(self):
        return self.titulo


class LivroCategoria(models.Model):
    livro = models.ForeignKey(LivroBase, on_delete=models.RESTRICT)
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT)

    class Meta:
        db_table = 'livro_categoria'
        unique_together = ('livro', 'categoria')


class Exemplar(models.Model):
    livro = models.ForeignKey(LivroBase, on_delete=models.RESTRICT, related_name='exemplares')
    codigo_exemplar = models.CharField(max_length=20, unique=True)
    ESTADOS = [
        ('disp', 'Disponível'),
        ('reservado', 'Reservado'),
        ('indisp', 'Indisponível'),
    ]
    estado = models.CharField(max_length=9, choices=ESTADOS, default='disp')

    class Meta:
        db_table = 'livros'

    def __str__(self):
        return f'{self.livro.titulo} – {self.codigo_exemplar}'


class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    exemplar = models.ForeignKey(Exemplar, on_delete=models.RESTRICT)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_agendada = models.DateTimeField()
    STATUS = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
    ]
    status = models.CharField(max_length=9, choices=STATUS, default='pendente')
    data_confirmacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reservas'
        unique_together = ('exemplar', 'data_agendada')


class Emprestimo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    exemplar = models.ForeignKey(Exemplar, on_delete=models.RESTRICT)
    data_retirada = models.DateTimeField(auto_now_add=True)
    data_prevista_devolucao = models.DateTimeField()
    data_devolucao_real = models.DateTimeField(null=True, blank=True)
    STATUS_EM = [
        ('em_uso', 'Em Uso'),
        ('devolvido', 'Devolvido'),
        ('atrasado', 'Atrasado'),
    ]
    status_emprestimo = models.CharField(max_length=9, choices=STATUS_EM, default='em_uso')
    num_renovacoes = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'emprestimos'
        indexes = [
            models.Index(fields=['exemplar', 'status_emprestimo']),
        ]


class PenaltyLog(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.SET_NULL, null=True)
    dias_atraso = models.IntegerField()
    data_aplicacao = models.DateTimeField(auto_now_add=True)
    bloqueio_ate = models.DateTimeField()

    class Meta:
        db_table = 'penalty_log'


class ReportRecord(models.Model):
    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveIntegerField()
    data_geracao = models.DateTimeField(auto_now_add=True)
    arquivo_pdf = models.CharField(max_length=255)

    class Meta:
        db_table = 'report_record'
        unique_together = ('mes', 'ano')


class SystemSetting(models.Model):
    chave = models.CharField(max_length=50, primary_key=True)
    valor = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'system_settings'


class OperationLog(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    tabela_afetada = models.CharField(max_length=50)
    acao = models.CharField(max_length=50)
    descricao = models.TextField()
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'logs_operacoes'
        indexes = [
            models.Index(fields=['tabela_afetada', 'data_hora']),
        ]
