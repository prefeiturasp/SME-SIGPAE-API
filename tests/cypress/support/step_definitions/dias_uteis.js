import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const formatoData = /^\d{4}-\d{2}-\d{2}$/

Given('que estou autenticado como CODAE para consultar dias uteis', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto os proximos dias uteis', function () {
	cy.consultar_dias_uteis().then((response) => {
		this.response = response
	})
})

Then(
	'a consulta de dias uteis retorna status 200 e as datas esperadas',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
		expect(this.response.body).to.include.all.keys(
			'proximos_cinco_dias_uteis',
			'proximos_dois_dias_uteis',
		)

		const proximosCincoDias = this.response.body.proximos_cinco_dias_uteis
		const proximosDoisDias = this.response.body.proximos_dois_dias_uteis

		expect(proximosCincoDias).to.match(formatoData)
		expect(proximosDoisDias).to.match(formatoData)
		expect(Date.parse(proximosCincoDias)).to.be.greaterThan(
			Date.parse(proximosDoisDias),
		)
	},
)
