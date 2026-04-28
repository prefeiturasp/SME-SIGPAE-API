/// <reference types='cypress' />

describe('Validar rotas de Fabricantes da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail').that.is.not.empty
	}

	function validarListaResultados(response) {
		expect(response.body).to.have.property('results')
		expect(response.body.results).to.be.an('array')

		if (response.body.results.length > 0) {
			expect(response.body.results[0]).to.have.property('nome')
			expect(response.body.results[0]).to.have.property('uuid')
		}
	}

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/fabricantes/', () => {
		it('Validar GET com sucesso de Fabricantes', () => {
			cy.consultar_fabricantes('').then((response) => {
				expect(response.status).to.eq(200)
				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Fabricantes com UUID valido', () => {
			cy.consultar_fabricantes('79a6ac62-559b-478d-a1e8-f07298d2bbcb').then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('nome')
			})
		})

		it('Validar GET de Fabricantes com UUID invalido', () => {
			cy.consultar_fabricantes('79a6ac62-559b-478d-a1e8-f07298d2aaaa').then((response) => {
				expect([403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes', () => {
			cy.consultar_fabricantes_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Avaliar Reclamacao', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Nova Reclamacao', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder Reclamacao', () => {
			cy.consultar_lista_nomes_responder_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder Reclamacao Escola', () => {
			usuario = Cypress.config('usuario_diretor_ue')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_lista_nomes_responder_reclamacao_escola().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				validarListaResultados(response)
			})
		})

		it('Validar GET com sucesso de Lista Nomes Responder Reclamacao Nutrisupervisor', () => {
			cy.consultar_nomes_responder_reclamacao_nutrisupervisao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Unicos', () => {
			cy.consultar_lista_nomes_unicos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})
