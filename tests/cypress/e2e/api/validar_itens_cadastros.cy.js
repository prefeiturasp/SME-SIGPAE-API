describe('Validar rotas de Itens Cadastros da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/itens-cadastros/', () => {
		it('Validar GET com sucesso de Itens Cadastros', () => {
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('tipo')
				expect(response.body.results[0]).to.have.property('tipo_display')
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Nome Válido', () => {
			var nome_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome

				var filtro = '?nome=' + nome_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Nome Inválido', () => {
			var filtro = '?nome=NomeInválido Para o Teste'
			cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Tipo Válido', () => {
			var tipo_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				tipo_filtro = response.body.results[0].tipo

				var filtro = '?tipo=' + tipo_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Tipo Inválido', () => {
			var filtro = '?tipo=TipoInválido Para o Teste'
			cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtros Nome e Tipo Válidos', () => {
			var nome_filtro = ''
			var tipo_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome
				tipo_filtro = response.body.results[0].tipo

				var filtro = '?nome=' + nome_filtro + '&tipo=' + tipo_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_itens_cadastros_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('uuid')
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('tipo')
					expect(response.body).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_itens_cadastros_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Lista Nomes', () => {
			cy.consultar_itens_cadastros_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results).to.have.length.greaterThan(0)
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Tipos', () => {
			cy.consultar_itens_cadastros_tipos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('tipo')
				expect(response.body[0]).to.have.property('tipo_display')
			})
		})

		it('Validar POST com sucesso de Itens Cadastros', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar POST de Itens Cadastros já existente', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação Item Existente'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
					expect(response.status).to.eq(400)
					expect(response.body[0]).to.eq('Item já cadastrado.')
				})

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar POST de Itens Cadastros com Tipo Inválido', () => {
			const opcoes = ['MARCAS', 'FABRICANTES', 'UNIDADES_MEDIDAS', 'EMBALAGENS']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq('Erro ao criar ItemCadastro.')
			})
		})

		it('Validar POST de Itens Cadastros com Nome e Tipo em branco', () => {
			var dados_teste = {
				nome: '',
				tipo: '',
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.tipo[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar POST de Itens Cadastros sem informar os campos Nome e Tipo', () => {
			var dados_teste = {}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.tipo[0]).to.eq('Este campo é obrigatório.')
			})
		})

		it('Validar DELETE de Itens Cadastros com sucesso', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação DELETE'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar DELETE de Itens Cadastros com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_itens_cadastros(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PUT com sucesso de Itens Cadastros', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					var dados_teste = {
						nome: 'Testes Automatizados Alterado via PUT',
						tipo: tipo_teste,
					}

					cy.put_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(200)
							expect(responsePut.body['tipo']).to.eq(tipo_teste)
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PUT de Itens Cadastros com Tipo inválido', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					var dados_teste = {
						nome: 'Testes Automatizados Alterado via PUT',
						tipo: 'TIPO_INVALIDO',
					}

					cy.put_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(400)
							expect(responsePut.body[0]).to.eq(
								'Erro ao criar ItemCadastro. Tipo não permitido: ' +
									dados_teste.tipo,
							)
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PUT de Itens Cadastros  já existente', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automatizados via PUT - Item Existente'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					cy.put_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(400)
							expect(responsePut.body[0]).to.eq('Item já cadastrado.')
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PUT de Itens Cadastros com Nome e Tipo em branco', () => {
			var uuid = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				uuid = response.body.results[0].uuid

				var dados_teste = {
					nome: '',
					tipo: '',
				}
				cy.put_alterar_itens_cadastros(uuid, dados_teste).then((response) => {
					expect(response.status).to.eq(400)
					expect(response.body.nome[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
					expect(response.body.tipo[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
				})
			})
		})

		it('Validar PUT de Itens Cadastros sem informar os campos Nome e Tipo', () => {
			var uuid = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				uuid = response.body.results[0].uuid

				var dados_teste = {}
				cy.put_alterar_itens_cadastros(uuid, dados_teste).then((response) => {
					expect(response.status).to.eq(400)
					expect(response.body.nome[0]).to.eq('Este campo é obrigatório.')
					expect(response.body.tipo[0]).to.eq('Este campo é obrigatório.')
				})
			})
		})

		it('Validar PACTH com sucesso de Itens Cadastros', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					var dados_teste = {
						nome: 'Testes Automatizados Alterado via PATCH',
						tipo: tipo_teste,
					}

					cy.patch_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(200)
							expect(responsePut.body['tipo']).to.eq(tipo_teste)
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PACTH de Itens Cadastros com Tipo inválido', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automação'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					var dados_teste = {
						nome: 'Testes Automatizados Alterado via PATCH',
						tipo: 'TIPO_INVALIDO',
					}

					cy.patch_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(400)
							expect(responsePut.body[0]).to.eq(
								'Erro ao criar ItemCadastro. Tipo não permitido: ' +
									dados_teste.tipo,
							)
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PACTH de Itens Cadastros  já existente', () => {
			const opcoes = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
			var tipo_teste = opcoes[Math.floor(Math.random() * opcoes.length)]

			var nome_teste = 'Testes Automatizados via PATCH - Item Existente'
			var dados_teste = {
				nome: nome_teste,
				tipo: tipo_teste,
			}
			cy.cadastrar_itens_cadastros(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['tipo']).to.eq(tipo_teste)

				var filtro = '?nome=' + nome_teste
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					var uuid_response = response.body.results[0].uuid

					cy.patch_alterar_itens_cadastros(uuid_response, dados_teste).then(
						(responsePut) => {
							expect(responsePut.status).to.eq(400)
							expect(responsePut.body[0]).to.eq('Item já cadastrado.')
						},
					)

					cy.deletar_itens_cadastros(uuid_response).then((responseDelete) => {
						expect(responseDelete.status).to.eq(204)
					})
				})
			})
		})

		it('Validar PACTH de Itens Cadastros com Nome e Tipo em branco', () => {
			var uuid = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				uuid = response.body.results[0].uuid

				var dados_teste = {
					nome: '',
					tipo: '',
				}
				cy.patch_alterar_itens_cadastros(uuid, dados_teste).then((response) => {
					expect(response.status).to.eq(400)
					expect(response.body.nome[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
					expect(response.body.tipo[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
				})
			})
		})
	})
})
