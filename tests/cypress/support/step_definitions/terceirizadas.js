import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuidInvalido = '3ac751ee-f95d-4d5b-80da-437506b00000'
const comandosLista = {
	emails_modulos: 'consultar_terceirizadas_emails_modulos',
	cnpjs: 'consultar_terceirizadas_lista_cnpjs',
	empresas_cronogramas: 'consultar_terceirizadas_empresas_cronogramas',
	nomes: 'consultar_terceirizadas_lista_nomes',
	distribuidores: 'consultar_terceirizadas_lista_nomes_distribuidores',
	simples: 'consultar_terceirizadas_lista_simples',
	relatorio: 'consultar_terceirizadas_relatorio_quantitativo',
}
function cpfAleatorio() {
	return Math.floor(Math.random() * 99999999999).toString().padStart(11, '0')
}
function dados(sobrescritos = {}) {
	return {
		nome_fantasia: `Testes Automacao ${Date.now()}`,
		razao_social: `Testes Automacao LTDA ${Date.now()}`,
		cnpj: '60498984000104', representante_legal: 'Representante Teste',
		representante_telefone: '1155555555', representante_email: 'representante@example.com',
		cep: '05010000', logradouro: 'Rua Teste Automacao', numero: '123',
		complemento: 'Complemento Teste', bairro: 'Bairro Teste', cidade: 'Sao Paulo',
		estado: 'SP', credenciado: true, contato_telefone: '1155555555',
		contato_email: 'user@example.com', contato_nome_nutri: 'Nutricionista Teste',
		crn_numero: '1155555555', super_admin_terceirizadas: true,
		nutri_telefone: '11 977777777', nutri_email: 'user@example.com',
		contato_eh_nutricionista: true, responsavel_cargo: 'Cargo Teste',
		responsavel_cpf: cpfAleatorio(), responsavel_nome: 'Responsavel Teste',
		responsavel_telefone: '11999999999', responsavel_email: 'responsavel@example.com',
		lotes: [], ...sobrescritos,
	}
}
const camposTerceirizada = [
	'tipo_alimento_display', 'tipo_empresa_display', 'tipo_servico_display',
	'nutricionistas', 'contatos', 'contratos', 'lotes', 'quantidade_alunos',
	'id_externo', 'ativo', 'uuid', 'nome_fantasia', 'razao_social', 'cnpj',
	'representante_legal', 'representante_telefone', 'representante_email',
	'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
	'responsavel_nome', 'responsavel_cpf', 'responsavel_telefone',
	'responsavel_email', 'responsavel_cargo', 'tipo_empresa', 'tipo_servico',
	'tipo_alimento', 'criado_em',
]
Given('que estou autenticado como CODAE para gerenciar terceirizadas', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto todas as terceirizadas', function () {
	cy.consultar_terceirizadas().then((response) => { this.response = response })
})
When('consulto uma terceirizada por nome existente', function () {
	cy.consultar_terceirizadas().then((lista) => {
		cy.consultar_terceirizadas_por_nome(lista.body.results[0].nome_fantasia)
			.then((response) => { this.response = response })
	})
})
When('consulto uma terceirizada por UUID existente', function () {
	cy.consultar_terceirizadas().then((lista) => {
		cy.consultar_terceirizadas_por_uuid(lista.body.results[0].uuid)
			.then((response) => { this.response = response })
	})
})
When('consulto uma terceirizada por UUID invalido', function () {
	cy.consultar_terceirizadas_por_uuid(uuidInvalido).then((response) => {
		this.response = response
	})
})
When('cadastro uma terceirizada valida', function () {
	cy.cadastrar_terceirizadas(dados()).then((criada) => {
		this.response = criada
		cy.deletar_terceirizadas(criada.body.uuid).then((exclusao) => { this.exclusao = exclusao })
	})
})
When('cadastro uma terceirizada com CPF de responsavel existente', function () {
	cy.consultar_terceirizadas().then((lista) => {
		cy.cadastrar_terceirizadas(dados({ responsavel_cpf: lista.body.results[0].responsavel_cpf }))
			.then((response) => { this.response = response })
	})
})
When('cadastro uma terceirizada com CNPJ em branco', function () {
	cy.cadastrar_terceirizadas(dados({ cnpj: '' })).then((response) => {
		this.response = response
	})
})
When('cadastro e excluo uma terceirizada valida', function () {
	cy.cadastrar_terceirizadas(dados()).then((criada) => {
		expect(criada.status).to.eq(201)
		cy.deletar_terceirizadas(criada.body.uuid).then((response) => { this.response = response })
	})
})
When('excluo uma terceirizada por UUID invalido', function () {
	cy.deletar_terceirizadas(uuidInvalido).then((response) => { this.response = response })
})
function atualizar(contexto, metodo) {
	const original = dados()
	cy.cadastrar_terceirizadas(original).then((criada) => {
		expect(criada.status).to.eq(201)
		const alterados = dados({
			responsavel_cpf: original.responsavel_cpf,
			nome_fantasia: `Testes Automacao ${metodo} ${Date.now()}`,
		})
		const comando = metodo === 'PUT' ? 'alterar_terceirizadas_put' : 'alterar_terceirizadas_patch'
		cy[comando](criada.body.uuid, alterados).then((response) => {
			contexto.response = response
			cy.deletar_terceirizadas(criada.body.uuid).then((exclusao) => { contexto.exclusao = exclusao })
		})
	})
}
When('atualizo uma terceirizada valida por PUT', function () { atualizar(this, 'PUT') })
When('atualizo uma terceirizada valida por PATCH', function () { atualizar(this, 'PATCH') })
When('atualizo por PUT uma terceirizada com UUID invalido', function () {
	cy.alterar_terceirizadas_put(uuidInvalido, dados()).then((response) => { this.response = response })
})
When('atualizo por PATCH uma terceirizada com UUID invalido', function () {
	cy.alterar_terceirizadas_patch(uuidInvalido, dados()).then((response) => { this.response = response })
})
When('consulto a listagem de terceirizadas {string}', function (lista) {
	this.lista = lista
	cy[comandosLista[lista]]().then((response) => { this.response = response })
})
function validarObjeto(item) {
	expect(item).to.include.all.keys(...camposTerceirizada)
	expect(item.nutricionistas).to.be.an('array')
	expect(item.contatos).to.be.an('array')
	expect(item.contratos).to.be.an('array')
	expect(item.lotes).to.be.an('array')
	expect(item.ativo).to.be.a('boolean')
}
Then('a lista de terceirizadas retorna dados completos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarObjeto(this.response.body.results[0])
})
Then('a terceirizada retorna dados completos', function () {
	expect(this.response.status).to.eq(200)
	validarObjeto(this.response.body)
})
Then('a operacao de terceirizada retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('a terceirizada e criada e removida com sucesso', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body.cnpj).to.eq('60498984000104')
	expect(this.exclusao.status).to.eq(204)
})
Then('o cadastro da terceirizada retorna status 400 e erro de CPF', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.responsavel_cpf).to.be.an('array').and.not.be.empty
})
Then('o cadastro da terceirizada retorna status 400 e erro de CNPJ', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.cnpj).to.be.an('array').and.not.be.empty
})
Then('a exclusao da terceirizada retorna status 204', function () {
	expect(this.response.status).to.eq(204)
})
Then('a terceirizada e atualizada e removida com sucesso', function () {
	expect(this.response.status).to.eq(200)
	expect(this.exclusao.status).to.eq(204)
})
Then('a listagem {string} retorna status 200 e dados validos', function (lista) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
	if (!this.response.body.results.length || lista === 'cnpjs') return
	const item = this.response.body.results[0]
	if (lista === 'emails_modulos') {
		expect(item).to.include.all.keys('uuid', 'razao_social', 'emails_terceirizadas')
		expect(item.emails_terceirizadas).to.be.an('array')
	} else if (['empresas_cronogramas', 'nomes'].includes(lista)) {
		expect(item).to.include.all.keys('uuid', 'cnpj', 'nome_fantasia', 'contatos', 'contratos')
	} else if (['distribuidores', 'simples'].includes(lista)) {
		expect(item).to.include.all.keys('uuid', 'nome_fantasia', 'razao_social')
	} else {
		expect(item).to.include.all.keys('nome_terceirizada', 'qtde_por_status')
		expect(item.qtde_por_status[0]).to.include.all.keys('status', 'qtde')
	}
})
