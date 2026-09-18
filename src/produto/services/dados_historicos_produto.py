from src.dados_comuns.models import LogSolicitacoesUsuario
from src.produto.models import DadosHistoricosProduto, HomologacaoProduto


class ServicoDadosHistoricosProduto:
    @staticmethod
    def registrar(
        log: LogSolicitacoesUsuario,
        homologacao: HomologacaoProduto,
    ) -> DadosHistoricosProduto:
        produto = homologacao.produto
        terceirizada = homologacao.rastro_terceirizada
        vinculo = log.usuario.vinculo_atual
        perfil = vinculo.perfil if vinculo else None
        instituicao = vinculo.instituicao if vinculo else None

        dados_historicos, _ = DadosHistoricosProduto.objects.get_or_create(
            log=log,
            defaults={
                "produto_uuid": produto.uuid,
                "empresa": getattr(terceirizada, "nome_fantasia", ""),
                "criado_em_produto": produto.criado_em,
                "nome_produto": produto.nome,
                "marca": getattr(produto.marca, "nome", ""),
                "fabricante": getattr(produto.fabricante, "nome", ""),
                "eh_para_alunos_com_dieta": produto.eh_para_alunos_com_dieta,
                "componentes": produto.componentes,
                "perfil_responsavel": getattr(perfil, "nome", ""),
                "nome_instituicao": getattr(instituicao, "nome", ""),
            },
        )
        return dados_historicos

    @staticmethod
    def copiar(
        log_original: LogSolicitacoesUsuario,
        log_copia: LogSolicitacoesUsuario,
    ) -> DadosHistoricosProduto | None:
        try:
            dados_originais = log_original.dados_produto
        except DadosHistoricosProduto.DoesNotExist:
            return None

        dados_copia, _ = DadosHistoricosProduto.objects.get_or_create(
            log=log_copia,
            defaults={
                "produto_uuid": dados_originais.produto_uuid,
                "empresa": dados_originais.empresa,
                "criado_em_produto": dados_originais.criado_em_produto,
                "nome_produto": dados_originais.nome_produto,
                "marca": dados_originais.marca,
                "fabricante": dados_originais.fabricante,
                "eh_para_alunos_com_dieta": (
                    dados_originais.eh_para_alunos_com_dieta
                ),
                "componentes": dados_originais.componentes,
                "perfil_responsavel": dados_originais.perfil_responsavel,
                "nome_instituicao": dados_originais.nome_instituicao,
            },
        )
        return dados_copia
