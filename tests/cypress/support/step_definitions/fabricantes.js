import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar fabricantes', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
function guardar(contexto, requisicao) {
	requisicao.then((response) => { contexto.response = response })
}
When('consulto todos os fabricantes', function () {
	guardar(this, cy.consultar_fabricantes(''))
})
When('consulto o fabricante pelo UUID valido', function () {
	guardar(this, cy.consultar_fabricantes('79a6ac62-559b-478d-a1e8-f07298d2bbcb'))
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
	guardar(this, cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao())
})
When('consulto fabricantes para responder reclamacao', function () {
	guardar(this, cy.consultar_lista_nomes_responder_reclamacao())
})
When('consulto fabricantes para resposta da escola', function () {
	cy.autenticar_login(Cypress.config('usuario_diretor_ue'), Cypress.config('senha'))
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
