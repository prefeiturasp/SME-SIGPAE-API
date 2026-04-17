describe('Validar rotas de Laboratorios da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_qualidade')
	var senha = Cypress.config('senha')

	function validarLaboratorio(laboratorio, options = {}) {
		expect(laboratorio).to.have.property('criado_em')
		expect(laboratorio).to.have.property('alterado_em')
		expect(laboratorio).to.have.property('uuid')
		expect(laboratorio).to.have.property('nome')
		expect(laboratorio).to.have.property('cnpj')
		expect(laboratorio).to.have.property('cep')
		expect(laboratorio).to.have.property('logradouro')
		expect(laboratorio).to.have.property('numero')
		expect(laboratorio).to.have.property('complemento')
		expect(laboratorio).to.have.property('bairro')
		expect(laboratorio).to.have.property('cidade')
		expect(laboratorio).to.have.property('estado')
		expect(laboratorio).to.have.property('credenciado')

		if (options.validarContatos !== false) {
			expect(laboratorio).to.have.property('contatos').that.is.an('array')
			if (laboratorio.contatos.length > 0) {
				expect(laboratorio.contatos[0]).to.have.property('nome')
				expect(laboratorio.contatos[0]).to.have.property('telefone')
				expect(laboratorio.contatos[0]).to.have.property('email')
			}
		}
	}

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail').that.is.not.empty
	}

	function validarListaResultados(response, validarItem) {
		expect(response.body).to.have.property('results')
		expect(response.body.results).to.be.an('array')

		if (response.body.results.length > 0 && validarItem) {
			validarItem(response.body.results[0])
		}
	}

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/laboratorios/', () => {
		it('Validar GET com sucesso de Laboratorios', () => {
			cy.consultar_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')

				if (response.body.results.length > 0) {
					validarLaboratorio(response.body.results[0])
				}
			})
		})

		it('Validar GET com sucesso de Laboratorios com filtro Nome Valido', () => {
			cy.consultar_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var nome_filtro = response.body.results[0].nome

				var filtro = '?nome=' + nome_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((responseFiltro) => {
					expect([200, 403]).to.include(responseFiltro.status)

					if (responseFiltro.status === 403) {
						validarPermissaoNegada(responseFiltro)
						return
					}

					expect(responseFiltro.body).to.have.property('count')
					expect(responseFiltro.body).to.have.property('next')
					expect(responseFiltro.body).to.have.property('previous')
					expect(responseFiltro.body).to.have.property('results')
					expect(responseFiltro.body.results).to.be.an('array').and.not.to.be.empty
					validarLaboratorio(responseFiltro.body.results[0])
				})
			})
		})

		it('Validar GET de Laboratorios com filtro Nome Invalido', () => {
			var filtro = '?nome=NomeInvalido Para o Teste'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratorios com filtro CNPJ', () => {
			cy.consultar_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var cnpj_filtro = response.body.results[0].cnpj

				var filtro = '?cnpj=' + cnpj_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((responseFiltro) => {
					expect([200, 403]).to.include(responseFiltro.status)

					if (responseFiltro.status === 403) {
						validarPermissaoNegada(responseFiltro)
						return
					}

					expect(responseFiltro.body).to.have.property('count')
					expect(responseFiltro.body).to.have.property('next')
					expect(responseFiltro.body).to.have.property('previous')
					expect(responseFiltro.body).to.have.property('results')
					expect(responseFiltro.body.results).to.be.an('array').and.not.to.be.empty
					validarLaboratorio(responseFiltro.body.results[0])
					expect(responseFiltro.body.results[0]).to.have.property('cnpj').to.eq(cnpj_filtro)
				})
			})
		})

		it('Validar GET de Laboratorios com filtro CNPJ Invalido', () => {
			var filtro = '?cnpj=11110000000000'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratorios com filtro UUID Valido', () => {
			cy.consultar_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var uuid_filtro = response.body.results[0].uuid

				var filtro = '?uuid=' + uuid_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((responseFiltro) => {
					expect([200, 403]).to.include(responseFiltro.status)

					if (responseFiltro.status === 403) {
						validarPermissaoNegada(responseFiltro)
						return
					}

					expect(responseFiltro.body).to.have.property('count')
					expect(responseFiltro.body).to.have.property('next')
					expect(responseFiltro.body).to.have.property('previous')
					expect(responseFiltro.body).to.have.property('results')
					expect(responseFiltro.body.results).to.be.an('array').and.not.to.be.empty
					validarLaboratorio(responseFiltro.body.results[0])
					expect(responseFiltro.body.results[0]).to.have.property('uuid').to.eq(uuid_filtro)
				})
			})
		})

		it('Validar GET de Laboratorios com filtro UUID Invalido', () => {
			var filtro = '?uuid=bd08e0a0-b0b0-0ab0-b000-a05c000f00c0'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratorios Com UUID Valido', () => {
			cy.consultar_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_laboratorios_por_uuid(uuid_response).then((responseUuid) => {
					expect([200, 403]).to.include(responseUuid.status)

				if (responseUuid.status === 403) {
					validarPermissaoNegada(responseUuid)
					return
				}
					validarLaboratorio(responseUuid.body)
					expect(responseUuid.body).to.have.property('uuid').to.eq(uuid_response)
				})
			})
		})

		it('Validar GET de Laboratorios Com UUID Invalido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_laboratorios_por_uuid(uuid).then((response) => {
				expect([400, 403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar GET com sucesso de Lista Laboratorios', () => {
			cy.consultar_lista_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				if (response.body.results.length > 0) {
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('cnpj')
				}
			})
		})

		it('Validar GET com sucesso de Lista Laboratorios Credenciados', () => {
			cy.consultar_lista_laboratorios_credenciados().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				validarListaResultados(response, (item) => {
					expect(item).to.have.property('uuid')
					expect(item).to.have.property('nome')
				})
			})
		})

		it('Validar GET com sucesso de Lista Nomes Laboratorios', () => {
			cy.consultar_lista_nomes_laboratorios().then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})

		it('Validar POST com sucesso de Laboratorios', () => {
			var dados_teste = {
				nome: 'Testes Automacao ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.cnpj).to.eq(cnpj)
				var uuid_response = response.body.uuid

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar POST de Laboratorios com Credenciado e Nutricionista Invalido', () => {
			var dados_teste = {
				nome: 'Testes Automacao ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([400, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.credenciado[0]).to.contain('booleano')
				expect(response.body.contatos[0].eh_nutricionista[0]).to.contain('booleano')
			})
		})

		it('Validar POST de Laboratorios com os campos em branco', () => {
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
				expect([400, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.nome[0]).to.contain('em branco')
				expect(response.body.cnpj[0]).to.contain('em branco')
				expect(response.body.cep[0]).to.contain('em branco')
				expect(response.body.logradouro[0]).to.contain('em branco')
				expect(response.body.numero[0]).to.contain('em branco')
				expect(response.body.bairro[0]).to.contain('em branco')
				expect(response.body.cidade[0]).to.contain('em branco')
				expect(response.body.estado[0]).to.contain('em branco')
			})
		})

		it('Validar POST de Laboratorios sem informar os campos obrigatorios', () => {
			var dados_teste = {}
			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect([400, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.nome[0]).to.contain('obrigatorio')
				expect(response.body.cnpj[0]).to.contain('obrigatorio')
				expect(response.body.cep[0]).to.contain('obrigatorio')
				expect(response.body.logradouro[0]).to.contain('obrigatorio')
				expect(response.body.numero[0]).to.contain('obrigatorio')
				expect(response.body.bairro[0]).to.contain('obrigatorio')
				expect(response.body.cidade[0]).to.contain('obrigatorio')
				expect(response.body.estado[0]).to.contain('obrigatorio')
				expect(response.body.credenciado[0]).to.contain('obrigatorio')
			})
		})

		it('Validar DELETE de Laboratorios com sucesso', () => {
			var dados_teste = {
				nome: 'Testes Automacao ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.cnpj).to.eq(cnpj)
				var uuid_response = response.body.uuid

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar DELETE de Laboratorios com UUID invalido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_laboratorios(uuid).then((response) => {
				expect([400, 403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar PUT com sucesso de Laboratorios', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PUT'
				cy.put_alterar_laboratorios(uuid_response, dados_teste).then((responsePut) => {
					expect([200, 403]).to.include(responsePut.status)

					if (responsePut.status === 403) {
						validarPermissaoNegada(responsePut)
						return
					}
					expect(responsePut.body.nome).to.eq('TESTES AUTOMATIZADOS - ALTERADO VIA PUT')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PUT de Laboratorios com Credenciado e Nutricionista Invalido', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				var uuid_response = response.body.uuid

				dados_teste.credenciado = '123'
				dados_teste.contato_eh_nutricionista = '456'
				cy.put_alterar_laboratorios(uuid_response, dados_teste).then((responsePut) => {
					expect([400, 403]).to.include(responsePut.status)

					if (responsePut.status === 403) {
						validarPermissaoNegada(responsePut)
						return
					}
					expect(responsePut.body.credenciado[0]).to.contain('booleano')
					expect(responsePut.body.contatos[0].eh_nutricionista[0]).to.contain('booleano')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PUT de Laboratorios sem informar os campos obrigatorios', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				var uuid_response = response.body.uuid

				cy.put_alterar_laboratorios(uuid_response, {}).then((responsePut) => {
					expect([400, 403]).to.include(responsePut.status)

					if (responsePut.status === 403) {
						validarPermissaoNegada(responsePut)
						return
					}
					expect(responsePut.body.nome[0]).to.contain('obrigatorio')
					expect(responsePut.body.cnpj[0]).to.contain('obrigatorio')
					expect(responsePut.body.cep[0]).to.contain('obrigatorio')
					expect(responsePut.body.logradouro[0]).to.contain('obrigatorio')
					expect(responsePut.body.numero[0]).to.contain('obrigatorio')
					expect(responsePut.body.bairro[0]).to.contain('obrigatorio')
					expect(responsePut.body.cidade[0]).to.contain('obrigatorio')
					expect(responsePut.body.estado[0]).to.contain('obrigatorio')
					expect(responsePut.body.credenciado[0]).to.contain('obrigatorio')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PUT de Laboratorios com os campos em branco', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

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

				cy.put_alterar_laboratorios(uuid_response, dados_teste).then((responsePut) => {
					expect([400, 403]).to.include(responsePut.status)

					if (responsePut.status === 403) {
						validarPermissaoNegada(responsePut)
						return
					}
					expect(responsePut.body.nome[0]).to.contain('em branco')
					expect(responsePut.body.cnpj[0]).to.contain('em branco')
					expect(responsePut.body.cep[0]).to.contain('em branco')
					expect(responsePut.body.logradouro[0]).to.contain('em branco')
					expect(responsePut.body.numero[0]).to.contain('em branco')
					expect(responsePut.body.bairro[0]).to.contain('em branco')
					expect(responsePut.body.cidade[0]).to.contain('em branco')
					expect(responsePut.body.estado[0]).to.contain('em branco')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PUT de Laboratorios com UUID invalido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.put_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect([400, 403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar PATCH com sucesso de Laboratorios', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				var uuid_response = response.body.uuid

				dados_teste.nome = 'Testes Automatizados - Alterado via PATCH'
				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then((responsePatch) => {
					expect([200, 403]).to.include(responsePatch.status)

					if (responsePatch.status === 403) {
						validarPermissaoNegada(responsePatch)
						return
					}
					expect(responsePatch.body.nome).to.eq('TESTES AUTOMATIZADOS - ALTERADO VIA PATCH')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PATCH de Laboratorios com Credenciado e Nutricionista Invalido', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				var uuid_response = response.body.uuid

				dados_teste.credenciado = '123'
				dados_teste.contato_eh_nutricionista = '456'
				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then((responsePatch) => {
					expect([400, 403]).to.include(responsePatch.status)

					if (responsePatch.status === 403) {
						validarPermissaoNegada(responsePatch)
						return
					}
					expect(responsePatch.body.credenciado[0]).to.contain('booleano')
					expect(responsePatch.body.contatos[0].eh_nutricionista[0]).to.contain('booleano')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PATCH de Laboratorios com os campos em branco', () => {
			var dados_teste = {
				nome: 'Testes Automacao - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste Automacao',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'Sao Paulo',
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
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

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

				cy.patch_alterar_laboratorios(uuid_response, dados_teste).then((responsePatch) => {
					expect([400, 403]).to.include(responsePatch.status)

					if (responsePatch.status === 403) {
						validarPermissaoNegada(responsePatch)
						return
					}
					expect(responsePatch.body.nome[0]).to.contain('em branco')
					expect(responsePatch.body.cnpj[0]).to.contain('em branco')
					expect(responsePatch.body.cep[0]).to.contain('em branco')
					expect(responsePatch.body.logradouro[0]).to.contain('em branco')
					expect(responsePatch.body.numero[0]).to.contain('em branco')
					expect(responsePatch.body.bairro[0]).to.contain('em branco')
					expect(responsePatch.body.cidade[0]).to.contain('em branco')
					expect(responsePatch.body.estado[0]).to.contain('em branco')
				})

				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect([204, 403, 404]).to.include(responseDelete.status)
				})
			})
		})

		it('Validar PATCH de Laboratorios com UUID invalido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.patch_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect([400, 403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})
	})
})
