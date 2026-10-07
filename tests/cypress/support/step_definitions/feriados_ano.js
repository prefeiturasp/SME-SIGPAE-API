import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function validarDatas(response, proximo) {
	expect(response.status).to.eq(200)
	expect(response.body).to.have.property('results').that.is.an('array').and.not.be.empty
	// Usa o ano do servidor para nao depender do relogio da maquina que executa o teste.
	const referencia = response.headers.date ? new Date(response.headers.date) : new Date()
	const ano = referencia.getUTCFullYear()
	const datas = response.body.results.map((valor) => {
		expect(valor).to.match(proximo ? /^\d{4}-\d{2}-\d{2}$/ : /^\d{2}\/\d{2}\/\d{4}$/)
		const [a, m, d] = proximo ? valor.split('-').map(Number) : valor.split('/').reverse().map(Number)
		const data = new Date(Date.UTC(a, m - 1, d))
		expect([data.getUTCFullYear(), data.getUTCMonth() + 1, data.getUTCDate()]).to.deep.eq([a, m, d])
		expect(proximo ? [ano, ano + 1] : [ano]).to.include(a)
		return data.toISOString().slice(0, 10)
	})
	expect(new Set(datas).size, 'datas sem duplicacao').to.eq(datas.length)
	expect(datas).to.deep.eq([...datas].sort())
	for (const a of proximo ? [ano, ano + 1] : [ano]) {
		expect(datas).to.include(`${a}-01-01`)
		expect(datas).to.include(`${a}-12-25`)
	}
	return datas
}
When('consulto feriados da rota {string} com acesso {string}', function (rota, acesso) {
	this.proximo = rota === 'atual e proximo'
	const executar = () => cy.executar_feriados_ano({ proximo: this.proximo,
		token: acesso === 'ausente' ? null : acesso === 'invalido' ? 'token-invalido' : globalThis.token,
	}).then((response) => { this.response = response })
	if (acesso === 'valido') return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(executar)
	return executar()
})
Then('os feriados possuem datas e anos corretos', function () {
	validarDatas(this.response, this.proximo)
})
Then('a consulta de feriados retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status >= 400) expect(this.response.body).to.have.property('detail').that.is.a('string').and.not.be.empty
})
When('envio {string} para a rota de feriados {string}', function (method, rota) {
	return cy.executar_feriados_ano({ method, proximo: rota === 'atual e proximo', token: null }).then((response) => { this.response = response })
})
When('comparo as duas consultas de feriados', function () {
	return cy.executar_feriados_ano({ token: null }).then((response) => {
		this.datasAtuais = validarDatas(response, false)
		return cy.executar_feriados_ano({ proximo: true, token: null })
	}).then((response) => { this.datasComProximo = validarDatas(response, true) })
})
Then('os feriados do ano atual coincidem nas duas rotas', function () {
	const ano = this.datasAtuais[0].slice(0, 4)
	expect(this.datasComProximo.filter((data) => data.startsWith(ano + '-'))).to.deep.eq(this.datasAtuais)
})
