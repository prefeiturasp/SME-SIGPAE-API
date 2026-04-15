/// <reference types='cypress' />

describe('Validar rotas de Escolas Simplíssima Com EOL da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/escolas-simplissima-com-eol/', () => {
		it('Validar GET com sucesso de Escolas Simplissima com DRE', () => {
			cy.consultar_escola_simplissima_eol().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('codigo_eol')
				expect(response.body.results[0]).property('codigo_eol_escola')
				expect(response.body.results[0]).property('tipo_gestao')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET de Escolas Simplissima com EOL com UUID válido', () => {
			var uuid = '141af3ae-7fc1-4850-9da3-f3ecf224d270'
			cy.consultar_escola_simplissima_eol_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('codigo_eol')
				expect(response.body).to.have.property('codigo_eol_escola')
				expect(response.body).to.have.property('tipo_gestao')
			})
		})

		it('Validar GET de Escolas Simplissima com EOL com UUID inválido', () => {
			var uuid = '141af3ae-7fc1-4850-9da3-f3ecf224d271'
			cy.consultar_escola_simplissima_eol_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
