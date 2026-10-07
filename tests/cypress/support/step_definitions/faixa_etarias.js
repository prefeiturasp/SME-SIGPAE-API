import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar faixas etarias', () => {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto as faixas etarias', function () {
	return cy.consultar_faixas_etarias().then((response) => { this.response = response })
})
Then('a consulta de faixas etarias deve retornar status 200 e dados paginados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((faixa) => {
		expect(faixa).to.include.all.keys('uuid', 'inicio', 'fim')
		expect(faixa.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
		expect(Number.isInteger(faixa.inicio)).to.eq(true)
		expect(Number.isInteger(faixa.fim)).to.eq(true)
		expect(faixa.inicio).to.be.at.least(0).and.be.lessThan(faixa.fim)
		expect(faixa.fim).to.be.at.most(100)
	})
})
When('consulto faixas etarias com limite {int}', function (limit) {
	this.limite = limit
	return cy.executar_faixas_etarias({ qs: { limit } }).then((response) => { this.response = response })
})
Then('a pagina de faixas etarias respeita o limite', function () {
	expect(this.response.body.results).to.have.length(Math.min(this.limite, this.response.body.count))
})
When('consulto a segunda faixa etaria por deslocamento', function () {
	return cy.executar_faixas_etarias({ qs: { limit: 2 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.have.length(2)
		this.segunda = response.body.results[1].uuid
		return cy.executar_faixas_etarias({ qs: { limit: 1, offset: 1 } })
	}).then((response) => { this.response = response })
})
Then('a pagina retorna somente a segunda faixa etaria', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.have.length(1)
	expect(this.response.body.results[0].uuid).to.eq(this.segunda)
})
When('consulto faixas etarias depois do total', function () {
	return cy.executar_faixas_etarias({ qs: { limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		return cy.executar_faixas_etarias({ qs: { limit: 1, offset: response.body.count } })
	}).then((response) => { this.response = response })
})
Then('a pagina de faixas etarias esta vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.next).to.eq(null)
})
When('executo {string} em faixas etarias com acesso {string}', function (method, acesso) {
	return cy.executar_faixas_etarias({ method, body: method === 'GET' ? undefined : {},
		token: acesso === 'ausente' ? null : acesso === 'invalido' ? 'token-invalido' : globalThis.token,
	}).then((response) => { this.response = response })
})
Then('faixas etarias retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
When('cadastro faixas etarias com dados invalidos {string}', function (caso) {
	const faixa = { inicio: 0, fim: 12 }
	const body = { justificativa: 'Validacao automatizada de dados invalidos', faixas_etarias_ativadas: [faixa] }
	switch (caso) {
	case 'sem justificativa': delete body.justificativa; break
	case 'justificativa vazia': body.justificativa = ''; break
	case 'sem faixas': delete body.faixas_etarias_ativadas; break
	case 'faixas nulas': body.faixas_etarias_ativadas = null; break
	case 'faixas tipo invalido': body.faixas_etarias_ativadas = 'invalido'; break
	case 'sem inicio': delete faixa.inicio; break
	case 'sem fim': delete faixa.fim; break
	case 'inicio texto': faixa.inicio = 'abc'; break
	case 'fim texto': faixa.fim = 'abc'; break
	case 'inicio negativo': faixa.inicio = -1; break
	case 'fim acima do limite': faixa.fim = 101; break
	case 'inicio igual ao fim': faixa.inicio = 12; break
	case 'inicio maior que fim': faixa.inicio = 13; break
	default: throw new Error(`Caso desconhecido: ${caso}`)
	}
	return cy.executar_faixas_etarias({ method: 'POST', body }).then((response) => { this.response = response })
})
Then('a resposta de faixas etarias informa erro no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property(campo)
	expect(this.response.body[campo]).to.not.be.empty
})
Given('que o ambiente de faixas etarias e descartavel', function () {
	// Este POST desativa TODAS as faixas existentes. Habilitar somente em banco descartavel.
	if (Cypress.env('faixas_etarias_ambiente_descartavel') !== true) this.skip()
	expect(new URL(Cypress.config('baseUrl')).hostname).not.to.eq('qa-sigpae.sme.prefeitura.sp.gov.br')
})
When('substituo as faixas etarias por dados validos', function () {
	this.novasFaixas = [{ inicio: 0, fim: 12 }, { inicio: 12, fim: 100 }]
	return cy.executar_faixas_etarias({ method: 'POST', body: {
		justificativa: 'Teste automatizado em ambiente descartavel', faixas_etarias_ativadas: this.novasFaixas,
	} }).then((response) => { this.response = response })
})
Then('as novas faixas etarias ficam ativas', function () {
	expect(this.response.status).to.eq(201)
	return cy.consultar_faixas_etarias().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.count).to.eq(2)
		expect(response.body.results.map(({ inicio, fim }) => ({ inicio, fim })).sort((a, b) => a.inicio - b.inicio)).to.deep.eq(this.novasFaixas)
	})
})
