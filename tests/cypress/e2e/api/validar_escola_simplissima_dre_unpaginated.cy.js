/// <reference types='cypress' />

describe('Validar rotas de Escolas Simplíssima Com EOL da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/escolas-simplissima-com-dre-unpaginated/', () => {
		it('Validar GET de Escolas Simplissima com DRE Unpaginated com UUID válido', () => {
			var uuid = '141af3ae-7fc1-4850-9da3-f3ecf224d270'
			cy.consultar_escola_simplissima_dre_unpaginated_por_uuid(uuid).then(
				(response) => {
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
				},
			)
		})

		it('Validar GET de Escolas Simplissima com DRE Unpaginated com UUID inválido', () => {
			var uuid = '141af3ae-7fc1-4850-9da3-f3ecf224d271'
			cy.consultar_escola_simplissima_dre_unpaginated_por_uuid(uuid).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})
	})
})
