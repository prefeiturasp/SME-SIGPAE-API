/// <reference types='cypress' />

describe('Validar rotas de Fabricantes da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/fabricantes/', () => {
		it('Validar GET com sucesso de Fabricantes', () => {
			var uuid = ''
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes com UUID vÃ¡lido', () => {
			var uuid = '79a6ac62-559b-478d-a1e8-f07298d2bbcb'
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('nome')
			})
		})

		it('Validar GET de Fabricantes com UUID invÃ¡lido', () => {
			var uuid = '79a6ac62-559b-478d-a1e8-f07298d2aaaa'
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes', () => {
			cy.consultar_fabricantes_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Avaliar ReclamaÃ§Ã£o', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Nova ReclamaÃ§Ã£o', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder ReclamaÃ§Ã£o', () => {
			cy.consultar_lista_nomes_responder_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder ReclamaÃ§Ã£o Escola', () => {
			usuario = Cypress.env('usuario_diretor_ue')
			senha = Cypress.env('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_lista_nomes_responder_reclamacao_escola().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Responder ReclamaÃ§Ã£o Nutrisupervisor', () => {
			cy.consultar_nomes_responder_reclamacao_nutrisupervisao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Ãšnicos', () => {
			cy.consultar_lista_nomes_unicos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})

