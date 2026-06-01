/// <reference types='cypress' />

describe('Validar rota de API Token Auth da aplicacao SIGPAE', () => {
	const senha = Cypress.env('senha')

	function obterUsuariosEnv() {
		return Object.entries(Cypress.env())
			.filter(([chave, valor]) => chave.startsWith('usuario_') && valor)
			.map(([chave, valor]) => ({
				perfil: chave.replace('usuario_', ''),
				username: valor,
			}))
	}

	function validarTokenAuth(response) {
		expect(response.status).to.eq(200)
		expect(response.body).to.have.property('refresh').that.is.not.empty
		expect(response.body).to.have.property('access').that.is.not.empty
	}

	context('Rota api/api-token-auth/', () => {
		obterUsuariosEnv().forEach((usuario) => {
			it(`Validar POST com sucesso de API Token Auth para ${usuario.perfil}`, () => {
				cy.autenticar_api_token_auth(usuario.username, senha).then((response) => {
					validarTokenAuth(response)
				})
			})
		})

		it('Validar POST de API Token Auth com credenciais invalidas', () => {
			cy.autenticar_api_token_auth('usuario_invalido', 'senha_invalida').then(
				(response) => {
					expect(response.status).to.eq(401)
					expect(response.body).to.have.property('detail').that.is.not.empty
				},
			)
		})
	})
})
