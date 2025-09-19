/// <reference types='cypress' />

describe('Validar rotas de dashboard de produtos da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/dashboard-produtos/', () => {
		it('Validar GET de produtos aguardando análise reclamação com sucesso', () => {
			cy.consultar_aguardando_analise_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos não homologados', () => {
			cy.consultar_nao_homologados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de questionamento da Codae', () => {
			cy.consultar_questionamento_codae().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos suspensos', () => {
			cy.consultar_suspensos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de produtos homologados', () => {
			cy.consultar_homologados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de correção de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_correcao_produtos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de aguardando amostra de análise sensorial de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_aguardando_amostra_analise_sensorial().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})

		it('Validar GET com sucesso de aguardando homologação de produtos', () => {
			usuario = Cypress.config('usuario_gpcodae')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_pendente_homologacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('marca_produto').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('fabricante_produto')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('status').that.exist
					.and.is.not.empty
				expect(response.body.results[0]).to.have.property('id_externo').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('log_mais_recente')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'nome_usuario_log_de_reclamacao',
				).that.exist
				expect(response.body.results[0]).to.have.property('qtde_reclamacoes')
					.that.exist
				expect(response.body.results[0]).to.have.property(
					'qtde_questionamentos',
				).that.exist
				expect(response.body.results[0]).to.have.property(
					'tem_vinculo_produto_edital_suspenso',
				).that.exist
				expect(response.body.results[0])
					.to.have.property('produto_editais')
					.to.be.an('array')
				expect(response.body.results[0]).to.have.property('tem_copia').that
					.exist
			})
		})
	})
})
