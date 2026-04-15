<<<<<<< HEAD
﻿describe('Validar rotas de Laboratórios da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_qualidade')
	var senha = Cypress.config('senha')
=======
﻿describe('Validar rotas de LaboratÃ³rios da aplicaÃ§Ã£o SIGPAE', () => {
const normalizarMensagem = (mensagem) =>
	mensagem
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toLowerCase()

const validarMensagem = (mensagem, trechoEsperado) => {
	expect(normalizarMensagem(mensagem)).to.include(trechoEsperado)
}

	var usuario = Cypress.env('usuario_dilog_qualidade')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/laboratorios/', () => {
<<<<<<< HEAD
		it('Validar GET com sucesso de Laboratários', () => {
=======
		it('Validar GET com sucesso de LaboratÃ³rios', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET com sucesso de Laboratários com filtro Nome Válido', () => {
=======
		it('Validar GET com sucesso de LaboratÃ³rios com filtro Nome VÃ¡lido', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET de Laboratários com filtro Nome Inválido', () => {
			var filtro = '?nome=NomeInválido Para o Teste'
=======
		it('Validar GET de LaboratÃ³rios com filtro Nome InvÃ¡lido', () => {
			var filtro = '?nome=NomeInvÃ¡lido Para o Teste'
>>>>>>> upstream/testes
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

<<<<<<< HEAD
		it('Validar GET com sucesso de Laboratários com filtro CNPJ', () => {
=======
		it('Validar GET com sucesso de LaboratÃ³rios com filtro CNPJ', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET de Laboratários com filtro CNPJ Inválido', () => {
=======
		it('Validar GET de LaboratÃ³rios com filtro CNPJ InvÃ¡lido', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET com sucesso de Laboratários com filtro UUID Válido', () => {
=======
		it('Validar GET com sucesso de LaboratÃ³rios com filtro UUID VÃ¡lido', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET de Laboratários com filtro UUID Inválido', () => {
=======
		it('Validar GET de LaboratÃ³rios com filtro UUID InvÃ¡lido', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET com sucesso de Laboratários Com UUID Válido', () => {
=======
		it('Validar GET com sucesso de LaboratÃ³rios Com UUID VÃ¡lido', () => {
>>>>>>> upstream/testes
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

<<<<<<< HEAD
		it('Validar GET de Laboratários Com UUID Inválido', () => {
=======
		it('Validar GET de LaboratÃ³rios Com UUID InvÃ¡lido', () => {
>>>>>>> upstream/testes
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_laboratorios_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

<<<<<<< HEAD
		it('Validar GET com sucesso de Lista Laboratários', () => {
=======
		it('Validar GET com sucesso de Lista LaboratÃ³rios', () => {
>>>>>>> upstream/testes
			cy.consultar_lista_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('cnpj')
			})
		})

<<<<<<< HEAD
		it('Validar GET com sucesso de Lista Laboratários Credenciados', () => {
=======
		it('Validar GET com sucesso de Lista LaboratÃ³rios Credenciados', () => {
>>>>>>> upstream/testes
			cy.consultar_lista_laboratorios_credenciados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

<<<<<<< HEAD
		it('Validar GET com sucesso de Lista Nomes Laboratários', () => {
=======
		it('Validar GET com sucesso de Lista Nomes LaboratÃ³rios', () => {
>>>>>>> upstream/testes
			cy.consultar_lista_nomes_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results).to.have.length.greaterThan(0)
			})
		})

<<<<<<< HEAD
		it('Validar POST com sucesso de Laboratários', () => {
=======
		it('Validar POST com sucesso de LaboratÃ³rios', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar POST de Laboratários com Credenciado e Nutricionista Inválido', () => {
=======
		it('Validar POST de LaboratÃ³rios com Credenciado e Nutricionista InvÃ¡lido', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
				validarMensagem(
					response.body.credenciado[0],
					'deve ser um valor booleano valido',
				)
				validarMensagem(
					response.body.contatos[0].eh_nutricionista[0],
					'deve ser um valor booleano valido',
				)
			})
		})

<<<<<<< HEAD
		it('Validar POST de Laboratários com os campos em branco', () => {
=======
		it('Validar POST de LaboratÃ³rios com os campos em branco', () => {
>>>>>>> upstream/testes
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
				validarMensagem(response.body.nome[0], 'este campo nao pode estar em branco')
				validarMensagem(response.body.cnpj[0], 'este campo nao pode estar em branco')
				validarMensagem(response.body.cep[0], 'este campo nao pode estar em branco')
				validarMensagem(
					response.body.logradouro[0],
					'este campo nao pode estar em branco',
				)
				validarMensagem(response.body.numero[0], 'este campo nao pode estar em branco')
				validarMensagem(response.body.bairro[0], 'este campo nao pode estar em branco')
				validarMensagem(response.body.cidade[0], 'este campo nao pode estar em branco')
				validarMensagem(response.body.estado[0], 'este campo nao pode estar em branco')
			})
		})

<<<<<<< HEAD
		it('Validar POST de Laboratários sem informar os campos obrigatórios', () => {
=======
		it('Validar POST de LaboratÃ³rios sem informar os campos obrigatÃ³rios', () => {
>>>>>>> upstream/testes
			var dados_teste = {}
			cy.cadastrar_laboratorios(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				validarMensagem(response.body.nome[0], 'este campo e obrigatorio')
				validarMensagem(response.body.cnpj[0], 'este campo e obrigatorio')
				validarMensagem(response.body.cep[0], 'este campo e obrigatorio')
				validarMensagem(response.body.logradouro[0], 'este campo e obrigatorio')
				validarMensagem(response.body.numero[0], 'este campo e obrigatorio')
				validarMensagem(response.body.bairro[0], 'este campo e obrigatorio')
				validarMensagem(response.body.cidade[0], 'este campo e obrigatorio')
				validarMensagem(response.body.estado[0], 'este campo e obrigatorio')
				validarMensagem(response.body.credenciado[0], 'este campo e obrigatorio')
			})
		})

<<<<<<< HEAD
		it('Validar DELETE de Laboratários com sucesso', () => {
=======
		it('Validar DELETE de LaboratÃ³rios com sucesso', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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

<<<<<<< HEAD
		it('Validar DELETE de Laboratários com UUID inválido', () => {
=======
		it('Validar DELETE de LaboratÃ³rios com UUID invÃ¡lido', () => {
>>>>>>> upstream/testes
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_laboratorios(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

<<<<<<< HEAD
		it('Validar PUT com sucesso de Laboratários', () => {
=======
		it('Validar PUT com sucesso de LaboratÃ³rios', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PUT de Laboratários com Credenciado e Nutricionista Inválido', () => {
=======
		it('Validar PUT de LaboratÃ³rios com Credenciado e Nutricionista InvÃ¡lido', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
						validarMensagem(
							responsePut.body.credenciado[0],
							'deve ser um valor booleano valido',
						)
						validarMensagem(
							responsePut.body.contatos[0].eh_nutricionista[0],
							'deve ser um valor booleano valido',
						)
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PUT de Laboratários sem informar os campos obrigatórios', () => {
=======
		it('Validar PUT de LaboratÃ³rios sem informar os campos obrigatÃ³rios', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
						validarMensagem(responsePut.body.nome[0], 'este campo e obrigatorio')
						validarMensagem(responsePut.body.cnpj[0], 'este campo e obrigatorio')
						validarMensagem(responsePut.body.cep[0], 'este campo e obrigatorio')
						validarMensagem(
							responsePut.body.logradouro[0],
							'este campo e obrigatorio',
						)
						validarMensagem(responsePut.body.numero[0], 'este campo e obrigatorio')
						validarMensagem(responsePut.body.bairro[0], 'este campo e obrigatorio')
						validarMensagem(responsePut.body.cidade[0], 'este campo e obrigatorio')
						validarMensagem(responsePut.body.estado[0], 'este campo e obrigatorio')
						validarMensagem(
							responsePut.body.credenciado[0],
							'este campo e obrigatorio',
						)
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PUT de Laboratários com os campos em branco', () => {
=======
		it('Validar PUT de LaboratÃ³rios com os campos em branco', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
						validarMensagem(responsePut.body.nome[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePut.body.cnpj[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePut.body.cep[0], 'este campo nao pode estar em branco')
						validarMensagem(
							responsePut.body.logradouro[0],
							'este campo nao pode estar em branco',
						)
						validarMensagem(responsePut.body.numero[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePut.body.bairro[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePut.body.cidade[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePut.body.estado[0], 'este campo nao pode estar em branco')
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PUT de Laboratários com UUID inválido', () => {
=======
		it('Validar PUT de LaboratÃ³rios com UUID invÃ¡lido', () => {
>>>>>>> upstream/testes
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.put_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

<<<<<<< HEAD
		it('Validar PATCH com sucesso de Laboratários', () => {
=======
		it('Validar PATCH com sucesso de LaboratÃ³rios', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
				const nomeAlteradoPatch =
					'TESTES AUTOMATIZADOS - ALTERADO VIA PATCH ' + new Date().getTime()

				const dados_patch = {
					nome: nomeAlteradoPatch,
				}
				cy.patch_alterar_laboratorios(uuid_response, dados_patch).then(
					(responsePatch) => {
						expect(responsePatch.status).to.eq(200)
						expect(responsePatch.body.nome).to.eq(nomeAlteradoPatch)
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PATCH de Laboratários com Credenciado e Nutricionista Inválido', () => {
=======
		it('Validar PATCH de LaboratÃ³rios com Credenciado e Nutricionista InvÃ¡lido', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
						validarMensagem(
							responsePatch.body.credenciado[0],
							'deve ser um valor booleano valido',
						)
						validarMensagem(
							responsePatch.body.contatos[0].eh_nutricionista[0],
							'deve ser um valor booleano valido',
						)
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PATCH de Laboratários com os campos em branco', () => {
=======
		it('Validar PATCH de LaboratÃ³rios com os campos em branco', () => {
>>>>>>> upstream/testes
			var dados_teste = {
				nome: 'Testes AutomaÃ§Ã£o - ' + new Date().getTime(),
				cnpj: new Date().getTime().toString().slice(0, 14),
				cep: '05010000',
				logradouro: 'Rua Teste AutomaÃ§Ã£o',
				numero: '123',
				bairro: 'Bairro Teste',
				cidade: 'SÃ£o Paulo',
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
						validarMensagem(responsePatch.body.nome[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePatch.body.cnpj[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePatch.body.cep[0], 'este campo nao pode estar em branco')
						validarMensagem(
							responsePatch.body.logradouro[0],
							'este campo nao pode estar em branco',
						)
						validarMensagem(responsePatch.body.numero[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePatch.body.bairro[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePatch.body.cidade[0], 'este campo nao pode estar em branco')
						validarMensagem(responsePatch.body.estado[0], 'este campo nao pode estar em branco')
					},
				)

				// Deletar o laboratÃ³rio cadastrado no teste
				cy.deletar_laboratorios(uuid_response).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

<<<<<<< HEAD
		it('Validar PATCH de Laboratários com UUID inválido', () => {
=======
		it('Validar PATCH de LaboratÃ³rios com UUID invÃ¡lido', () => {
>>>>>>> upstream/testes
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			var dados_teste = {}
			cy.patch_alterar_laboratorios(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})

