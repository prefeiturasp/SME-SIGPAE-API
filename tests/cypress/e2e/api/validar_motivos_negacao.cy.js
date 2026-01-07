describe('Validar rotas de Motivos de Negacao da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/motivos-negacao/', () => {
		it('Validar GET com sucesso de Motivos de Negacao', () => {
			cy.consultar_motivos_negacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('id')
				expect(response.body[0]).to.have.property('descricao')
				expect(response.body[0]).to.have.property('processo')
			})
		})

		it('Validar GET com sucesso de Motivos de Negacao por Processo', () => {
			var processo = Math.random() < 0.5 ? 'INCLUSAO' : 'CANCELAMENTO' // NOSONAR
			var param = '?processo=' + processo
			cy.consultar_motivos_negacao_por_processo(param).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('id')
				expect(response.body[0]).to.have.property('descricao')
				expect(response.body[0]).to.have.property('processo').to.eq(processo)
			})
		})

		it('Validar GET de Motivos de Negacao com Processo Inválido', () => {
			var param = '?processo=NomeInvalidoParaoTeste'
			cy.consultar_motivos_negacao_por_processo(param).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.have.property('processo')
				expect(response.body.processo).to.be.an('array')
				expect(response.body.processo).to.eql([
					'Faça uma escolha válida. NomeInvalidoParaoTeste não é uma das escolhas disponíveis.',
				])
			})
		})

		it('Validar GET com sucesso de Motivos de Negacao Com ID Válido', () => {
			var id_response = ''
			cy.consultar_motivos_negacao().then((response) => {
				expect(response.status).to.eq(200)
				id_response = response.body[0].id

				cy.consultar_motivos_negacao_por_id(id_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('id').eq(id_response)
					expect(response.body).to.have.property('descricao')
					expect(response.body).to.have.property('processo')
				})
			})
		})

		it('Validar GET de Motivos de Negacao Com ID Inválido', () => {
			var id = '3ac751e'
			cy.consultar_motivos_negacao_por_id(id).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
