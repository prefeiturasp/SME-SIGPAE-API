import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const dreUuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
const consultas = {
	'aguardando codae': () => cy.dre_consultar_aguardando_codae(),
	'autorizadas temporariamente dieta': () =>
		cy.dre_consultar_autorizadas_temporariamente_dieta(dreUuid),
	autorizados: () => cy.dre_consultar_autorizados(),
	'autorizados dieta': () => cy.dre_consultar_autorizados_dieta(dreUuid),
	cancelados: () => cy.dre_consultar_cancelados(),
	'cancelados dieta': () => cy.dre_consultar_cancelados_dieta(dreUuid),
	'inativas dieta': () => cy.dre_consultar_inativas_dieta(dreUuid),
	'inativas temporariamente dieta': () =>
		cy.dre_consultar_inativas_temporariamente_dieta(dreUuid),
	negados: () => cy.dre_consultar_negados(),
	'negados dieta': () => cy.dre_consultar_negados_dieta(dreUuid),
	'pendentes autorizacao dieta': () =>
		cy.dre_consultar_pendentes_autorizacao_dieta(dreUuid),
	'pendentes autorizacao': () => cy.dre_consultar_pendentes_autorizacao(),
}

function validarPermissaoNegada(response) {
	expect(response.body).to.have.property('detail').that.is.a('string').and.not.empty
}

function validarStatus(response) {
	expect([200, 403]).to.include(response.status)
	if (response.status === 403) validarPermissaoNegada(response)
}

Given('que estou autenticado para consultar solicitacoes da DRE', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
})

When('consulto solicitacoes da DRE pelo agrupamento {string}', function (agrupamento) {
	expect(consultas, `agrupamento ${agrupamento}`).to.have.property(agrupamento)
	consultas[agrupamento]().then((response) => { this.response = response })
})

When('consulto as solicitacoes detalhadas da DRE', function () {
	cy.dre_consultar_solicitacoes_detalhadas().then((response) => {
		this.response = response
	})
})

When('consulto pendencias da DRE com filtro {string} e visao {string}', function (filtro, visao) {
	cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(filtro, visao)
		.then((response) => { this.response = response })
})

Then('a consulta de solicitacoes da DRE retorna dados ou permissao negada', function () {
	validarStatus(this.response)
	if (this.response.status === 200) {
		expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
		expect(this.response.body.results).to.be.an('array')
	}
})

Then('a consulta detalhada da DRE retorna dados ou permissao negada', function () {
	validarStatus(this.response)
	if (this.response.status === 200) {
		expect(this.response.body).to.have.property('data').that.is.an('array')
		expect(this.response.body).to.have.property('status')
	}
})

Then('a consulta filtrada da DRE retorna dados ou permissao negada', function () {
	validarStatus(this.response)
	if (this.response.status === 200) {
		expect(this.response.body).to.have.property('results')
	}
})
