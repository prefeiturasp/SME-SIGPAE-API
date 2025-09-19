/// <reference types='cypress' />

describe('Validar rotas de alimentos da guia da aplicação SIGPAE', () => {
	var usuario
	var senha
	var id
	before(() => {
		usuario = Cypress.config('usuario_coordenador_codae_dilog_logistica')
		senha = Cypress.config('senha')
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/alimentos-da-guia/ GET', () => {
		it('Validar GET de todos os alimentos da guia com sucesso', () => {
			id = ''
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.exist
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('alterado_em').that.exist
				expect(primeiro_resultado).to.have.property('codigo_papa').that.exist
				expect(primeiro_resultado).to.have.property('codigo_suprimento').that
					.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
				expect(primeiro_resultado).to.have.property('guia').that.exist
				expect(primeiro_resultado).to.have.property('nome_alimento').that.exist
				expect(primeiro_resultado).to.have.property('uuid').that.exist
			})
		})

		it('Validar GET com parametros limitados com sucesso', () => {
			id = '?limit=4&offset=5'
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.exist
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('alterado_em').that.exist
				expect(primeiro_resultado).to.have.property('codigo_papa').that.exist
				expect(primeiro_resultado).to.have.property('codigo_suprimento').that
					.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
				expect(primeiro_resultado).to.have.property('guia').that.exist
				expect(primeiro_resultado).to.have.property('nome_alimento').that.exist
				expect(primeiro_resultado).to.have.property('uuid').that.exist
			})
		})

		it('Validar GET com parametros invalidos', () => {
			id = 'dgaugsusausay'
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.redirects[0]).to.contain('301:')
				expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
				expect(response.allRequestResponses[0])
					.to.have.property('Response Status')
					.that.equals(301)
				expect(response.redirects).to.be.an('array').that.is.not.empty
			})
		})

		it('Validar que um usuário sem permissão não pode acessar o endpoint', () => {
			id = ''
			usuario = Cypress.config('usuario_diretor_ue')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body).to.have.property('detail').that.is.a('string')
				expect(response.body.detail).to.eq(
					'Você não tem permissão para executar essa ação.',
				)
			})
		})
	})

	context('Casos de teste para a rota api/alimentos-da-guia/uuid/ GET', () => {
		it('Validar GET com id de um unico alimentos da guia com sucesso', () => {
			id = 'b9a97cc1-f4dc-469d-be34-f63eb96bdbf4/'
			usuario = Cypress.config('usuario_coordenador_codae_dilog_logistica')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('alterado_em').that.exist
				expect(response.body).to.have.property('codigo_papa').that.exist
				expect(response.body).to.have.property('codigo_suprimento').that.exist
				expect(response.body).to.have.property('criado_em').that.exist
				expect(response.body).to.have.property('guia').that.exist
				expect(response.body).to.have.property('nome_alimento').that.exist
				expect(response.body).to.have.property('uuid').that.exist
			})
		})

		it('Validar GET com a rota sem a / no fim', () => {
			id = 'b9a97cc1-f4dc-469d-be34-f63eb96bdbf4'
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.redirects[0]).to.contain('301:')
				expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
				expect(response.allRequestResponses[0])
					.to.have.property('Response Status')
					.that.equals(301)
				expect(response.redirects).to.be.an('array').that.is.not.empty
			})
		})

		it('Validar GET com o id invalido', () => {
			id = 'b9adscc1-fddc-46sd-b534-f63ebdsbdbf4'
			cy.validar_alimentos_da_guia(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.redirects[0]).to.contain('301:')
				expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
				expect(response.allRequestResponses[0])
					.to.have.property('Response Status')
					.that.equals(301)
				expect(response.redirects).to.be.an('array').that.is.not.empty
			})
		})
	})

	context('Casos de teste para a rota api/alimentos-da-guia/ POST', () => {
		it('Validar Post cadastro de alimento da guia com sucesso', () => {
			var alimento = {
				codigo_suprimento: 'teste automatizado',
				codigo_papa: 't a',
				nome_alimento: 'Teste Batatinha',
				guia: 8159,
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body).to.have.property('alterado_em').that.exist
				expect(response.body.codigo_papa).to.eq('t a')
				expect(response.body.codigo_suprimento).to.eq('teste automatizado')
				expect(response.body).to.have.property('criado_em').that.exist
				expect(response.body.guia).to.eq(8159)
				expect(response.body).to.have.property('uuid').that.exist
				id = response.body.uuid
				cy.excluir_alimentos_da_guia(id)
			})
		})
		it('Validar Post cadastro com codigo do suprimento com mais de 100 caracteres', () => {
			var alimento = {
				codigo_suprimento:
					'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
				codigo_papa: 't a',
				nome_alimento: 'Teste Batatinha',
				guia: 8159,
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.codigo_suprimento[0]).contains(
					'Certifique-se de que este campo não tenha mais de 100 caracteres.',
				)
			})
		})
		it('Validar Post cadastro com codigo do papa com mais de 10 caracteres', () => {
			var alimento = {
				codigo_suprimento: '1010101010',
				codigo_papa: '12312312312',
				nome_alimento: 'Teste Batatinha',
				guia: 8159,
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.codigo_papa[0]).contains(
					'Certifique-se de que este campo não tenha mais de 10 caracteres.',
				)
			})
		})
		it('Validar Post cadastro com nome alimento com mais de 100 caracteres', () => {
			var alimento = {
				codigo_suprimento: 'teste automatizado',
				codigo_papa: 't a',
				nome_alimento:
					'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
				guia: 8159,
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome_alimento[0]).to.eq(
					'Certifique-se de que este campo não tenha mais de 100 caracteres.',
				)
			})
		})
		it('Validar Post numero guia do tipo string', () => {
			var alimento = {
				codigo_suprimento: 'teste automatizado',
				codigo_papa: 't a',
				nome_alimento: 'Teste Batatinha',
				guia: 'a',
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq(
					'Tipo incorreto. Esperava valor pk, recebeu str.',
				)
			})
		})
		it('Validar Post numero guia invalido', () => {
			var alimento = {
				codigo_suprimento: 'teste automatizado',
				codigo_papa: 't a',
				nome_alimento: 'Teste Batatinha',
				guia: '1',
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq(
					'Pk inválido "1" - objeto não existe.',
				)
			})
		})
	})

	context('Casos de teste para a rota api/alimentos-da-guia/id/ DELETE', () => {
		it('Validar Delete com id de um unico alimento da guia com sucesso', () => {
			var alimento = {
				codigo_suprimento: 'teste automatizado',
				codigo_papa: 't a',
				nome_alimento: 'Teste Batatinha',
				guia: 8159,
			}
			cy.cadastrar_alimentos_da_guia(alimento).then((response_id) => {
				id = response_id.body.uuid
				cy.excluir_alimentos_da_guia(id).then((response) => {
					expect(response.status).to.eq(204)
				})
			})
		})
		it('Validar Delete sem o id informado', () => {
			id = ''
			cy.excluir_alimentos_da_guia(id).then((response) => {
				expect(response.status).to.eq(405)
			})
		})
		it('Validar Delete com id inexistente', () => {
			id = '5e141551-d242-482c-b74a-64e7e7efeb24'
			cy.excluir_alimentos_da_guia(id).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Casos de teste para a rota api/alimentos-da-guia/id PUT', () => {
		var alimento = {
			codigo_suprimento: 'teste automatizado',
			codigo_papa: 't a',
			nome_alimento: 'Teste Batatinha',
			guia: 8159,
		}
		it('Validar Put alterar alimento da guia com sucesso', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'Alteracao automatizado',
					codigo_papa: 'a a',
					nome_alimento: 'Teste Batatinha Alteracao',
					guia: 8160,
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(200)
						expect(response_alteracao.body).to.have.property('alterado_em').that
							.exist
						expect(response_alteracao.body.codigo_papa).to.eq('a a')
						expect(response_alteracao.body.codigo_suprimento).to.eq(
							'Alteracao automatizado',
						)
						expect(response_alteracao.body).to.have.property('criado_em').that
							.exist
						expect(response_alteracao.body.nome_alimento).to.eq(
							'Teste Batatinha Alteracao',
						)
						expect(response_alteracao.body.guia).to.eq(8160)
						expect(response_alteracao.body).to.have.property('uuid').that.exist
						id = response_alteracao.body.uuid
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com codigo do suprimento com mais de 100 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento:
						'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.codigo_suprimento[0]).contains(
							'Certifique-se de que este campo não tenha mais de 100 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com codigo do papa com mais de 10 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: '1010101010',
					codigo_papa: '12312312312',
					nome_alimento: 'Teste Batatinha',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.codigo_papa[0]).contains(
							'Certifique-se de que este campo não tenha mais de 10 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com nome alimento com mais de 100 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento:
						'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.nome_alimento[0]).to.eq(
							'Certifique-se de que este campo não tenha mais de 100 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put numero guia do tipo string', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: 'a',
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.guia[0]).to.eq(
							'Tipo incorreto. Esperava valor pk, recebeu str.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})
		it('Validar Put numero guia invalido', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: '1',
				}
				cy.alterar_alimentos_da_guia(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.guia[0]).to.eq(
							'Pk inválido "1" - objeto não existe.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})
	})

	context('Casos de teste para a rota api/alimentos-da-guia/id PATCH', () => {
		var alimento = {
			codigo_suprimento: 'teste automatizado',
			codigo_papa: 't a',
			nome_alimento: 'Teste Batatinha',
			guia: 8159,
		}
		it('Validar Patch alterar todos os itens de alimento da guia com sucesso', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'Alteracao automatizado',
					codigo_papa: 'a a',
					nome_alimento: 'Teste Batatinha Alteracao',
					guia: 8160,
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(200)
						expect(response_alteracao.body).to.have.property('alterado_em').that
							.exist
						expect(response_alteracao.body.codigo_papa).to.eq('a a')
						expect(response_alteracao.body.codigo_suprimento).to.eq(
							'Alteracao automatizado',
						)
						expect(response_alteracao.body).to.have.property('criado_em').that
							.exist
						expect(response_alteracao.body.nome_alimento).to.eq(
							'Teste Batatinha Alteracao',
						)
						expect(response_alteracao.body.guia).to.eq(8160)
						expect(response_alteracao.body).to.have.property('uuid').that.exist
						id = response_alteracao.body.uuid
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com codigo do suprimento com mais de 100 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento:
						'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.codigo_suprimento[0]).contains(
							'Certifique-se de que este campo não tenha mais de 100 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com codigo do papa com mais de 10 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: '1010101010',
					codigo_papa: '12312312312',
					nome_alimento: 'Teste Batatinha',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.codigo_papa[0]).contains(
							'Certifique-se de que este campo não tenha mais de 10 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put cadastro com nome alimento com mais de 100 caracteres', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento:
						'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511',
					guia: 8159,
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.nome_alimento[0]).to.eq(
							'Certifique-se de que este campo não tenha mais de 100 caracteres.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})

		it('Validar Put numero guia do tipo string', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: 'a',
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.guia[0]).to.eq(
							'Tipo incorreto. Esperava valor pk, recebeu str.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})
		it('Validar Put numero guia invalido', () => {
			cy.cadastrar_alimentos_da_guia(alimento).then((response) => {
				id = response.body.uuid
				var alimento_alterado = {
					codigo_suprimento: 'teste automatizado',
					codigo_papa: 't a',
					nome_alimento: 'Teste Batatinha',
					guia: '1',
				}
				cy.alterar_alimentos_da_guia_patch(id, alimento_alterado).then(
					(response_alteracao) => {
						expect(response_alteracao.status).to.eq(400)
						expect(response_alteracao.body.guia[0]).to.eq(
							'Pk inválido "1" - objeto não existe.',
						)
						cy.excluir_alimentos_da_guia(id)
					},
				)
			})
		})
	})

	context(
		'Casos de teste para a rota api/alimentos-da-guia/lista-nomes/ GET',
		() => {
			it('Validar GET da lista de nomes de alimentos da guia com sucesso', () => {
				cy.Validar_lista_de_nomes_alimentos_da_guia().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results').that.is.an('array')
						.and.not.to.be.empty
					const primeiroResultado = response.body.results[0]
					expect(primeiroResultado).to.have.property('nome_alimento').that.exist
					expect(primeiroResultado).to.have.property('uuid').that.exist
				})
			})
		},
	)
})
