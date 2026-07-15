/// <reference types='cypress' />

describe('Validar classificações de dieta por ID da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_classificacoes_dieta') || '13318331325'
	const senha = Cypress.env('senha') || 'adminadmin'
	const classificacoesEncontradas = [
		{
			id: 1,
			nome: 'Tipo A',
		},
		{
			id: 5,
			nome: 'Tipo A ENTERAL',
		},
		{
			id: 7,
			nome: 'Tipo A RESTRIÇÃO DE AMINOÁCIDOS',
		},
		{
			id: 2,
			nome: 'Tipo B',
		},
		{
			id: 6,
			nome: 'Tipo C',
		},
	]

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/classificacoes-dieta/{id}/', () => {
		classificacoesEncontradas.forEach(({ id, nome }) => {
			it(`Valida GET da classificação de dieta ${id} com sucesso`, () => {
				cy.consultar_classificacao_dieta_por_id(id).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.include({ id, nome })
					expect(response.body.descricao).to.be.a('string')
				})
			})
		})
		;[3, 4].forEach((id) => {
			it(`Exibe erro ao consultar a classificação de dieta ${id} não encontrada`, () => {
				cy.consultar_classificacao_dieta_por_id(id).then((response) => {
					expect(response.status).to.eq(404)
				})
			})
		})
	})
})
