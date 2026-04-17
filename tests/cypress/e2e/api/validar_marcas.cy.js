describe('Validar rotas de Marcas da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/marcas/', () => {
		it('Validar GET com sucesso de Marcas', () => {
			cy.consultar_marcas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de Marcas com Nome Edital Válido', () => {
			var edital = ''
			cy.consultar_editais().then((response) => {
				expect(response.status).to.eq(200)
				edital = response.body.results[0].numero

				var param = '?nome_edital=' + edital
				cy.consultar_marcas_por_edital(param).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('uuid')
				})
			})
		})

		it('Validar GET de Marcas com Nome Edital Inválido', () => {
			var param = '?nome_edital=NomeInválido Para o Teste'
			cy.consultar_marcas_por_edital(param).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Marcas Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_marcas().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_marcas_por_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('uuid').eq(uuid_response)
				})
			})
		})

		it('Validar GET de Marcas Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_marcas_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar POST com sucesso de Marcas', () => {
			var dados_teste = {
				nome: 'Testes Automação ' + new Date().getTime(),
			}
			cy.cadastrar_marcas(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.nome).to.eq(dados_teste.nome)
				expect(response.body).to.have.property('uuid')
				var uuid_response = response.body.uuid

				// Deletar a marca cadastrada no teste
				cy.deletar_marcas(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de Marcas com sucesso', () => {
			var dados_teste = {
				nome: 'Testes Automação ' + new Date().getTime(),
			}
			cy.cadastrar_marcas(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.nome).to.eq(dados_teste.nome)
				expect(response.body).to.have.property('uuid')
				var uuid_response = response.body.uuid

				cy.deletar_marcas(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de Marcas com UUID Inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_marcas(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PUT com sucesso de Marcas', () => {
			var dados_teste = {
				nome: 'Testes Automação PUT - ' + new Date().getTime(),
			}

			cy.cadastrar_marcas(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.nome).to.eq(dados_teste.nome)
				expect(response.body).to.have.property('uuid')
				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PUT'
				cy.put_alterar_marcas(uuid_response, dados_teste).then(
					(responsePut) => {
						expect(responsePut.status).to.eq(200)
						expect(responsePut.body.nome).to.eq(
							'Testes Automatizados - Alterado via PUT',
						)
					},
				)

				// Deletar a marca cadastrada no teste
				cy.deletar_marcas(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PUT de Marcas com UUID Inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.put_alterar_marcas(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PATCH com sucesso de Marcas', () => {
			var dados_teste = {
				nome: 'Testes Automação PATCH - ' + new Date().getTime(),
			}

			cy.cadastrar_marcas(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.nome).to.eq(dados_teste.nome)
				expect(response.body).to.have.property('uuid')
				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PATCH'
				cy.patch_alterar_marcas(uuid_response, dados_teste).then(
					(responsePatch) => {
						expect(responsePatch.status).to.eq(200)
						expect(responsePatch.body.nome).to.eq(
							'Testes Automatizados - Alterado via PATCH',
						)
					},
				)

				// Deletar a marca cadastrada no teste
				cy.deletar_marcas(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PATCH de Marcas com UUID Inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.patch_alterar_marcas(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/marcas/lista-nomes/', () => {
		it('Validar GET com sucesso de Lista Nomes', () => {
			cy.consultar_marcas_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Avaliar Reclamação', () => {
			cy.consultar_lista_nomes_avaliar_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Nova Reclamação', () => {
			cy.consultar_lista_nomes_nova_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Responder Reclamação', () => {
			cy.consultar_lista_nomes_responder_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Responder Reclamação Escola', () => {
			usuario = Cypress.config('usuario_diretor_ue')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_lista_nomes_responder_reclamacao_escola().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Responder Reclamação NutriSupervisor', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_lista_nomes_responder_reclamacao_nutrisupervisor().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Únicos', () => {
			cy.consultar_lista_nomes_unicos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})
