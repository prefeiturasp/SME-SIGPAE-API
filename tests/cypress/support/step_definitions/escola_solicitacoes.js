import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const escolaUuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'

const consultas = {
	'autorizadas temporariamente dieta': () =>
		cy.ue_consultar_autorizadas_temporariamente_dieta(escolaUuid),
	autorizados: () => cy.ue_consultar_autorizados(),
	'autorizados dieta': () => cy.ue_consultar_autorizados_dieta(escolaUuid),
	cancelados: () => cy.ue_consultar_cancelados(),
	'cancelados dieta': () => cy.ue_consultar_cancelados_dieta(escolaUuid),
	'inativas dieta': () => cy.ue_consultar_inativas_dieta(escolaUuid),
	'inativas temporariamente dieta': () =>
		cy.ue_consultar_inativas_temporariamente_dieta(escolaUuid),
	negados: () => cy.ue_consultar_negados(),
	'negados dieta': () => cy.ue_consultar_negados_dieta(escolaUuid),
	'pendentes autorizacao dieta': () =>
		cy.ue_consultar_pendentes_autorizacao_dieta(escolaUuid),
	'pendentes autorizacao': () => cy.ue_consultar_pendentes_autorizacao(),
	'aguardando vigencia dieta': () =>
		cy.ue_consultar_aguardando_vigencia_dieta(escolaUuid),
	'kit lanches autorizadas': () => cy.ue_consultar_kit_lanches_autorizadas(),
	'suspensoes autorizadas': () => cy.ue_consultar_suspensoes_autorizadas(),
}

Given('que estou autenticado como diretor de escola para consultar solicitacoes', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
})

When('consulto solicitacoes da escola pelo agrupamento {string}', function (agrupamento) {
	expect(consultas, `agrupamento ${agrupamento}`).to.have.property(agrupamento)
	consultas[agrupamento]().then((response) => {
		this.response = response
	})
})

When('consulto as solicitacoes detalhadas da escola', function () {
	cy.ue_consultar_solicitacoes_detalhadas().then((response) => {
		this.response = response
	})
})

Then('a consulta de solicitacoes da escola retorna uma lista paginada valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
})

Then('a consulta detalhada da escola retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('data').that.is.an('array')
	expect(this.response.body).to.have.property('status')
})

Then('a consulta de solicitacoes da escola retorna resultados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array')
})
