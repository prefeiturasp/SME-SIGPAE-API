/// <reference types='cypress' />

describe('Validar rotas de dashboard de produtos da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
	const usuario_dashboard = Cypress.env('usuario_coordenador_logistica')
	const senha_dashboard = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail')
	}

	context('Casos de teste para a rota api/dashboard-produtos/', () => {
		it('Validar GET paginado do dashboard de produtos com sucesso', () => {
			const pageSize = 1

			cy.consultar_dashboard_produtos({
				page: 1,
				pageSize,
				usuario: usuario_dashboard,
				senha: senha_dashboard,
			}).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.have.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number').and.be.greaterThan(0)
				expect(response.body.results).to.be.an('array').and.have.length(pageSize)

				const produto = response.body.results[0]
				expect(produto).to.include.all.keys(
					'uuid',
					'nome_produto',
					'marca_produto',
					'fabricante_produto',
					'status',
					'id_externo',
					'log_mais_recente',
					'nome_usuario_log_de_reclamacao',
					'qtde_reclamacoes',
					'qtde_questionamentos',
					'tem_vinculo_produto_edital_suspenso',
					'produto_editais',
				)
				expect(produto.uuid).to.be.a('string').and.not.be.empty
				expect(produto.produto_editais).to.be.an('array')
			})
		})

		it('Validar GET do dashboard de produtos sem autenticacao', () => {
			cy.consultar_dashboard_produtos({ page: 1, pageSize: 1 }).then(
				(response) => {
					expect(response.status, JSON.stringify(response.body)).to.eq(401)
					expect(response.body.detail).to.be.a('string').and.not.be.empty
				},
			)
		})
		it('Validar GET de produtos aguardando analise reclamacao com sucesso', () => {
			cy.consultar_aguardando_analise_reclamacao().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos nao homologados', () => {
			cy.consultar_nao_homologados().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de questionamento da Codae', () => {
			cy.consultar_questionamento_codae().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos suspensos', () => {
			cy.consultar_suspensos().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos homologados', () => {
			cy.consultar_homologados().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de correcao de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_correcao_produtos().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de aguardando amostra de analise sensorial de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_aguardando_amostra_analise_sensorial().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(primeiroResultado).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de aguardando homologacao de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_pendente_homologacao().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('nome_produto').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca_produto').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('fabricante_produto').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('id_externo').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('log_mais_recente').that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('nome_usuario_log_de_reclamacao').that.exist
				expect(primeiroResultado).to.have.property('qtde_reclamacoes').that.exist
				expect(primeiroResultado).to.have.property('qtde_questionamentos').that.exist
				expect(primeiroResultado).to.have.property('tem_vinculo_produto_edital_suspenso').that.exist
				expect(primeiroResultado).to.have.property('produto_editais').to.be.an('array')
				expect(primeiroResultado).to.have.property('tem_copia').that.exist
			})
		})
	})
})
