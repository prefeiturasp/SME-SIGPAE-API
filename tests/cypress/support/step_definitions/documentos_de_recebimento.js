import { When, Then } from 'cypress-cucumber-preprocessor/steps'
const parametros = { limit: 10, offset: 0 }
function autenticar(usuario) {
	cy.autenticar_login(Cypress.env(usuario), Cypress.env('senha'))
}
When('consulto documentos de recebimento com usuario autorizado', function () {
	autenticar('usuario_coordenador_codae_dilog_logistica')
	cy.consultar_documentos_de_recebimento(parametros).then((response) => {
		this.response = response
	})
})
When('consulto documentos de recebimento com usuario CODAE', function () {
	autenticar('usuario_codae')
	cy.consultar_documentos_de_recebimento(parametros).then((response) => {
		this.response = response
	})
})
When('tento gerar documentos de recebimento com usuario CODAE', function () {
	autenticar('usuario_codae')
	cy.gerar_documentos_de_recebimento().then((response) => { this.response = response })
})
Then('a consulta de documentos retorna status 200 e dados paginados validos', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number')
	expect(this.response.body.results).to.be.an('array')
	this.response.body.results.forEach((documento) => {
		expect(documento).to.include.all.keys(
			'uuid', 'numero_cronograma', 'numero_laudo', 'pregao_chamada_publica',
			'nome_produto', 'programa_leve_leite', 'status', 'criado_em',
		)
		expect(documento.uuid).to.be.a('string').and.not.be.empty
		expect(documento.numero_cronograma).to.be.a('string')
		expect(documento.numero_laudo).to.be.a('string')
		expect(documento.pregao_chamada_publica).to.be.a('string')
		expect(documento.nome_produto).to.be.a('string').and.not.be.empty
		expect(documento.programa_leve_leite).to.be.a('boolean')
		expect(documento.status).to.be.a('string').and.not.be.empty
		expect(documento.criado_em).to.be.a('string').and.not.be.empty
	})
})
Then('a consulta de documentos retorna status 403 e mensagem de permissao', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('a geracao de documentos retorna status 403 e mensagem de permissao', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('consulto documentos de recebimento pela operacao {string}', function (operacao) {
	autenticar('usuario_coordenador_codae_dilog_logistica')
	this.operacaoDocumentos = operacao
	if (operacao === 'detalhe') {
		cy.consultar_documentos_de_recebimento({ limit: 1, offset: 0 }).then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results).to.be.an('array').and.not.be.empty
			this.uuidDocumento = response.body.results[0].uuid
			cy.executar_documentos_recebimento({ caminho: this.uuidDocumento }).then((resposta) => { this.response = resposta })
		})
	} else {
		cy.executar_documentos_recebimento({ caminho: operacao, qs: { limit: 1, offset: 0 } }).then((response) => { this.response = response })
	}
})
Then('a consulta complementar de documentos retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	if (this.operacaoDocumentos === 'detalhe') expect(this.response.body.uuid).to.eq(this.uuidDocumento)
	else {
		expect(this.response.body.results).to.be.an('array')
		if (this.operacaoDocumentos === 'listagem-relatorio') expect(this.response.body.totalizadores).to.be.an('object')
	}
})
When('executo {string} em documentos na rota {string} com perfil {string}', function (metodo, rota, perfil) {
	const autenticado = perfil !== 'anonimo'
	if (autenticado) autenticar(perfil === 'qualidade' ? 'usuario_dilog_qualidade' : perfil === 'codae' ? 'usuario_codae' : 'usuario_coordenador_codae_dilog_logistica')
	else cy.clearCookies()
	const uuid = '00000000-0000-0000-0000-000000000000'
	const caminho = rota === 'listagem' ? '' : rota === 'detalhe' ? uuid : ['dashboard', 'exportar-excel', 'listagem-relatorio'].includes(rota) ? rota : `${uuid}/${rota}`
	cy.executar_documentos_recebimento({ metodo, caminho, autenticado, body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})
Then('a operacao complementar de documentos retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
