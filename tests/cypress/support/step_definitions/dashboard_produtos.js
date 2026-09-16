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
