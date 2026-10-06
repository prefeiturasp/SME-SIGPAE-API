import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function referencia(contexto) {
	return cy.consultar_escola_simplissima_dre().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		contexto.escola = response.body.results[0]
	})
}
function validarEscola(escola) {
	expect(escola).to.include.all.keys('uuid', 'nome', 'codigo_eol', 'diretoria_regional', 'quantidade_alunos')
	expect(escola.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(escola.nome).to.be.a('string')
	expect(escola.codigo_eol).to.be.a('string')
	expect(escola.quantidade_alunos).to.be.a('number').and.be.at.least(0)
	if (escola.diretoria_regional !== null) {
		expect(escola.diretoria_regional).to.include.all.keys('uuid', 'nome', 'codigo_eol')
	}
}
Given('que estou autenticado como CODAE para consultar escolas com DRE sem paginacao', () => {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
Then('a escola simplissima com DRE sem paginacao retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})

When('consulto escolas com DRE sem paginacao na rota {string}', function (rota) {
	return cy.executar_escolas_dre_sem_paginacao({ caminho: rota === 'lista' ? '' : 'terc-total/' }).then((response) => { this.response = response })
})
When('consulto detalhe sem paginacao com UUID {string}', function (uuid) {
	if (uuid === 'existente') {
		return referencia(this).then(() => cy.executar_escolas_dre_sem_paginacao({ caminho: this.escola.uuid + '/' })).then((response) => { this.response = response })
	}
	return cy.executar_escolas_dre_sem_paginacao({ caminho: uuid + '/' }).then((response) => { this.response = response })
})
Then('o detalhe sem paginacao corresponde a escola consultada', function () {
	expect(this.response.status).to.eq(200)
	validarEscola(this.response.body)
	expect(this.response.body.uuid).to.eq(this.escola.uuid)
})
Then('a resposta sem paginacao contem uma lista de escolas', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	this.response.body.slice(0, 10).forEach(validarEscola)
})
When('executo {string} na rota sem paginacao {string} com acesso {string}', function (method, rota, acesso) {
	return referencia(this).then(() => cy.executar_escolas_dre_sem_paginacao({
		method,
		caminho: rota === 'detalhe' ? this.escola.uuid + '/' : rota === 'terc-total' ? 'terc-total/' : '',
		token: acesso === 'ausente' ? null : acesso === 'invalido' ? 'token-invalido' : globalThis.token,
	})).then((response) => { this.response = response })
})
When('filtro terc-total por escola existente', function () {
	return cy.executar_escolas_dre_sem_paginacao({ caminho: 'terc-total/' }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.be.an('array').and.not.be.empty
		this.escola = response.body[0]
		return cy.executar_escolas_dre_sem_paginacao({ caminho: 'terc-total/', qs: { escola: this.escola.uuid } })
	}).then((response) => { this.response = response })
})
Then('terc-total retorna somente a escola filtrada', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.have.length(1)
	expect(this.response.body[0].uuid).to.eq(this.escola.uuid)
})
When('filtro terc-total pelo campo {string} inexistente', function (campo) {
	const valor = campo === 'nome_edital' ? 'EDITAL-INEXISTENTE-CYPRESS-000000' : '00000000-0000-0000-0000-000000000000'
	return cy.executar_escolas_dre_sem_paginacao({ caminho: 'terc-total/', qs: { [campo]: valor } }).then((response) => { this.response = response })
})
Then('terc-total retorna lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.deep.eq([])
})
