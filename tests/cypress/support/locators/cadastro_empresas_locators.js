export const Cadastro_Empresas_Locators = {
	inputs: {
		// Dados da Empresa
		nomeEmpresa: '[data-cy="razao_social"]',
		nome_usual: '[data-cy="nome_fantasia"]',
		cnpj: '#content-wrapper input[placeholder="Digite o CNPJ da Empresa"]',

		// Endereco da Empresa
		cep: '#cep',
		endereco: '[data-cy="endereco"]',
		numero: '[data-cy="numero"]',
		complemento: '[data-cy="complemento"]',
		bairro: '[data-cy="bairro"]',
		cidade: '[data-cy="cidade"]',
		estado: '[data-cy="estado"]',

		// Dados do Representante do Contrato
		rep_nome:
			'#content-wrapper section:nth-of-type(3) input:nth-of-type(1), #content-wrapper input[name="nome"]',
		rep_cpf:
			'#content-wrapper section:nth-of-type(3) input:nth-of-type(2), #content-wrapper input[name="cpf"]',
		rep_cargo:
			'#content-wrapper section:nth-of-type(3) input:nth-of-type(3), #content-wrapper input[name="cargo"]',
		rep_telefone:
			'#content-wrapper section:nth-of-type(3) input:nth-of-type(4), #content-wrapper input[name="telefone"]',
		rep_email:
			'#content-wrapper section:nth-of-type(3) input:nth-of-type(5), #content-wrapper input[name="email"]',

		// Contatos
		contato_nome:
			'#content-wrapper section:nth-of-type(4) input:nth-of-type(1)',
		contato_telefone:
			'#content-wrapper section:nth-of-type(4) input:nth-of-type(2)',
		contato_email:
			'#content-wrapper section:nth-of-type(4) input:nth-of-type(3)',

		// Contratos
		processo_administrativo:
			'#content-wrapper section:nth-of-type(5) input:nth-of-type(1)',
		numero_contrato:
			'#content-wrapper section:nth-of-type(5) input:nth-of-type(2)',
		numero_pregao_eletronico:
			'#content-wrapper section:nth-of-type(5) input:nth-of-type(3)',
		vigencia_de:
			'#content-wrapper input[placeholder="De"], input[placeholder="De"]',
		vigencia_ate:
			'#content-wrapper input[placeholder="Até"], #content-wrapper input[placeholder="AtÃ©"], #content-wrapper input[placeholder="AtÃƒÂ©"], input[placeholder="Até"], input[placeholder="AtÃ©"], input[placeholder="AtÃƒÂ©"]',
	},

	selects: {
		tipo_servico: 'select:eq(0)',
		tipo_empresa: 'select:eq(1)',
		tipo_alimento: 'select:eq(2)',
		modalidade: 'select:eq(3)',
		programa: 'select:eq(4)',
		situacao: 'select:last',
	},

	buttons: {
		adicionar_contato: 'button:contains("+"), button[type="button"]',
		adicionar_contrato: 'button:contains("Adicionar")',
		salvar: '[data-cy="Salvar"]',
		cancelar: '[data-testid="btn-cancelar"]',
	},

	modais: {
		confirmacao: '[data-cy="Sim"]',
	},

	mensagens: {
		sucesso: '#root div.Toastify__toast',
	},
}
