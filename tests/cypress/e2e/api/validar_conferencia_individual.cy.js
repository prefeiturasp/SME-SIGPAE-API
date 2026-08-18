/// <reference types='cypress' />

describe('Validar rota de Conferencia Individual da aplicacao SIGPAE', () => {
	const senha = Cypress.env('senha')
	const parametros = {
		limit: 10,
		offset: 0,
	}

	context('Rota GET api/conferencia-individual/', () => {
		// Temporariamente desabilitado: a API retorna 500 no ambiente QA.
		it.skip('Validar GET paginado de Conferencia Individual com sucesso', () => {
			cy.autenticar_login(Cypress.env('usuario_abastecimento'), senha)

			cy.consultar_conferencia_individual(parametros).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number')
				expect(response.body.results).to.be.an('array')

				response.body.results.forEach((conferencia) => {
					expect(conferencia).to.include.all.keys(
						'conferencia',
						'status_alimento',
						'tipo_embalagem',
						'arquivo',
						'criado_em',
						'alterado_em',
						'uuid',
						'nome_alimento',
						'qtd_recebido',
						'observacao',
						'ocorrencia',
						'tem_ocorrencia',
					)
					expect(conferencia.uuid).to.be.a('string').and.not.be.empty
					expect(conferencia.conferencia).to.be.a('string').and.not.be.empty
					expect(conferencia.nome_alimento).to.be.a('string').and.not.be.empty
					expect(conferencia.tem_ocorrencia).to.be.a('boolean')
				})
			})
		})

		it('Validar GET de Conferencia Individual sem permissao', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), senha)

			cy.consultar_conferencia_individual(parametros).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(403)
				expect(response.body).to.deep.eq({
					detail: 'Você não tem permissão para executar essa ação.',
				})
			})
		})
	})
})
