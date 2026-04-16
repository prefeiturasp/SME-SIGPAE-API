describe('Validar rotas de Laboratórios da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_qualidade')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/laboratorios/', () => {
		it('Validar GET com sucesso de Laboratórios', () => {
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0].contatos[0]).to.have.property('nome')
				expect(response.body.results[0].contatos[0]).to.have.property(
					'telefone',
				)
				expect(response.body.results[0].contatos[0]).to.have.property('email')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('cnpj')
				expect(response.body.results[0]).to.have.property('cep')
				expect(response.body.results[0]).to.have.property('logradouro')
				expect(response.body.results[0]).to.have.property('numero')
				expect(response.body.results[0]).to.have.property('complemento')
				expect(response.body.results[0]).to.have.property('bairro')
				expect(response.body.results[0]).to.have.property('cidade')
				expect(response.body.results[0]).to.have.property('estado')
				expect(response.body.results[0]).to.have.property('credenciado')
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro Nome Válido', () => {
			var nome_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome

				var filtro = '?nome=' + nome_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('cnpj')
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro Nome Inválido', () => {
			var filtro = '?nome=NomeInválido Para o Teste'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro CNPJ', () => {
			var cnpj_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				cnpj_filtro = response.body.results[0].cnpj

				var filtro = '?cnpj=' + cnpj_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0])
						.to.have.property('cnpj')
						.to.eq(cnpj_filtro)
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro CNPJ Inválido', () => {
			var filtro = '?cnpj=11110000000000'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro UUID Válido', () => {
			var uuid_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				uuid_filtro = response.body.results[0].uuid

				var filtro = '?uuid=' + uuid_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0])
						.to.have.property('uuid')
						.to.eq(uuid_filtro)
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('cnpj')
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro UUID Inválido', () => {
			var filtro = '?uuid=bd08e0a0-b0b0-0ab0-b000-a05c000f00c0'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_laboratorios_por_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body.contatos[0]).to.have.property('nome')
					expect(response.body.contatos[0]).to.have.property('telefone')
					expect(response.body.contatos[0]).to.have.property('email')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid').to.eq(uuid_response)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('cnpj')
					expect(response.body).to.have.property('cep')
					expect(response.body).to.have.property('logradouro')
					expect(response.body).to.have.property('numero')
					expect(response.body).to.have.property('complemento')
					expect(response.body).to.have.property('bairro')
					expect(response.body).to.have.property('cidade')
					expect(response.body).to.have.property('estado')
					expect(response.body).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_laboratorios_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Lista Laboratórios', () => {
			cy.consultar_lista_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('cnpj')
			})
		})

		it('Validar GET com sucesso de Lista Laboratórios Credenciados', () => {
			cy.consultar_lista_laboratorios_credenciados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Laboratórios', () => {
			cy.consultar_lista_nomes_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results).to.have.length.greaterThan(0)
			})
		})

		it('Validar POST com sucesso de Laboratórios', () => {
			var dados_teste = {
				nome: 'Testes Automação ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}
			var cnpj = dados_teste.cnpj
			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.cnpj).to.eq(cnpj)
				var uuid_response = response.body.uuid

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar POST de Laboratórios com Credenciado e Nutricionista Inválido', () => {
			var dados_teste = {
				nome: 'Testes Automação ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: '123',
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: '456',
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.credenciado[0]).to.eq(
					'Deve ser um valor booleano válido.',
				)
				expect(response.body.contatos[0].eh_nutricionista[0]).to.eq(
					'Deve ser um valor booleano válido.',
				)
			})
		})

		it('Validar POST de Laboratórios com os campos em branco', () => {
			var dados_teste = {
				nome: '',
				cnpj: '',
				cep: '',
				logradouro: '',
				numero: '',
				bairro: '',
				cidade: '',
				estado: '',
				credenciado: false,
				contato_nome: '',
				contato_telefone: '',
				contato_telefone2: '',
				contato_celular: '',
				contato_email: '',
				contato_eh_nutricionista: '',
				contato_crn_numero: '',
				complemento: '',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.cnpj[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.cep[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.logradouro[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.numero[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.bairro[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.cidade[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
				expect(response.body.estado[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar POST de Laboratórios sem informar os campos obrigatórios', () => {
			var dados_teste = {}
			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.cnpj[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.cep[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.logradouro[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.numero[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.bairro[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.cidade[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.estado[0]).to.eq('Este campo é obrigatório.')
				expect(response.body.credenciado[0]).to.eq('Este campo é obrigatório.')
			})
		})

		it('Validar DELETE de Laboratórios com sucesso', () => {
			var dados_teste = {
				nome: 'Testes Automação ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}
			var cnpj = dados_teste.cnpj
			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.cnpj).to.eq(cnpj)
				var uuid_response = response.body.uuid

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de Laboratórios com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_laboratorios(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PUT com sucesso de Laboratórios', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PUT'
				cy.put_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePut) => {
						expect(responsePut.status).to.eq(200)
						expect(responsePut.body.nome).to.eq(
							'TESTES AUTOMATIZADOS - ALTERADO VIA PUT',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PUT de Laboratórios com Credenciado e Nutricionista Inválido', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.credenciado = '123'
				dados_teste.contato_eh_nutricionista = '456'
				cy.put_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePut) => {
						expect(responsePut.status).to.eq(400)
						expect(responsePut.body.credenciado[0]).to.eq(
							'Deve ser um valor booleano válido.',
						)
						expect(responsePut.body.contatos[0].eh_nutricionista[0]).to.eq(
							'Deve ser um valor booleano válido.',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PUT de Laboratórios sem informar os campos obrigatórios', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste = {}
				cy.put_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePut) => {
						expect(responsePut.status).to.eq(400)
						expect(responsePut.body.nome[0]).to.eq('Este campo é obrigatório.')
						expect(responsePut.body.cnpj[0]).to.eq('Este campo é obrigatório.')
						expect(responsePut.body.cep[0]).to.eq('Este campo é obrigatório.')
						expect(responsePut.body.logradouro[0]).to.eq(
							'Este campo é obrigatório.',
						)
						expect(responsePut.body.numero[0]).to.eq(
							'Este campo é obrigatório.',
						)
						expect(responsePut.body.bairro[0]).to.eq(
							'Este campo é obrigatório.',
						)
						expect(responsePut.body.cidade[0]).to.eq(
							'Este campo é obrigatório.',
						)
						expect(responsePut.body.estado[0]).to.eq(
							'Este campo é obrigatório.',
						)
						expect(responsePut.body.credenciado[0]).to.eq(
							'Este campo é obrigatório.',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PUT de Laboratórios com os campos em branco', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.nome = ''
				dados_teste.cnpj = ''
				dados_teste.cep = ''
				dados_teste.logradouro = ''
				dados_teste.numero = ''
				dados_teste.bairro = ''
				dados_teste.cidade = ''
				dados_teste.estado = ''
				dados_teste.credenciado = false

				cy.put_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePut) => {
						expect(responsePut.status).to.eq(400)
						expect(responsePut.body.nome[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.cnpj[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.cep[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.logradouro[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.numero[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.bairro[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.cidade[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePut.body.estado[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PUT de Laboratórios com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.put_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PATCH com sucesso de Laboratórios', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PATCH'
				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePatch) => {
						expect(responsePatch.status).to.eq(200)
						expect(responsePatch.body.nome).to.eq(
							'TESTES AUTOMATIZADOS - ALTERADO VIA PATCH',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PATCH de Laboratórios com Credenciado e Nutricionista Inválido', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.credenciado = '123'
				dados_teste.contato_eh_nutricionista = '456'
				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePatch) => {
						expect(responsePatch.status).to.eq(400)
						expect(responsePatch.body.credenciado[0]).to.eq(
							'Deve ser um valor booleano válido.',
						)
						expect(responsePatch.body.contatos[0].eh_nutricionista[0]).to.eq(
							'Deve ser um valor booleano válido.',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PATCH de Laboratórios com os campos em branco', () => {
			var dados_teste = {
				nome: 'Testes Automação - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automação',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'São Paulo',
				estado: 'SP',
				credenciado: true,
				contato_nome: 'Contato Teste',
				contato_telefone: '1155555555',
				contato_telefone2: '115888888',
				contato_celular: '11977777777',
				contato_email: 'user@example.com',
				contato_eh_nutricionista: true,
				contato_crn_numero: '1234567',
				complemento: 'Complemento Teste',
			}

			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid_response = response.body.uuid

				dados_teste.nome = ''
				dados_teste.cnpj = ''
				dados_teste.cep = ''
				dados_teste.logradouro = ''
				dados_teste.numero = ''
				dados_teste.bairro = ''
				dados_teste.cidade = ''
				dados_teste.estado = ''
				dados_teste.credenciado = false

				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then(
					(responsePatch) => {
						expect(responsePatch.status).to.eq(400)
						expect(responsePatch.body.nome[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.cnpj[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.cep[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.logradouro[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.numero[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.bairro[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.cidade[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
						expect(responsePatch.body.estado[0]).to.eq(
							'Este campo não pode estar em branco.',
						)
					},
				)

				// Deletar o laboratório cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar PATCH de Laboratórios com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.patch_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
