/// <reference types='cypress' />

describe('Validar rota de Documentos de Recebimento da aplicacao SIGPAE', () => {
	const senha = Cypress.env('senha')
	const parametros = {
		limit: 10,
		offset: 0,
	}

	context('Rota GET api/documentos-de-recebimento/', () => {
		it('Validar GET paginado de Documentos de Recebimento com sucesso', () => {
			cy.autenticar_login(
				Cypress.env('usuario_coordenador_codae_dilog_logistica'),
				senha,
			)

			cy.consultar_documentos_de_recebimento(parametros).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number')
				expect(response.body.results).to.be.an('array')

				response.body.results.forEach((documento) => {
					expect(documento).to.include.all.keys(
						'uuid',
						'numero_cronograma',
						'numero_laudo',
						'pregao_chamada_publica',
						'nome_produto',
						'programa_leve_leite',
						'status',
						'criado_em',
					)
					expect(documento.uuid).to.be.a('string').and.not.be.empty
					expect(documento.numero_cronograma).to.be.a('string')
					expect(documento.numero_laudo).to.be.a('string')
					expect(documento.pregao_chamada_publica).to.be.a('string')
					expect(documento.nome_produto).to.be.a('string').and.not.be.empty
					expect(documento.programa_leve_leite).to.be.a('boolean')
					expect(documento.status).to.be.a('string').and.not.be.empty
					expect(documento.criado_em).to.be.a('string').and.not.be.empty
				})
			})
		})

		it('Validar GET de Documentos de Recebimento sem permissao', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), senha)

			cy.consultar_documentos_de_recebimento(parametros).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(403)
				expect(response.body).to.deep.eq({
					detail: 'Você não tem permissão para executar essa ação.',
				})
			})
		})
	})

	context('Rota POST api/documentos-de-recebimento/', () => {
		// Temporariamente desabilitado: nenhum usuario do .env possui permissao para o POST.
		it.skip('Validar POST de Documentos de Recebimento com sucesso', () => {
			cy.autenticar_login(
				Cypress.env('usuario_coordenador_codae_dilog_logistica'),
				senha,
			)

			cy.gerar_documentos_de_recebimento().then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(201)
			})
		})

		it('Validar POST de Documentos de Recebimento sem permissao', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), senha)

			cy.gerar_documentos_de_recebimento().then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(403)
				expect(response.body).to.deep.eq({
					detail: 'Você não tem permissão para executar essa ação.',
				})
			})
		})
	})
})
