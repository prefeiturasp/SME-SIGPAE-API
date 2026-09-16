import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const usuarioUuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
const tokenReset = 'token-invalido'

When('solicito a atualizacao de senha sem os dados obrigatorios', function () {
	cy.atualizar_senha_cadastro(usuarioUuid, tokenReset, {}).then((response) => {
		this.response = response
	})
})

When('solicito a atualizacao de senha com usuario e token invalidos', function () {
	const dados = {
		email: 'user@example.com',
		registro_funcional: 'strings',
		password: 'string',
		confirmar_password: 'string',
		cpf: 'stringstrin',
	}
	cy.atualizar_senha_cadastro(usuarioUuid, tokenReset, dados).then((response) => {
		this.response = response
	})
})

Then('a atualizacao de senha deve retornar status 400 e um corpo de resposta', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.exist
})

Then('a atualizacao de senha deve retornar erro de validacao ou recurso nao encontrado', function () {
	expect(this.response.status).to.be.oneOf([400, 404])
	expect(this.response.body).to.exist
})
