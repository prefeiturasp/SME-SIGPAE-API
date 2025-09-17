/// <reference types='cypress' />
const dayjs = require('dayjs')
const { validar_dia_semana } = require('../../support/utils/data_utils')
var data_atual = dayjs()

describe('Validar rotas de alteracoes cardapio da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_diretor_ue')
	var senha = Cypress.config('senha')
	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context.only('Casos de teste para a rota api/alteracoes_cardapio/', () => {
		it('Validar GET de alterações cardápio com sucesso', () => {
			var id = ''
			cy.validar_alteracoes_cardapio(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.count).to.exist

				const results = response.body.results
				expect(results).to.exist

				results.forEach((result) => {
					const escola = result.escola
					const lote = escola.lote
					const contratos = lote.contratos_do_lote
					const datasIntervalo = result.datas_intervalo

					expect(escola.codigo_eol).to.exist
					expect(escola.nome).to.exist

					expect(lote.nome).to.exist
					contratos.forEach((contrato) => {
						expect(contrato.uuid).to.exist
					})

					datasIntervalo.forEach((data) => {
						expect(data.alteracao_cardapio).to.exist
					})
				})
			})
		})

		it('Validar POST de alterações cardápio com sucesso', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.allRequestResponses[0]['Response Body'].motivo).to.eq(
					dados_teste.motivo,
				)
				expect(response.allRequestResponses[0]['Response Body'].escola).to.eq(
					dados_teste.escola,
				)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.periodo_escolar,
				).to.eq(dados_teste.periodo_escolar)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_de[0],
				).to.eq(dados_teste.tipos_alimentacao_de)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_para[0],
				).to.eq(dados_teste.tipos_alimentacao_para)
				expect(
					response.allRequestResponses[0]['Response Body'].criado_em,
				).to.contains(data_atual.format('DD/MM/YYYY'))
				expect(
					response.allRequestResponses[0]['Response Body'].data_final,
				).to.contains(validar_dia_semana(data_atual, 5).format('DD/MM/YYYY'))
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.criado_em,
				).to.contains(data_atual.format('DD/MM/YYYY'))
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.data,
				).to.eq(validar_dia_semana(data_atual, 5).format('DD/MM/YYYY'))
			})
		})

		it('Validar POST com motivo em branco', () => {
			var dados_teste = {
				motivo: '',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].motivo[0],
				).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar POST com UUID inexistente no campo motivo', () => {
			var dados_teste = {
				motivo: '671f5641-ds54-4736-dsa4-7115590b7018',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].motivo[0],
				).to.eq(
					'O valor “671f5641-ds54-4736-dsa4-7115590b7018” não é um UUID válido',
				)
			})
		})

		it('Validar POST com escola em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].escola[0],
				).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar POST com UUID inexistente no campo escola', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '1ddec320-dss2-45ds-9666-3e7b3a2b903c',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].escola[0],
				).to.eq(
					'O valor “1ddec320-dss2-45ds-9666-3e7b3a2b903c” não é um UUID válido',
				)
			})
		})

		it('Validar POST com periodo escolar em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.periodo_escolar[0],
				).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar POST com UUID inexistente no campo periodo escolar', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '671f5641-54ds-56s4-5d6s-7115590b7018',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.periodo_escolar[0],
				).to.eq(
					'O valor “671f5641-54ds-56s4-5d6s-7115590b7018” não é um UUID válido',
				)
			})
		})

		it('Validar POST com tipo alimentação de em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_de[0],
				).to.eq('O valor “” não é um UUID válido')
			})
		})

		it('Validar POST com UUID inexistente no campo tipo alimentação de', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '5067e137-ds54-ds45-ds54-7f58cce93f33',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_de[0],
				).to.eq(
					'O valor “5067e137-ds54-ds45-ds54-7f58cce93f33” não é um UUID válido',
				)
			})
		})

		it('Validar POST com alteracao cardapio de em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.alteracao_cardapio[0],
				).to.eq('Este campo não pode ser nulo.')
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.alteracao_cardapio[0],
				).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar POST com UUID inexistente no campo alteracao cardapio', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '65f11f11-ds51-ds54-ds4-07c875c548f1',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.alteracao_cardapio[0],
				).to.eq(
					'O valor “65f11f11-ds51-ds54-ds4-07c875c548f1” não é um UUID válido',
				)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.alteracao_cardapio[0],
				).to.eq(
					'O valor “65f11f11-ds51-ds54-ds4-07c875c548f1” não é um UUID válido',
				)
			})
		})

		it('Validar POST com tipos alimentacao para em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_para[0],
				).to.eq('O valor “” não é um UUID válido')
			})
		})

		it('Validar POST com UUID inexistente no campo tipos alimentacao para', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '6595ebe5-fd54-ds56-ds56-6347341f9797',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.tipos_alimentacao_para[0],
				).to.eq(
					'O valor “6595ebe5-fd54-ds56-ds56-6347341f9797” não é um UUID válido',
				)
			})
		})

		it('Validar POST com qtd alunos negativo', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: -1,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.qtd_alunos[0],
				).to.eq('Certifque-se de que este valor seja maior ou igual a 0.')
			})
		})

		it('Validar POST com qtd alunos em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: '',
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].substituicoes[0]
						.qtd_alunos[0],
				).to.eq('Um número inteiro válido é exigido.')
			})
		})

		it('Validar POST com campo cancelado em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: '',
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado[0],
				).to.eq('Deve ser um valor booleano válido.')
			})
		})

		it('Validar POST com campo cancelado em com valor string', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: 'a',
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado_em[0],
				).to.eq(
					'Formato inválido para data e hora. Use um dos formatos a seguir: DD/MM/YYYY hh:mm:ss, YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].',
				)
			})
		})

		it('Validar POST com campo cancelado em com formato invalido', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: data_atual.format('DD-MM-YYYY'),
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado_em[0],
				).to.eq(
					'Formato inválido para data e hora. Use um dos formatos a seguir: DD/MM/YYYY hh:mm:ss, YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].',
				)
			})
		})

		it('Validar POST com campo cancelado em em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: '',
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado_em[0],
				).to.eq(
					'Formato inválido para data e hora. Use um dos formatos a seguir: DD/MM/YYYY hh:mm:ss, YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].',
				)
			})
		})

		it('Validar POST com campo cancelado por com valor string', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: 'a',
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado_por[0],
				).to.eq('Tipo incorreto. Esperava valor pk, recebeu str.')
			})
		})

		it('Validar POST com campo cancelado por com formato invalido', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: validar_dia_semana(data_atual, 5).format('DD-MM-YYYY'),
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].datas_intervalo[0]
						.cancelado_por[0],
				).to.eq('Tipo incorreto. Esperava valor pk, recebeu str.')
			})
		})

		it('Validar POST com campo foi solicitado fora do prazo em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: '',
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body']
						.foi_solicitado_fora_do_prazo[0],
				).to.eq('Deve ser um valor booleano válido.')
			})
		})

		it('Validar POST com terceirizada conferiu gestao em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: '',
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body']
						.terceirizada_conferiu_gestao[0],
				).to.eq('Deve ser um valor booleano válido.')
			})
		})

		it('Validar POST com terceirizada conferiu gestao em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: '',
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body']
						.eh_alteracao_com_lanche_repetida[0],
				).to.eq('Deve ser um valor booleano válido.')
			})
		})

		it('Validar POST com datas em branco', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: '',
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.data_final[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
				expect(response.body.data_inicial[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
				expect(response.body.datas_intervalo[0].data[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
			})
		})

		it('Validar POST com datas no passado', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(
					response.allRequestResponses[0]['Response Body'].non_field_errors[0],
				).to.eq('Não pode ser no passado')
			})
		})

		it('Validar POST com datas em dia nao letivo de lanche emergencial', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: '2025-11-15',
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.allRequestResponses[0]['Response Body'][0]).to.eq(
					'Não é possível solicitar Lanche Emergencial para dia(s) não letivo(s)',
				)
			})
		})

		it('Validar POST com datas em formato invalido', () => {
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: data_atual.format('DD-MM-YYYU'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then((response) => {
				expect(response.body.data_final[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
				expect(response.body.data_inicial[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
				expect(response.body.datas_intervalo[0].data[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
			})
		})
	})

	context('Casos de teste para a rota api/alteracoes_cardapio/id/', () => {
		it('Validar usuario sem permissão de Get na rota api/alteracoes_cardapio/id/', () => {
			var id = '3f42cdc6-f524-4364-af62-13a831abae5d/'
			cy.validar_alteracoes_cardapio(id).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body.detail).to.eq(
					'Você não tem permissão para executar essa ação.',
				)
			})
		})

		it('Validar GET de alterações cardápio por id inválido', () => {
			var id = '3f42cdc6-f524-4364-af62-13a831abaecd/'
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.validar_alteracoes_cardapio(id).then((response) => {
				expect(response.status).to.eq(404)
				expect(response.statusText).to.eq('Not Found')
			})
		})

		it('Validar GET de alterações cardápio por id incompleto', () => {
			var id = '3f42cdc6-f524-4364-af62-13a831abae5d'
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.validar_alteracoes_cardapio(id).then((response) => {
				cy.log(response)
				expect(response.status).to.eq(200)
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.redirects[0]).to.contains('301: https://hom-sigpae.')
			})
		})

		it('Validar GET de alterações cardápio por id com sucesso', () => {
			var id = '3f42cdc6-f524-4364-af62-13a831abae5d/'
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.validar_alteracoes_cardapio(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.criado_em).to.exist
				expect(response.body.criado_por).to.exist
				expect(response.body.data_final).to.exist
				expect(response.body.datas_intervalo).to.be.an('array').that.is.not
					.empty
				expect(response.body.foi_solicitado_fora_do_prazo).to.eq(false)
				expect(response.body.id_externo).to.eq('3F42C')
				expect(response.body.logs).to.be.an('array').that.is.not.empty
				expect(response.body.motivo.ativo).to.eq(true)
				expect(response.body.motivo.nome).to.eq('RPL - Refeição por Lanche')
				expect(response.body.motivo.uuid).to.exist
				expect(response.body.observacao).to.exist
				expect(response.body.prioridade).to.exist
				expect(response.body.rastro_dre).to.exist
				expect(response.body.rastro_escola).to.exist
				expect(response.body.rastro_lote).to.exist
				expect(response.body.rastro_terceirizada.contatos).to.be.an('array')
					.that.is.not.empty
				expect(response.body.rastro_terceirizada.contratos).to.be.an('array')
					.that.is.not.empty
				expect(response.body.rastro_terceirizada.nome_fantasia).to.exist
				expect(response.body.rastro_terceirizada.uuid).to.exist
				expect(response.body.status).is.not.null
				expect(response.body.substituicoes).to.be.an('array').that.is.not.empty
				expect(response.body.terceirizada_conferiu_gestao).to.exist
			})
		})

		it('Validar DELETE de alterações cardápio com sucesso', () => {
			usuario = Cypress.config('usuario_coordenador_logistica')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			var dados_teste = {
				motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
				escola: '671f5641-b1d4-4736-be38-7115590b7018',
				periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
				tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
				alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
				tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
				qtd_alunos: 10,
				cancelado: true,
				cancelado_justificativa: 'teste automatizado api',
				cancelado_em: null,
				cancelado_por: null,
				observacao: '<p>teste automatizado api</p>',
				foi_solicitado_fora_do_prazo: true,
				terceirizada_conferiu_gestao: true,
				eh_alteracao_com_lanche_repetida: true,
				criado_por: null,
				data: validar_dia_semana(data_atual, 5).format('YYYY-MM-DD'),
			}
			cy.cadastrar_alteracoes_cardapio(dados_teste).then(
				(response_exclusao) => {
					var id =
						response_exclusao.allRequestResponses[0]['Response Body']
							.substituicoes[0].alteracao_cardapio
					cy.excluir_alteracoes_cardapio(id).then((response) => {
						expect(response.allRequestResponses[0]['Response Status']).to.eq(
							204,
						)
						expect(response.allRequestResponses[0]['Response Body']).to.exist
					})
				},
			)
		})

		it('Validar DELETE com id inválido', () => {
			var id = '1ddec320-cd24-4cf4-9666-3e7b3ds5903c'
			cy.excluir_alteracoes_cardapio(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(404)
			})
		})
	})

	context(
		'Casos de teste para a rota api/alteracoes_cardapio/id/relatorio',
		() => {
			it('Validar GET de relatorio de alterações cardápio com sucesso', () => {
				var id = '3f42cdc6-f524-4364-af62-13a831abae5d'
				cy.validar_alteracoes_cardapio_relatorio(id).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.allRequestResponses).to.be.an('array').that.is.not
						.empty
					expect(response.allRequestResponses[0]['Response Body']).to.contain(
						'%PDF',
					)
				})
			})

			it('Validar GET de relatorio de alterações cardápio com id inválido', () => {
				var id = '3f42cdc6-f524-4364-af62-13a831adde5d'
				cy.validar_alteracoes_cardapio_relatorio(id).then((response) => {
					expect(response.status).to.eq(404)
					expect(response.allRequestResponses).to.be.an('array').that.is.not
						.empty
					expect(response.statusText).to.eq('Not Found')
				})
			})
		},
	)

	context(
		'Casos de teste para a rota /api/alteracoes-cardapio/minhas-solicitacoes/',
		() => {
			it('Validar GET minhas solicitacoes com sucesso', () => {
				var usuario = Cypress.config('usuario_diretor_ue')
				var senha = Cypress.config('senha')
				cy.autenticar_login(usuario, senha)
				cy.validar_alteracoes_cardapio_minhas_solicitacoes().then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body.count).to.exist

						const results = response.body.results
						expect(results).to.exist

						results.forEach((result) => {
							const escola = result.escola
							const lote = escola.lote
							const contratos = lote.contratos_do_lote
							const datasIntervalo = result.datas_intervalo

							expect(escola.codigo_eol).to.exist
							expect(escola.nome).to.exist

							expect(lote.nome).to.exist
							contratos.forEach((contrato) => {
								expect(contrato.uuid).to.exist
							})

							datasIntervalo.forEach((data) => {
								expect(data.alteracao_cardapio).to.exist
							})
						})
					},
				)
			})
		},
	)
})
