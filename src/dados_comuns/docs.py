DOCS_FLUXO_PARTINDO_ESCOLA_GESTAO_ALIMENTACAO_DJANGO_WORKFLOW = {
    "inicia_fluxo": """
        Inicia o fluxo da solicitação de Gestão de Alimentação (envia a solicitação para DRE validar).

        Só é possível iniciar uma solicitação que esteja em **RASCUNHO**.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_inicia_fluxo_hook``) para, após o início do fluxo:
          - definir o campo ``foi_solicitado_fora_do_prazo`` com base na prioridade da solicitação.
          - salvar os rastros históricos da solicitação (escola, DRE, lote e terceirizada).
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
    """,
    "codae_autoriza": """
        Autoriza a solicitação de Gestão de Alimentação como CODAE pedida com mais de 5 dias úteis de antecedência.
        Só é possível autorizar uma solicitação que foi validada pela Diretoria Regional.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_autoriza_hook``) para, após a autorização:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a autorização.
    """,
    "codae_autoriza_questionamento": """
        CODAE autoriza a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência, mediante resposta positiva do questionamento para a empresa terceirizada que atende a escola.
        Só é possível autorizar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser autorizada se:
          - teve uma resposta positiva do questionamento pela empresa terceirizada que atende a escola, ou seja, resposta_sim_nao=True no log de questionamento.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_autoriza_hook``) para, após a autorização:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a autorização.
    """,
    "codae_nega": """
        CODAE nega a solicitação de Gestão de Alimentação.
        Só é possível negar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser negada se, por exemplo:
          - infringir alguma regra do edital
          - tiver algum dado incorreto ou inconsistente (por exemplo, um Kit Lanche não pode ser solicitado para um "passeio" nas dependências da escola. É apenas para passeios externos.)

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_recusou_hook``) para, após a negação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a negação.
    """,
    "codae_nega_questionamento": """
        CODAE nega a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência.
        Só é possível negar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pode ser negada se:
          - não tiver uma resposta positiva do questionamento pela empresa terceirizada que atende a escola, ou seja, resposta_sim_nao=False no log de questionamento.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_recusou_hook``) para, após a negação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a negação.
    """,
    "codae_questiona": """
        CODAE questiona a empresa terceirizada se é possível atender a solicitação de Gestão de Alimentação pedida com menos de 5 dias úteis de antecedência.
        Só é possível questionar uma solicitação que foi validada pela Diretoria Regional.

        Uma solicitação pedida com menos de 5 dias úteis de antecedência não pode ser autorizada imediatamente, pois a empresa terceirizada que atende a escola precisa confirmar se é possível atender a solicitação nesse prazo. Portanto, o CODAE questiona a solicitação para obter essa confirmação.

        Exceção (pode ser autorizado imediatamente, sem questionamento):
          - Alteração do Tipo de Alimentação - Lanche Emergencial

        Este método é herdado de django_xworkflows.

        Possui um hook (``_codae_questiona_hook``) para, após o questionamento:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
    """,
    "dre_nao_valida": """
        DRE não valida a solicitação de Gestão de Alimentação.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_dre_nao_valida_hook``) para, após a não validação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - enviar e-mail para as partes interessadas notificando sobre a não validação.
    """,
    "dre_pede_revisao": """
        Deprecado.

        Este método é herdado de django_xworkflows.
    """,
    "dre_valida": """
        DRE valida a solicitação de Gestão de Alimentação.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_dre_valida_hook``) para, após a validação:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
    """,
    "escola_revisa": """
        Deprecado.

        Este método é herdado de django_xworkflows.
    """,
    "terceirizada_toma_ciencia": """
        Deprecado.

        Este método é herdado de django_xworkflows.

        Antigamente, este método era utilizado para registrar a ciência da empresa terceirizada sobre a solicitação.

        O status final do fluxo era **TERCEIRIZADA_TOMOU_CIENCIA**.

        Atualmente:
          - o status final é **CODAE_AUTORIZADO**.
          - o status TERCEIRIZADA_TOMOU_CIENCIA foi deprecado.
          - a empresa toma ciência sem alterar o status da solicitação, através do campo ``terceirizada_conferiu_gestao``.
    """,
    "terceirizada_responde_questionamento": """
        A empresa terceirizada responde ao questionamento da CODAE sobre a possibilidade de atendimento da solicitação.

        Só é possível responder um questionamento quando a solicitação está em **CODAE_QUESTIONADO**.

        Caso a empresa responda que **sim** (resposta_sim_nao=True), a solicitação pode ser autorizada normalmente pela CODAE, mesmo tendo sido pedida com menos de 5 dias úteis de antecedência.

        Caso a empresa responda que **não** (resposta_sim_nao=False), a solicitação deve ser negada pela CODAE, pois a empresa, pelo contrato, tem o direito de negar solicitações pedidas com menos de 5 dias úteis de antecedência.

        Este método é herdado de django_xworkflows.

        Possui um hook (``_terceirizada_responde_questionamento_hook``) para, após a resposta:
          - criar uma entrada de log específico para esta ação, utilizando o método ``salvar_log_transicao``.
          - registrar no log a justificativa informada e a resposta booleana em ``resposta_sim_nao``.
    """,
}
