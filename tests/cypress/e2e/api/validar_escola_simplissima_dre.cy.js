/// <reference types='cypress' />

describe('Validar rotas de Escolas Simplíssima Com DRE da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/escolas-simplissima-com-dre/', () => {
		it('Validar GET com sucesso de Escolas Simplissima com DRE', () => {
			cy.consultar_escola_simplissima_dre().then((response) => {
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

		it('Validar GET de Escolas Simplissima com DRE com UUID válido', () => {
			var uuid = '141af3ae-7fc1-4850-9da3-f3ecf224d270'
			cy.consultar_escola_simplissima_dre_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('nome')
				expect(response.body)
					.to.have.property('diretoria_regional')
					.to.be.an('object')
				expect(response.body).to.have.property('codigo_eol')
				expect(response.body).to.have.property('quantidade_alunos')
				expect(response.body).to.have.property('lote_obj')
				expect(response.body).to.have.property('tipo_unidade')
			})
		})

		it('Validar GET de Escolas Simplissima com DRE com UUID inválido', () => {
			var uuid = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
			cy.consultar_escola_simplissima_dre_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
