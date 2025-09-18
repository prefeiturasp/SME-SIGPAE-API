/// <reference types='cypress' />

describe('Validar rotas de cadastro de produtos edital da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_diretor_ue')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/cadastro-produtos-edital/', () => {
		it('Validar GET de produtos edital com sucesso', () => {
			var parametros = ''
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.exist
				expect(response.body).to.have.property('previous').that.null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
			})
		})

		it('Validar GET de produtos edital por nome', () => {
			var parametros = '?nome=Teste Automação Novo Produto'
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.null
				expect(response.body).to.have.property('previous').that.null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
			})
		})

		it('Validar GET de produtos edital por nome não existente', () => {
			var parametros = '?nome=Produto não existente'
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').to.eq(0)
				expect(response.body).to.have.property('next').that.null
				expect(response.body).to.have.property('previous').that.null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.to.be.empty
			})
		})

		it('Validar GET de produtos edital por data de cadastro', () => {
			var parametros = '?data_cadastro=13/03/2025'
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.null
				expect(response.body).to.have.property('previous').that.null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
			})
		})

		it('Validar GET de produtos edital por data de cadastro inválida', () => {
			var parametros = '?data_cadastro=13/03'
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.data_cadastro[0]).to.eq('Informe uma data válida.')
			})
		})

		it('Validar GET de produtos edital por status', () => {
			var status = Math.random() < 0.5 ? 'Ativo' : 'Inativo'
			var parametros = '?status=' + status
			cy.consultar_produtos_edital(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('previous').that.null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
			})
		})

		it('Validar POST de cadastro produto edital com sucesso', () => {
			var dados_teste = {
				nome: 'Teste Automação Novo Produto Cadastrado',
				ativo: 'True',
				tipo_produto: 'TERCEIRIZADA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body['ativo']).to.eq('True')
				expect(response.body['tipo_produto']).to.eq('TERCEIRIZADA')
			})
		})

		it('Validar POST de cadastro produto edital existente', () => {
			var dados_teste = {
				nome: 'Teste Automação',
				ativo: 'True',
				tipo_produto: 'TERCEIRIZADA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq('Item já cadastrado.')
			})
		})

		it('Validar POST de cadastro produto edital com tipo de produto inválido', () => {
			var dados_teste = {
				nome: 'Teste Automação',
				ativo: 'True',
				tipo_produto: 'TERCEIRA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.tipo_produto[0]).to.contains(
					'"TERCEIRA" não é um escolha válida.',
				)
			})
		})

		it('Validar POST de cadastro produto edital sem o campo nome', () => {
			var dados_teste = {
				ativo: 'True',
				tipo_produto: 'TERCEIRA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome).to.contains('Este campo é obrigatório.')
			})
		})

		it('Validar POST de cadastro produto edital com o campo nome em branco', () => {
			var dados_teste = {
				nome: '',
				ativo: 'True',
				tipo_produto: 'TERCEIRA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar POST de cadastro produto edital sem o campo ativo', () => {
			var dados_teste = {
				nome: 'Teste Automação',
				tipo_produto: 'TERCEIRA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.ativo).to.contains('Este campo é obrigatório.')
			})
		})

		it('Validar POST de cadastro produto edital com o campo ativo em branco', () => {
			var dados_teste = {
				nome: 'Teste Automação',
				ativo: '',
				tipo_produto: 'TERCEIRA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.ativo[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar GET de produto com UUID válido com sucesso', () => {
			var uuid = '32e04f4b-7b10-4a73-afbc-d2550c3b1511/'
			cy.validar_produto_edital(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid').that.exist
				expect(response.body).to.have.property('nome').that.exist
				expect(response.body).to.have.property('status').that.exist
				expect(response.body).to.have.property('criado_em').that.exist
			})
		})

		it('Validar GET de produto com UUID inválido', () => {
			var uuid = 'b2dbaff4-dbd3-45b8-b67c-57ff4b5ad35b/'
			cy.validar_produto_edital(uuid).then((response) => {
				expect(response.status).to.eq(404)
				expect(response.body).to.exist
			})
		})

		it('Validar GET da lista completa de logística com sucesso', () => {
			cy.validar_lista_completa_logistica().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
			})
		})

		it('Validar GET da lista de nomes dos produtos com sucesso', () => {
			cy.validar_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
			})
		})

		it('Validar GET da lista de nomes dos produtos logística com sucesso', () => {
			cy.validar_lista_nomes_logistica().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
			})
		})

		it('Validar GET de todos os produtos logística com sucesso', () => {
			cy.validar_produtos_logistica().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.exist
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('criado_em').that.exist
				expect(primeiro_resultado).to.have.property('status').that.exist
			})
		})

		it('Validar PUT de produto edital alterado com sucesso.', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO COM SUCESSO',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = '5a192d62-999f-4805-89ed-91e9a88cc0b4/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body['ativo']).to.eq('True')
				expect(response.body['tipo_produto']).to.eq('TERCEIRIZADA')
			})
		})

		it('Validar PUT de produto edital já cadastrado', () => {
			var dados_teste = {
				nome: 'PRODUTO DE TESTE AUTOMAÇÃO - VIA PATCH',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = 'e6d735aa-8a99-491b-9a14-0e2288ff1d0f/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq('Item já cadastrado.')
			})
		})

		it('Validar PUT de produto edital com tipo de produto inválido', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRA',
			}
			var uuid = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.tipo_produto[0]).to.contains(
					'TERCEIRA" não é um escolha válida.',
				)
			})
		})

		it('Validar PUT de produto edital sem o campo nome', () => {
			var dados_teste = {
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome).to.contains('Este campo é obrigatório.')
			})
		})

		it('Validar PUT de produto edital com o campo nome em branco', () => {
			var dados_teste = {
				nome: '',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar PUT de produto edital sem o campo ativo', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.ativo[0]).to.eq('Este campo é obrigatório.')
			})
		})

		it('Validar PUT de produto edital com o campo ativo em branco', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO',
				ativo: '',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
			cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.ativo[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar DELETE de produto edital com sucesso', () => {
			var dados_teste = {
				nome: 'Automação Produto Para Exclusão',
				ativo: 'True',
				tipo_produto: 'TERCEIRIZADA',
			}
			cy.cadastrar_produto_edital(dados_teste).then((response_inclusao) => {
				expect(response_inclusao.status).to.eq(201)
				var parametros = '?nome=' + dados_teste.nome
				cy.consultar_produtos_edital(parametros).then((response) => {
					expect(response.status).to.eq(200)
					var uuid = response.body.results[0].uuid
					cy.excluir_produto_edital(uuid).then((response) => {
						expect(response.status).to.eq(204)
					})
				})
			})
		})

		it('Validar DELETE de produto edital não existente', () => {
			var uuid = 'b2dbaff4-dbd3-45b8-b67c-57ff4b5ad35b/'
			cy.excluir_produto_edital(uuid).then((response) => {
				expect(response.status).to.eq(404)
				expect(response.body).to.exist
			})
		})

		it('Validar PATCH de produto edital alterado com sucesso.', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO VIA PATCH COM SUCESSO',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = 'b38437a5-ec30-406a-84cf-be4109a8651a/'
			cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body['ativo']).to.eq('True')
				expect(response.body['tipo_produto']).to.eq('TERCEIRIZADA')
			})
		})

		it('Validar PATCH de produto edital já cadastrado', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO VIA PUT - AUTOMAÇÃO',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = 'cbd9638c-b972-4184-814d-cc48e95ab7a4/'
			cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq('Item já cadastrado.')
			})
		})

		it('Validar PATCH de produto edital com tipo de produto inválido', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRA',
			}
			var uuid = 'b38437a5-ec30-406a-84cf-be4109a8651a/'
			cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.tipo_produto[0]).to.contains(
					'\"TERCEIRA\" não é um escolha válida.',
				)
			})
		})

		it('Validar PATCH de produto edital com o campo nome em branco', () => {
			var dados_teste = {
				nome: '',
				ativo: 'Ativo',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = 'b38437a5-ec30-406a-84cf-be4109a8651a/'
			cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar PATCH de produto edital com o campo ativo em branco', () => {
			var dados_teste = {
				nome: 'PRODUTO ATUALIZADO',
				ativo: '',
				tipo_produto: 'TERCEIRIZADA',
			}
			var uuid = 'b38437a5-ec30-406a-84cf-be4109a8651a/'
			cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.ativo[0]).to.contains(
					'Este campo não pode estar em branco.',
				)
			})
		})
	})
})

afterEach(function () {
	if (
		this.currentTest.title ===
		'Validar PUT de produto edital alterado com sucesso.'
	) {
		var dados_teste = {
			nome: 'PRODUTO CRIADO',
			ativo: 'Ativo',
			tipo_produto: 'TERCEIRIZADA',
		}
		var uuid = '5a192d62-999f-4805-89ed-91e9a88cc0b4/'
		cy.atualizar_produto_edital(uuid, dados_teste).then((response) => {
			expect(response.status).to.eq(200)
		})
		cy.log('Alterando o produto para o estado original, após o PUT com sucesso')
	}
	if (
		this.currentTest.title ===
		'Validar POST de cadastro produto edital com sucesso'
	) {
		var parametros = '?nome=Teste Automação Novo Produto Cadastrado'
		cy.consultar_produtos_edital(parametros).then((response) => {
			var uuid = response.body.results[0].uuid
			cy.excluir_produto_edital(uuid).then((response) => {
				expect(response.status).to.eq(204)
			})
			cy.log('Excluíndo o produto após o POST com sucesso')
		})
	}
	if (
		this.currentTest.title ===
		'Validar PATCH de produto edital alterado com sucesso.'
	) {
		var dados_teste = {
			nome: 'PRODUTO ATUALIZADO VIA PATCH',
			ativo: 'Ativo',
			tipo_produto: 'TERCEIRIZADA',
		}
		var uuid = 'b38437a5-ec30-406a-84cf-be4109a8651a/'
		cy.atualizar_produto_edital_patch(uuid, dados_teste).then((response) => {
			expect(response.status).to.eq(200)
		})
		cy.log(
			'Alterando o produto para o estado original, após o PATCH com sucesso',
		)
	}
})
