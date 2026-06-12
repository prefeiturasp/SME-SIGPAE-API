/// <reference types='cypress' />

describe('Validar rota de cadastro atualizar senha da aplicacao SIGPAE', () => {
	context('Rota api/cadastro/atualizar-senha/usuario_uuid/token_reset/', () => {
		it('Validar POST de atualizar senha sem dados obrigatorios', () => {
			cy.atualizar_senha_cadastro(
				'3ac751ee-f95d-4d5b-80da-437506b00000',
				'token-invalido',
				{},
			).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.exist
			})
		})

		it('Validar POST de atualizar senha com usuario_uuid e token_reset invalidos', () => {
			var dados_teste = {
				email: 'user@example.com',
				registro_funcional: 'strings',
				password: 'string',
				confirmar_password: 'string',
				cpf: 'stringstrin',
			}

			cy.atualizar_senha_cadastro(
				'3ac751ee-f95d-4d5b-80da-437506b00000',
				'token-invalido',
				dados_teste,
			).then((response) => {
				expect(response.status).to.be.oneOf([400, 404])
				expect(response.body).to.exist
			})
		})
	})
})
