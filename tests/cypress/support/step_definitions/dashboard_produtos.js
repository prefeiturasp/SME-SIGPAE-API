import { When, Then } from 'cypress-cucumber-preprocessor/steps'
const comandos = {
	aguardando_analise_reclamacao: 'consultar_aguardando_analise_reclamacao',
	nao_homologados: 'consultar_nao_homologados',
	questionamento_codae: 'consultar_questionamento_codae',
	suspensos: 'consultar_suspensos',
	homologados: 'consultar_homologados',
	correcao_produtos: 'consultar_correcao_produtos',
	aguardando_amostra_analise_sensorial: 'consultar_aguardando_amostra_analise_sensorial',
	pendente_homologacao: 'consultar_pendente_homologacao',
}
const camposProduto = [
	'uuid', 'nome_produto', 'marca_produto', 'fabricante_produto', 'status',
	'id_externo', 'log_mais_recente', 'nome_usuario_log_de_reclamacao',
	'qtde_reclamacoes', 'qtde_questionamentos',
	'tem_vinculo_produto_edital_suspenso', 'produto_editais', 'tem_copia',
]
When('consulto uma pagina do dashboard de produtos autenticado', function () {
	cy.consultar_dashboard_produtos({
		page: 1, pageSize: 1,
		usuario: Cypress.env('usuario_coordenador_logistica'),
		senha: Cypress.env('senha'),
	}).then((response) => { this.response = response })
})
When('consulto o dashboard de produtos sem autenticacao', function () {
	cy.consultar_dashboard_produtos({ page: 1, pageSize: 1 }).then((response) => {
		this.response = response
	})
})
When('consulto a fila {string} do dashboard com o perfil {string}', function (fila, perfil) {
	cy.autenticar_login(Cypress.config(`usuario_${perfil}`), Cypress.config('senha'))
	cy[comandos[fila]]().then((response) => { this.response = response })
})
Then('o dashboard retorna status 200 e um produto valido', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.have.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.be.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.have.length(1)
	expect(this.response.body.results[0]).to.include.all.keys(...camposProduto)
	expect(this.response.body.results[0].uuid).to.be.a('string').and.not.be.empty
	expect(this.response.body.results[0].produto_editais).to.be.an('array')
})
Then('o dashboard retorna status 401', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(401)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('a fila do dashboard retorna status permitido e dados validos', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		expect(this.response.body).to.have.property('detail')
		return
	}
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (!this.response.body.results.length) return
	const produto = this.response.body.results[0]
	expect(produto).to.include.all.keys(...camposProduto)
	for (const campo of [
		'uuid', 'nome_produto', 'marca_produto', 'fabricante_produto',
		'status', 'id_externo', 'log_mais_recente',
	]) expect(produto[campo]).to.exist.and.not.be.empty
	expect(produto.produto_editais).to.be.an('array')
})

When('consulto um produto existente pelo UUID no dashboard', function () {
	cy.autenticar_login(Cypress.env('usuario_coordenador_logistica'), Cypress.env('senha'))
	cy.consultar_dashboard_produtos({ pageSize: 1, usuario: Cypress.env('usuario_coordenador_logistica'), senha: Cypress.env('senha') }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.uuidDashboard = response.body.results[0].uuid
		cy.executar_dashboard_produtos('GET', this.uuidDashboard).then((resposta) => { this.response = resposta })
	})
})

Then('o detalhe do dashboard corresponde ao produto consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys(...camposProduto)
	expect(this.response.body.uuid).to.eq(this.uuidDashboard)
	expect(this.response.body.nome_produto).to.be.a('string').and.not.be.empty
	expect(this.response.body.produto_editais).to.be.an('array')
})

When('executo {string} no dashboard com UUID inexistente', function (metodo) {
	cy.autenticar_login(Cypress.env('usuario_coordenador_logistica'), Cypress.env('senha'))
	cy.executar_dashboard_produtos(metodo, '00000000-0000-0000-0000-000000000000', ['PUT', 'PATCH'].includes(metodo) ? {} : undefined).then((response) => { this.response = response })
})

When('executo {string} no dashboard sem autenticacao', function (metodo) {
	cy.clearCookies()
	cy.executar_dashboard_produtos(metodo, metodo === 'POST' ? '' : '00000000-0000-0000-0000-000000000000', ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined, false).then((response) => { this.response = response })
})

When('cadastro no dashboard um status invalido', function () {
	cy.autenticar_login(Cypress.env('usuario_coordenador_logistica'), Cypress.env('senha'))
	cy.executar_dashboard_produtos('POST', '', { status: 'STATUS_INEXISTENTE', tem_vinculo_produto_edital_suspenso: false }).then((response) => { this.response = response })
})

Then('a operacao do dashboard retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('o dashboard informa erro no campo status', function () {
	expect(this.response.body.status).to.be.an('array').and.not.be.empty
})
