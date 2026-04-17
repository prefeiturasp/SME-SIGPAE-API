export const Cadastro_Empresas_Locators = {
	// Inputs
	inputs: {
		nomeEmpresa: '[data-cy="razao_social"]',
		cnpj: '#content-wrapper input[placeholder="Digite o CNPJ da Empresa"]',
		nome_usual: '[data-cy="nome_fantasia"]',
		cep: '#cep',
		endereco: '[data-cy="endereco"]',
		numero: '[data-cy="numero"]',
		complemento: '[data-cy="complemento"]',
		bairro: '[data-cy="bairro"]',
		cidade: '[data-cy="cidade"]',
		estado: '[data-cy="estado"]',
		telefone_empresa: '#telefone_empresa_0',
		email_empresa: '[data-cy="email_empresa_0"]',

		//principal Admin do Sistema
		responsavel_email: '[data-cy="responsavel_email"]',
		responsavel_nome: '[data-cy="responsavel_nome"]',
		responsavel_cpf:
			'#content-wrapper div:nth-child(3) > div:nth-child(1) > div.input > input.false',
		responsavel_telefone:
			'#content-wrapper div:nth-child(3) > div:nth-child(2) > div.input > input.false',
		responsavel_cargo: '[data-cy="responsavel_cargo"]',

		//Representante Legal
		rep_legal_nome: '[data-cy="representante_legal"]',
		rep_legal_telefone: '#telefone_representante',
		rep_legal_email: '[data-cy="representante_email"]',

		//Nutricionista Responsável Técnico
		nutri_responsavel_nome: '[data-cy="nutricionista_nome_0"]',
		nutri_responsavel_crn: '[data-cy="nutricionista_crn_0"]',
		nutri_responsavel_telefone: '#telefone_terceirizada_0',
		nutri_responsavel_email: '[data-cy="email_terceirizada_0"]',
	},

	// Buttons
	buttons: {
		salvar: '[data-cy="Salvar"]',
		cancelar: '[data-testid="btn-cancelar"]',
		editar: '[data-testid="btn-editar"]',
	},

	// Selects
	selects: {
		tipoEmpresa: 'select[name="tipo_empresa"]',
		estado: '[data-testid="select-estado"]',
	},

	// Tabelas
	tabelas: {
		linhas: 'table tbody tr',
		linhaComEmpresa: (nomeEmpresa) =>
			`table tbody tr:contains("${nomeEmpresa}")`,
	},

	// Modais
	modais: {
		confirmacao: '[data-cy="Sim"]',
		fechar: '[data-cy="Nao"]',
	},

	// Mensagens
	mensagens: {
		sucesso: '#root div.Toastify__toast',
		erro: '[data-testid="alert-erro"]',
	},
}
