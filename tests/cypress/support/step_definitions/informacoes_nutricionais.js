import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['tipo_nutricional', 'eh_dependente', 'nome', 'uuid', 'medida', 'eh_fixo']
Given('que estou autenticado como CODAE para consultar informacoes nutricionais', () => {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto a lista de informacoes nutricionais', function () {
	return cy.consultar_informacoes_nutricionais('').then((response) => { this.response = response })
})
When('consulto uma informacao nutricional existente por UUID', function () {
	return cy.consultar_informacoes_nutricionais('').then((lista) => {
		expect(lista.status).to.eq(200)
		expect(lista.body.results, 'informacao nutricional disponivel em QA').to.be.an('array').and.not.be.empty
		this.informacaoReferencia = lista.body.results[0]
		return cy.consultar_informacoes_nutricionais(this.informacaoReferencia.uuid)
			.then((response) => { this.response = response })
	})
})
When('consulto uma informacao nutricional por UUID invalido', function () {
	return cy.consultar_informacoes_nutricionais('3ac751ee-f95d-4d5b-80da-437506b1906j')
		.then((response) => { this.response = response })
})
When('consulto as informacoes nutricionais agrupadas', function () {
	return cy.consultar_informacoes_nutricionais_agrupadas().then((response) => {
		this.response = response
	})
})
When('consulto as informacoes nutricionais ordenadas', function () {
	return cy.consultar_informacoes_nutricionais_ordenadas().then((response) => {
		this.response = response
	})
})
function validarInformacao(item) {
	expect(item).to.include.all.keys(...campos)
	expect(item.tipo_nutricional).to.include.all.keys('nome', 'uuid')
	expect(item.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(item.nome).to.be.a('string').and.not.be.empty
	expect(item.medida).to.be.a('string')
	for (const campo of ['eh_dependente', 'eh_fixo', 'ativo']) expect(item[campo], campo).to.be.a('boolean')
}
Then('a lista de informacoes nutricionais retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach(validarInformacao)
})
Then('a informacao nutricional retorna os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	validarInformacao(this.response.body)
	expect(this.response.body).to.deep.eq(this.informacaoReferencia)
})
Then('a informacao nutricional retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('as informacoes agrupadas retornam dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	const nomes = this.response.body.results.map((grupo) => grupo.nome)
	expect(new Set(nomes).size).to.eq(nomes.length)
	this.response.body.results.forEach((grupo) => {
		expect(grupo.nome).to.be.a('string').and.not.be.empty
		expect(grupo.informacoes_nutricionais).to.be.an('array').and.not.be.empty
		grupo.informacoes_nutricionais.forEach((item) => {
			expect(item).to.include.all.keys('nome', 'uuid', 'medida')
		})
	})
})
Then('as informacoes ordenadas retornam dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach(validarInformacao)
	const ordem = ['VALOR ENERGÉTICO', 'CARBOIDRATOS', 'AÇÚCARES TOTAIS', 'AÇÚCARES ADICIONADOS', 'PROTEÍNAS', 'GORDURAS TOTAIS', 'GORDURAS SATURADAS', 'GORDURAS TRANS', 'FIBRA ALIMENTAR', 'SÓDIO']
	const posicoes = this.response.body.results.map((item) => {
		const indice = ordem.indexOf(item.nome)
		return indice === -1 ? ordem.length : indice
	})
	expect(posicoes).to.deep.eq([...posicoes].sort((a, b) => a - b))
})

When('executo {string} em informacoes nutricionais na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = { method, caminho: rota === 'principal' ? '' : rota }
	const executar = () => cy.executar_informacoes_nutricionais(opcoes).then((response) => { this.response = response })
	if (acesso === 'autenticado') return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(executar)
	cy.clearCookies()
	return cy.executar_informacoes_nutricionais({ ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
		.then((response) => { this.response = response })
})

Then('informacoes nutricionais retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('consulto informacoes nutricionais na rota {string} com ativo {string}', function (rota, ativo) {
	this.ativoNutricional = ativo === 'true'
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(() =>
		cy.executar_informacoes_nutricionais({ caminho: rota === 'principal' ? '' : rota, qs: { ativo } }),
	).then((response) => { this.response = response })
})

Then('as informacoes nutricionais correspondem ao filtro ativo', function () {
	expect(this.response.body.results).to.be.an('array')
	this.response.body.results.forEach((item) => {
		validarInformacao(item)
		expect(item.ativo).to.eq(this.ativoNutricional)
	})
})

Then('as informacoes agrupadas correspondem ao filtro ativo', function () {
	expect(this.response.body.results).to.be.an('array')
	const agrupadas = this.response.body.results.flatMap((grupo) => grupo.informacoes_nutricionais.map((item) => item.uuid))
	return cy.executar_informacoes_nutricionais({ caminho: 'ordenadas/', qs: { ativo: String(this.ativoNutricional) } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(agrupadas.sort()).to.deep.eq(response.body.results.map((item) => item.uuid).sort())
	})
})

When('consulto informacoes nutricionais com limite {int} e deslocamento {int}', function (limit, offset) {
	this.limiteNutricional = limit
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(() =>
		cy.executar_informacoes_nutricionais({ qs: { limit, offset } }),
	).then((response) => { this.response = response })
})

Then('a paginacao de informacoes nutricionais respeita o limite', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(this.limiteNutricional)
	this.response.body.results.forEach(validarInformacao)
})
