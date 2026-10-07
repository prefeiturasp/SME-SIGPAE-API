import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar fabricantes', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
function guardar(contexto, requisicao) {
	requisicao.then((response) => { contexto.response = response })
}
When('consulto todos os fabricantes', function () {
	guardar(this, cy.consultar_fabricantes(''))
})
When('consulto o fabricante pelo UUID valido', function () {
	return cy.executar_fabricantes({ qs: { page: 1, limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		return cy.consultar_fabricantes(response.body.results[0].uuid)
	}).then((response) => { this.response = response })
})
When('consulto o fabricante pelo UUID invalido', function () {
	guardar(this, cy.consultar_fabricantes('79a6ac62-559b-478d-a1e8-f07298d2aaaa'))
})
When('consulto a lista de nomes de fabricantes', function () {
	guardar(this, cy.consultar_fabricantes_lista_nomes())
})
When('consulto fabricantes para avaliar reclamacao', function () {
	guardar(this, cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao())
})
When('consulto fabricantes para nova reclamacao', function () {
	guardar(this, cy.consultar_fabricantes_lista_nomes_nova_reclamacao())
})
When('consulto fabricantes para responder reclamacao', function () {
	guardar(this, cy.consultar_lista_nomes_responder_reclamacao())
})
When('consulto fabricantes para resposta da escola', function () {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
	guardar(this, cy.consultar_lista_nomes_responder_reclamacao_escola())
})
When('consulto fabricantes para resposta da nutrisupervisao', function () {
	guardar(this, cy.consultar_nomes_responder_reclamacao_nutrisupervisao())
})
When('consulto nomes unicos de fabricantes', function () {
	guardar(this, cy.consultar_lista_nomes_unicos())
})
function validarLista(response) {
	expect(response.body.results).to.be.an('array')
	if (response.body.results.length) {
		expect(response.body.results[0]).to.include.all.keys('nome', 'uuid')
	}
}
Then('a consulta de fabricantes retorna status 200 e uma lista valida', function () {
	expect(this.response.status).to.eq(200)
	validarLista(this.response)
})
Then('o fabricante retorna status 200 e os campos esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('uuid', 'nome')
})
Then('o fabricante invalido retorna status 403 ou 404', function () {
	expect([403, 404]).to.include(this.response.status)
	if (this.response.status === 403) expect(this.response.body.detail).to.not.be.empty
})
Then('a consulta da escola retorna status permitido e dados coerentes', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) expect(this.response.body.detail).to.not.be.empty
	else validarLista(this.response)
})
Then('a consulta retorna status 200 e uma propriedade results', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
})

let fabricanteTemporario
let tokenTemporario
afterEach(() => {
	if (!fabricanteTemporario) return
	return cy.executar_fabricantes({ method: 'DELETE', caminho: fabricanteTemporario + '/', token: tokenTemporario }).then((response) => {
		expect([204, 404], 'limpeza do fabricante temporario').to.include(response.status)
		fabricanteTemporario = undefined
	})
})
When('executo o ciclo de cadastro e alteracao de fabricante', function () {
	const nome = `CYPRESS-FABRICANTE-${Date.now()}-${Cypress._.random(100000)}`
	tokenTemporario = globalThis.token
	return cy.executar_fabricantes({ method: 'POST', body: { nome } }).then((response) => {
		if (response.status === 201) fabricanteTemporario = response.body.uuid
		expect(response.status).to.eq(201)
		expect(response.body.nome).to.eq(nome)
		expect(fabricanteTemporario).to.be.a('string').and.not.be.empty
		return cy.executar_fabricantes({ method: 'PUT', caminho: fabricanteTemporario + '/', body: { nome: nome + '-PUT' } })
	}).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.nome).to.eq(nome + '-PUT')
		return cy.executar_fabricantes({ method: 'PATCH', caminho: fabricanteTemporario + '/', body: { nome: nome + '-PATCH' } })
	}).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.nome).to.eq(nome + '-PATCH')
		return cy.executar_fabricantes({ caminho: fabricanteTemporario + '/' })
	}).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.nome).to.eq(nome + '-PATCH')
		return cy.executar_fabricantes({ method: 'DELETE', caminho: fabricanteTemporario + '/' })
	}).then((response) => {
		expect(response.status).to.eq(204)
		const uuid = fabricanteTemporario
		fabricanteTemporario = undefined
		return cy.executar_fabricantes({ caminho: uuid + '/' })
	}).then((response) => { this.response = response })
})
When('consulto fabricante com UUID malformado', function () {
	return cy.executar_fabricantes({ caminho: 'uuid-invalido/' }).then((response) => { this.response = response })
})
When('consulto fabricantes com limite {int} e deslocamento {int}', function (limit, offset) {
	this.limite = limit
	return cy.executar_fabricantes({ qs: { page: 1, limit, offset } }).then((response) => { this.response = response })
})
Then('fabricantes retorna pagina com limite solicitado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.have.length(this.limite)
	validarLista(this.response)
})
When('consulto fabricantes apos o total', function () {
	return cy.executar_fabricantes({ qs: { page: 1, limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		return cy.executar_fabricantes({ qs: { page: 1, limit: 1, offset: response.body.count } })
	}).then((response) => { this.response = response })
})
When('consulto fabricantes com edital inexistente', function () {
	return cy.executar_fabricantes({ qs: { nome_edital: 'CYPRESS-EDITAL-INEXISTENTE-000000' } }).then((response) => { this.response = response })
})
Then('fabricantes retorna lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
})
When('consulto fabricantes na rota {string} com acesso {string}', function (rota, acesso) {
	return cy.executar_fabricantes({ caminho: rota === 'lista' ? '' : rota + '/', token: acesso === 'ausente' ? null : 'token-invalido' }).then((response) => { this.response = response })
})
When('consulto reclamacao de escola com perfil CODAE', function () {
	return cy.executar_fabricantes({ caminho: 'lista-nomes-responder-reclamacao-escola/' }).then((response) => { this.response = response })
})
When('consulto nomes de fabricantes filtrados por reclamacoes', function () {
	return cy.executar_fabricantes({ caminho: 'lista-nomes/', qs: { filtrar_por: 'reclamacoes/' } }).then((response) => { this.response = response })
})
Then('fabricantes retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
