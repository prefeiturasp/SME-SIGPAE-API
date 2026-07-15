SELECT terceirizada_terceirizada.nome_fantasia nome_terceirizada,
	   produto_homologacaodoproduto.status,
	   count(*)
	FROM django_content_type,
		 perfil_vinculo,
		 perfil_usuario,
		 produto_homologacaodoproduto,
		 produto_produto,
		 terceirizada_terceirizada
	WHERE perfil_vinculo.content_type_id = django_content_type.id
	  AND terceirizada_terceirizada.id = object_id
	  AND perfil_vinculo.usuario_id = perfil_usuario.id
	  AND produto_produto.criado_por_id = perfil_usuario.id
	  AND produto_homologacaodoproduto.produto_id = produto_produto.id
	  AND django_content_type.app_label = 'terceirizada'
	  AND django_content_type.model = 'terceirizada'
	GROUP BY nome_terceirizada, status
	ORDER BY nome_terceirizada
