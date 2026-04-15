/// <reference types='cypress' />

<<<<<<< HEAD
describe('Validar rotas de Escolas Simpli­ssima da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
describe('Validar rotas de Escolas SimplÃ­ssima da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/escolas-simplissima/', () => {
		it('Validar GET com sucesso de Escolas Simplissima', () => {
			cy.consultar_escola_simplissima().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('uuid')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).to.have.property('codigo_eol')
			})
		})

		it('Validar GET de Escolas Simplissima com UUID vÃ¡lido', () => {
			var uuid = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
			cy.consultar_escola_simplissima_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body[0]).to.have.property('uuid')
				expect(response.body[0]).to.have.property('nome')
				expect(response.body[0]).to.have.property('codigo_eol')
			})
		})

		it('Validar GET com sucesso de Escolas Simplissima por DRE', () => {
			var uuid = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
			cy.consultar_escola_simplissima_por_dre(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body[0]).to.have.property('uuid')
				expect(response.body[0]).to.have.property('nome')
				expect(response.body[0]).to.have.property('codigo_eol')
				expect(response.body[0]).to.have.property('diretoria_regional')
				expect(response.body[0].diretoria_regional)
					.to.have.property('uuid')
					.to.eq(uuid)
			})
		})
	})
})

