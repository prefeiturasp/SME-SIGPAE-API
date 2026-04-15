/// <reference types='cypress' />

describe('Validar rotas da aplicação SIGPAE - ', () => {
	var usuario = Cypress.config('usuario_dre')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para as rotas /api/editais-contratos/', () => {
		it('Validar GET com sucesso de Editais Contratos', () => {
			cy.consultar_editais_contratos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('numero')
				expect(response.body.results[0]).to.have.property('tipo_contratacao')
				expect(response.body.results[0]).to.have.property('processo')
				expect(response.body.results[0]).to.have.property('objeto')
				expect(response.body.results[0]).to.have.property('eh_imr')
			})
		})

		it('Validar GET de Editais Contratos com UUID válido', () => {
			var uuid = 'e40ccae2-2080-4510-aeee-d1b8dcacc3b8'
			cy.consultar_editais_contratos_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('numero')
				expect(response.body).to.have.property('tipo_contratacao')
				expect(response.body).to.have.property('processo')
				expect(response.body).to.have.property('objeto')
				expect(response.body).to.have.property('eh_imr')
			})
		})

		it('Validar GET de Editais Contratos com UUID inválido', () => {
			var uuid = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
			cy.consultar_editais_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar POST de Editais Contratos com sucesso', () => {
			var dados_teste = {
				numero: '987' + new Date().getTime(),
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/06/2025',
				data_final: '25/06/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Teste',
				eh_imr: false,
			}
			cy.cadastrar_editais_contratos(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid = response.body.uuid

				cy.deletar_editais_contratos(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de Editais Contratos com sucesso', () => {
			var dados_teste = {
				numero: '987' + new Date().getTime(),
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/06/2025',
				data_final: '25/06/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Teste',
				eh_imr: false,
			}
			cy.cadastrar_editais_contratos(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid = response.body.uuid

				cy.deletar_editais_contratos(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de Editais Contratos com UUID não existente', () => {
			var uuid = 'b2dbaff4-dbd3-45b8-b67c-57ff4b5ad35b/'
			cy.deletar_editais_contratos(uuid).then((response) => {
				expect(response.status).to.eq(404)
				expect(response.body).to.exist
			})
		})

		it('Validar PUT de Editais Contratos com sucesso', () => {
			var dados_teste = {
				numero: '987' + new Date().getTime(),
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/06/2025',
				data_final: '25/06/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Teste',
				eh_imr: false,
			}
			var dados_teste_alterados = {
				numero: dados_teste.numero,
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/06/2025',
				data_final: '25/06/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Alterado!',
				eh_imr: true,
			}
			cy.cadastrar_editais_contratos(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid = response.body.uuid
				var uuid_lotes = response.body.contratos[0].uuid

				cy.atualizar_editais_contratos(
					uuid,
					uuid_lotes,
					dados_teste_alterados,
				).then((response_put) => {
					expect(response_put.status).to.eq(200)
					expect(response_put.body.uuid).to.eq(uuid)
					expect(response_put.body)
						.to.have.property('numero')
						.equals(dados_teste_alterados.numero)
					expect(response_put.body).to.have.property('eh_imr').equals(true)
				})
				cy.deletar_editais_contratos(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
				})
			})
		})

		it('Validar PATCH de Editais Contratos com sucesso', () => {
			var dados_teste = {
				numero: '987' + new Date().getTime(),
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/10/2025',
				data_final: '25/10/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Teste',
				eh_imr: false,
			}
			var dados_teste_alterados = {
				numero: dados_teste.numero,
				lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
				terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
				diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
				data_inicial: '25/10/2025',
				data_final: '25/10/2026',
				processo: '123',
				data_proposta: '21/08/2025',
				encerrado: false,
				data_hora_encerramento: null,
				ata: '',
				numero_pregao: '',
				numero_chamada_publica: '',
				edital: 31,
				modalidade: null,
				numero: 'AUTOMAÇÃO' + new Date().getTime(),
				tipo_contratacao: 'Teste',
				processo: '123456',
				objeto: 'Objeto Alterado PATCH!',
				eh_imr: true,
			}
			cy.cadastrar_editais_contratos(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid = response.body.uuid
				var uuid_lotes = response.body.contratos[0].uuid

				cy.atualizar_editais_contratos(
					uuid,
					uuid_lotes,
					dados_teste_alterados,
				).then((response_put) => {
					expect(response_put.status).to.eq(200)
					expect(response_put.body.uuid).to.eq(uuid)
					expect(response_put.body)
						.to.have.property('numero')
						.equals(dados_teste_alterados.numero)
					expect(response_put.body).to.have.property('eh_imr').equals(true)
				})
				cy.deletar_editais_contratos(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
				})
			})
		})
	})
})
