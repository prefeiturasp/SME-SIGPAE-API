import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuidInvalido = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
const listas = {
	nomes: 'consultar_marcas_lista_nomes',
	avaliar_reclamacao: 'consultar_lista_nomes_avaliar_reclamacao',
	nova_reclamacao: 'consultar_lista_nomes_nova_reclamacao',
	responder_reclamacao: 'consultar_lista_nomes_responder_reclamacao',
}
Given('que estou autenticado como CODAE para gerenciar marcas', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto todas as marcas', function () {
	cy.consultar_marcas().then((response) => { this.response = response })
})
When('consulto marcas por um edital existente', function () {
	cy.consultar_editais().then((editais) => {
		cy.consultar_marcas_por_edital(`?nome_edital=${editais.body.results[0].numero}`)
			.then((response) => { this.response = response })
	})
})
When('consulto marcas por um edital invalido', function () {
	cy.consultar_marcas_por_edital('?nome_edital=NomeInvalido Para o Teste')
		.then((response) => { this.response = response })
})
When('consulto uma marca existente por UUID', function () {
	cy.consultar_marcas().then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy.consultar_marcas_por_uuid(this.uuid).then((response) => { this.response = response })
	})
})
When('consulto uma marca por UUID invalido', function () {
	cy.consultar_marcas_por_uuid('3ac751ee-f95d-4d5b-80da-437506b00000')
		.then((response) => { this.response = response })
})
function nomeTeste(prefixo = 'Teste Automacao') {
	return `${prefixo} ${Date.now()}`
}
When('cadastro uma marca valida para remocao', function () {
	const nome = nomeTeste()
	cy.cadastrar_marcas({ nome }).then((criada) => {
		this.response = criada
		this.nome = nome
		cy.deletar_marcas(criada.body.uuid).then((exclusao) => { this.exclusao = exclusao })
	})
})
When('cadastro e excluo uma marca valida', function () {
	cy.cadastrar_marcas({ nome: nomeTeste() }).then((criada) => {
		expect(criada.status).to.eq(201)
		cy.deletar_marcas(criada.body.uuid).then((response) => { this.response = response })
	})
})
When('excluo uma marca por UUID invalido', function () {
	cy.deletar_marcas(uuidInvalido).then((response) => { this.response = response })
})
function atualizar(contexto, metodo) {
	cy.cadastrar_marcas({ nome: nomeTeste(`Teste ${metodo}`) }).then((criada) => {
		expect(criada.status).to.eq(201)
		contexto.nome = `Testes Automatizados - Alterado via ${metodo}`
		const comando = metodo === 'PUT' ? 'put_alterar_marcas' : 'patch_alterar_marcas'
		cy[comando](criada.body.uuid, { nome: contexto.nome }).then((response) => {
			contexto.response = response
			cy.deletar_marcas(criada.body.uuid).then((exclusao) => { contexto.exclusao = exclusao })
		})
	})
}
When('atualizo uma marca valida por PUT', function () { atualizar(this, 'PUT') })
When('atualizo uma marca valida por PATCH', function () { atualizar(this, 'PATCH') })
When('atualizo por PUT uma marca com UUID invalido', function () {
	cy.put_alterar_marcas(uuidInvalido, {}).then((response) => { this.response = response })
})
When('atualizo por PATCH uma marca com UUID invalido', function () {
	cy.patch_alterar_marcas(uuidInvalido, {}).then((response) => { this.response = response })
})
When('consulto a lista de marcas {string}', function (lista) {
	cy[listas[lista]]().then((response) => { this.response = response })
})
When('consulto marcas para resposta da escola', function () {
	cy.autenticar_login(Cypress.config('usuario_diretor_ue'), Cypress.config('senha'))
	cy.consultar_lista_nomes_responder_reclamacao_escola().then((response) => {
		this.response = response
	})
})
When('consulto marcas para resposta da nutrisupervisao', function () {
	cy.autenticar_login(
		Cypress.config('usuario_coordenador_supervisao_nutricao'), Cypress.config('senha'),
	)
	cy.consultar_lista_nomes_responder_reclamacao_nutrisupervisor().then((response) => {
		this.response = response
	})
})
When('consulto nomes unicos de marcas', function () {
	cy.consultar_lista_nomes_unicos().then((response) => { this.response = response })
})
function validarLista(response) {
	expect(response.body.results).to.be.an('array')
	if (response.body.results.length) {
		expect(response.body.results[0]).to.include.all.keys('uuid', 'nome')
	}
}
Then('a consulta de marcas retorna status 200 e lista valida', function () {
	expect(this.response.status).to.eq(200)
	validarLista(this.response)
})
Then('a consulta de marcas retorna status 200 e lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.empty
})
Then('a marca retorna status 200 e o UUID esperado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.nome).to.exist
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('a operacao de marca retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('a marca e criada e removida com sucesso', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body.nome).to.eq(this.nome)
	expect(this.response.body.uuid).to.exist
	expect(this.exclusao.status).to.eq(204)
})
Then('a exclusao da marca retorna status 204', function () {
	expect(this.response.status).to.eq(204)
})
Then('a marca atualizada retorna o nome esperado e e removida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.nome).to.eq(this.nome)
	expect(this.exclusao.status).to.eq(204)
})
Then('a lista de nomes de marcas retorna status 200 e dados validos', function () {
	expect(this.response.status).to.eq(200)
	validarLista(this.response)
})
Then('a lista da escola retorna status permitido e dados coerentes', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) expect(this.response.body.detail).to.not.be.empty
	else validarLista(this.response)
})
Then('a consulta de nomes unicos retorna status 200 e results', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
})
