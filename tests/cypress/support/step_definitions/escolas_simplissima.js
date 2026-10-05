import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuidDre = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
Given('que estou autenticado como CODAE para consultar escolas simplissimas', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto a lista de escolas simplissimas', function () {
	cy.consultar_escola_simplissima().then((response) => { this.response = response })
})
When('consulto escolas simplissimas pelo UUID da DRE', function () {
	cy.consultar_escola_simplissima_por_uuid(uuidDre).then((response) => { this.response = response })
})
When('filtro escolas simplissimas pela DRE', function () {
	cy.consultar_escola_simplissima_por_dre(uuidDre).then((response) => { this.response = response })
})
Then('a lista de escolas simplissimas retorna dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol')
})
Then('a consulta por UUID retorna escolas simplissimas validas', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol')
})
Then('a consulta filtrada retorna escolas vinculadas a DRE', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((escola) => expect(escola.diretoria_regional.uuid).to.eq(uuidDre))
	expect(this.response.body.results[0].diretoria_regional.uuid).to.eq(uuidDre)
})

const uuidInexistente = '00000000-0000-0000-0000-000000000000'
function consultar(contexto, opcoes = {}) {
	return cy.executar_escolas_simplissimas({ token: globalThis.token, ...opcoes }).then((response) => { contexto.response = response })
}
function referencia(contexto) {
	return cy.executar_escolas_simplissimas({ token: globalThis.token, qs: { page: 1, page_size: 10 } }).then((response) => {
		expect(response.status).to.eq(200)
		contexto.escolaReferencia = response.body.results.find((e) => e.nome && e.codigo_eol && e.diretoria_regional)
		expect(contexto.escolaReferencia, 'Escola com nome, codigo EOL e DRE').to.exist
	})
}
When('consulto escolas simplissimas sem paginacao', function () {
	return referencia(this).then(() => consultar(this, { qs: { codigo_eol: this.escolaReferencia.codigo_eol } }))
})
When('consulto escolas simplissimas usando o filtro {string}', function (filtro) {
	this.filtroAplicado = filtro
	return referencia(this).then(() => {
		const e = this.escolaReferencia
		const filtros = {
			codigo_eol: { codigo_eol: e.codigo_eol },
			nome: { nome: e.nome },
			dre: { diretoria_regional__uuid: e.diretoria_regional.uuid },
			combinados: { codigo_eol: e.codigo_eol, nome: e.nome, diretoria_regional__uuid: e.diretoria_regional.uuid },
		}
		return consultar(this, { qs: { page: 1, page_size: 2, ...filtros[filtro] } })
	})
})
Then('escolas simplissimas respeita o filtro aplicado', function () {
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((e) => {
		if (['codigo_eol', 'combinados'].includes(this.filtroAplicado)) expect(e.codigo_eol).to.eq(this.escolaReferencia.codigo_eol)
		if (['nome', 'combinados'].includes(this.filtroAplicado)) expect(e.nome).to.eq(this.escolaReferencia.nome)
		if (['dre', 'combinados'].includes(this.filtroAplicado)) expect(e.diretoria_regional.uuid).to.eq(this.escolaReferencia.diretoria_regional.uuid)
	})
})
When('consulto escolas simplissimas com parametro {string} e valor {string}', function (campo, valor) {
	this.campoFiltro = campo
	return consultar(this, { qs: { page: 1, page_size: 2, [campo]: valor } })
})
Then('escolas simplissimas retorna lista vazia', function () {
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
})
Then('escolas simplissimas informa UUID de filtro invalido', function () {
	expect(this.response.body.diretoria_regional__uuid).to.be.an('array').and.not.be.empty
})
Then('escolas simplissimas retorna lista sem paginacao', function () {
	expect(this.response.body).to.have.all.keys('results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((e) => expect(e.codigo_eol).to.eq(this.escolaReferencia.codigo_eol))
})
When('consulto paginas consecutivas de escolas simplissimas', function () {
	return consultar(this, { qs: { page: 1, page_size: 2 } }).then(() => {
		expect(this.response.status).to.eq(200)
		expect(this.response.body.results).to.have.length(2)
		this.segundaEscola = this.response.body.results[1]
		this.totalEscolas = this.response.body.count
		return consultar(this, { qs: { page: 2, page_size: 1 } })
	})
})
Then('escolas simplissimas respeita tamanho e pagina', function () {
	expect(this.response.body.count).to.eq(this.totalEscolas)
	expect(this.response.body.results).to.deep.eq([this.segundaEscola])
})
When('consulto pagina alem do total de escolas simplissimas', function () {
	return consultar(this, { qs: { page: 1, page_size: 1 } }).then(() => {
		expect(this.response.status).to.eq(200)
		return consultar(this, { qs: { page: this.response.body.count + 1, page_size: 1 } })
	})
})
When('consulto escolas simplissimas pela DRE {string}', function (uuid) {
	return consultar(this, { caminho: uuid })
})
Then('escolas simplissimas retorna agrupamento vazio', function () {
	expect(this.response.body).to.deep.eq([])
})
When('executo {string} em escolas simplissimas na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	if (acesso !== 'autenticado') cy.clearCookies()
	return consultar(this, { metodo, caminho: rota === 'listagem' ? '' : uuidInexistente, qs: { page: 1, page_size: 1 }, token: acesso === 'autenticado' ? globalThis.token : acesso === 'token invalido' ? 'token-invalido' : undefined })
})
Then('a operacao de escolas simplissimas retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
