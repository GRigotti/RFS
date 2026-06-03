from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore

class Molde(models.Model):
    # O Django já assume 'id' como primary key automaticamente se não especificarmos
    molde_nome = models.CharField(max_length=100, db_column='molde_nome')
    endereco_molde = models.CharField(max_length=50, db_column='endereco_molde')
    status = models.CharField(max_length=20, db_column='status')

    class Meta:
        managed = False # Informa ao Django: "Não crie esta tabela, ela já existe"
        db_table = 'moldes' # Nome exato da tabela no SQLite

class ItemPorMolde(models.Model):
    id_item = models.AutoField(primary_key=True, db_column='id_item')
    # db_column faz o Django ler 'id_referencia_molde' em vez do padrão 'molde_id'
    molde = models.ForeignKey(Molde, on_delete=models.CASCADE, db_column='id_referencia_molde', related_name='itens', null=True, blank=True)
    item_codigo = models.CharField(max_length=50, db_column='item_codigo')
    descricao = models.CharField(max_length=100, db_column='descricao')
    cod_complementar = models.CharField(max_length=50, db_column='cod_complementar', null=True, blank=True)
    linha = models.CharField(max_length=50, db_column='linha', null=True, blank=True)
    status = models.CharField(max_length=20, db_column='status', default='Ativo')

    class Meta:
        managed = False
        db_table = 'itens_por_molde'

class Maquina(models.Model):
    id_maquina = models.AutoField(primary_key=True, db_column='id_maquina')
    maquina = models.CharField(max_length=50, db_column='maquina')
    grupo_maquina = models.CharField(max_length=50, db_column='grupo_maquina')
    descricao = models.CharField(max_length=100, db_column='descricao')
    status = models.CharField(max_length=20, db_column='status')

    class Meta:
        managed = False
        db_table = 'maquinas'

class Colaborador(models.Model):
    nome = models.CharField(max_length=100, db_column='nome')
    funcao = models.CharField(max_length=50, db_column='funcao')
    status = models.CharField(max_length=20, db_column='status')


    class Meta:
        managed = False
        db_table = 'colaboradores'

class Problema(models.Model):
    problema = models.CharField(max_length=100, db_column='problema')
    
    class Meta:
        managed = False
        db_table = 'problemas'

class AcaoManutencao(models.Model):
    acao = models.CharField(max_length=100, db_column='acao')

    class Meta:
        managed = False
        db_table = 'acoes_manutencao'

class SolicitacaoManutencao(models.Model):
    molde = models.ForeignKey(Molde, on_delete=models.DO_NOTHING, db_column='id_molde')
    maquina = models.ForeignKey(Maquina, on_delete=models.DO_NOTHING, db_column='id_maquina')
    operador = models.ForeignKey(Colaborador, on_delete=models.DO_NOTHING, db_column='id_operador', related_name='abertas_por')
    responsavel = models.ForeignKey(Colaborador, on_delete=models.DO_NOTHING, db_column='id_responsavel', null=True, related_name='resolvidas_por')
    
    ordem_producao = models.CharField(max_length=50, db_column='ordem_producao')
    parecer_producao = models.TextField(db_column='parecer_producao')
    parecer_ferramentaria = models.TextField(db_column='parecer_ferramentaria', null=True)
    status = models.CharField(max_length=20, db_column='status', default='Aberto')
    
    data_op = models.DateTimeField(db_column='data_op', null=True)
    data_abertura = models.DateTimeField(db_column='data_abertura', default=timezone.now)
    data_fechamento = models.DateTimeField(db_column='data_fechamento', null=True)
    ultima_alteracao = models.DateTimeField(db_column='ultima_alteracao', auto_now=True)

    # Mapeamento exato das suas tabelas de ligação originais
    problemas = models.ManyToManyField(Problema, through='SolicitacaoProblema')
    acoes = models.ManyToManyField(AcaoManutencao, through='SolicitacaoAcao')

    class Meta:
        managed = False
        db_table = 'solicitacoes_manutencao'

# Tabelas de Ligação explícitas
class SolicitacaoProblema(models.Model):
    solicitacao = models.ForeignKey(SolicitacaoManutencao, on_delete=models.CASCADE, db_column='id_solicitacao')
    problema = models.ForeignKey(Problema, on_delete=models.CASCADE, db_column='id_problema')

    class Meta:
        managed = False
        db_table = 'solicitacao_problemas'

class SolicitacaoAcao(models.Model):
    solicitacao = models.ForeignKey(SolicitacaoManutencao, on_delete=models.CASCADE, db_column='id_solicitacao')
    acao = models.ForeignKey(AcaoManutencao, on_delete=models.CASCADE, db_column='id_acao')

    class Meta:
        managed = False
        db_table = 'solicitacao_acoes'