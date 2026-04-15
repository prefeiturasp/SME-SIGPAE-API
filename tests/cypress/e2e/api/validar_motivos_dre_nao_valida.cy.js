describe('Validar rotas de Motivos DRE Não Válida da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/motivos-dre-nao-valida/', () => {
		it('Validar GET com sucesso de Motivos DRE Não Válida', () => {
			cy.consultar_motivos_dre_nao_valida().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de Motivos DRE Não Válida Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_motivos_dre_nao_valida().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_motivos_dre_nao_valida_por_uuid(uuid_response).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('nome')
						expect(response.body).to.have.property('uuid').eq(uuid_response)
					},
				)
			})
		})

		it('Validar GET de Motivos DRE Não Válida Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_motivos_dre_nao_valida_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
