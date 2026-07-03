from ..models import ItemPorMolde, LogAuditoria

class ItemService:
    
    @staticmethod
    def adicionar(id_ref_molde, item_codigo, descricao, cod_complementar, linha, status, usuario_logado):
        item_codigo = item_codigo.strip().upper()
        id_molde_tratado = int(id_ref_molde) if id_ref_molde and id_ref_molde.isdigit() else None

        if ItemPorMolde.objects.filter(item_codigo__iexact=item_codigo).exists():
            raise ValueError(f"Erro: O código de item '{item_codigo}' já existe!")

        novo_item = ItemPorMolde.objects.create(
            molde_id=id_molde_tratado,
            item_codigo=item_codigo,
            descricao=descricao.strip() if descricao else '',
            cod_complementar=cod_complementar.strip().upper() if cod_complementar else '',
            linha=linha.strip() if linha else '',
            status=status
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='ITENS', acao='CRIADO',
            descricao=f"Criou o item {item_codigo}. Status: {status}."
        )
        return novo_item.id_item

    @staticmethod
    def alterar(id_item, id_ref_molde, item_codigo, descricao, cod_complementar, linha, status, usuario_logado):
        item_codigo = item_codigo.strip().upper()
        id_molde_tratado = int(id_ref_molde) if id_ref_molde and id_ref_molde.isdigit() else None

        if ItemPorMolde.objects.filter(item_codigo__iexact=item_codigo).exclude(id_item=id_item).exists():
            raise ValueError(f"Erro: O código de item '{item_codigo}' já existe!")

        linhas_afetadas = ItemPorMolde.objects.filter(id_item=id_item).update(
            molde_id=id_molde_tratado,
            item_codigo=item_codigo,
            descricao=descricao.strip() if descricao else '',
            cod_complementar=cod_complementar.strip().upper() if cod_complementar else '',
            linha=linha.strip() if linha else '',
            status=status
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='ITENS', acao='EDITADO',
            descricao=f"Alterou o item {item_codigo} (ID: {id_item}). Status atual: {status}."
        )
        return linhas_afetadas > 0