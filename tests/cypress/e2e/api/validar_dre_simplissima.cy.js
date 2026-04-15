/// <reference types='cypress' />

describe('Validar rotas de Diretorias Regionais da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_dre')
	var senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/diretorias-regionais-simplissima/', () => {
		it('Validar GET com sucesso de Diretorias Regionais Simplissima', () => {
			cy.consultar_dre_simplissima().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('uuid')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).to.have.property('codigo_eol')
				expect(response.body.results[0]).to.have.property('iniciais')
				expect(response.body.results[0]).to.have.property(
					'acesso_modulo_medicao_inicial',
				)
			})
		})

		it('Validar GET de Diretorias Regionais Simplissima com UUID vÃ¡lido', () => {
			var uuid = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
			cy.consultar_dre_simplissima_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('nome')
				expect(response.body).to.have.property('codigo_eol')
				expect(response.body).to.have.property('iniciais')
				expect(response.body).to.have.property('acesso_modulo_medicao_inicial')
			})
		})

		it('Validar GET de Diretorias Regionais Simplissima com UUID invÃ¡lido', () => {
			var uuid = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
			cy.consultar_dre_simplissima_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Lista Completa de Diretorias Regionais Simplissima', () => {
			cy.consultar_lista_completa_dre_simplissima().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('uuid')
				expect(response.body.results[0]).to.have.property('iniciais')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).to.have.property('codigo_eol')
			})
		})
	})
})

