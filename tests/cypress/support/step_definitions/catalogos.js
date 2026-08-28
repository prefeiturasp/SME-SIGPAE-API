import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const comandos = {
	motivos_inclusao_normal: {
		listar: 'consultar_motivos_inclusao_normal',
		buscar: 'consultar_motivos_inclusao_normal_por_uuid',
	},
	motivos_suspensao_cardapio: {
		listar: 'consultar_motivos_suspensao_cardapio',
		buscar: 'consultar_motivos_suspensao_cardapio_por_uuid',
	},
	motivos_alteracao_cardapio: {
		listar: 'consultar_motivos_alteracao_cardapio',
		buscar: 'consultar_motivos_alteracao_cardapio_por_uuid',
	},
}

Given('que estou autenticado como CODAE para consultar catalogos', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto a lista do catalogo {string}', function (catalogo) {
	cy[comandos[catalogo].listar]().then((response) => {
		this.response = response
	})
})

When('consulto um item existente do catalogo {string}', function (catalogo) {
	const comando = comandos[catalogo]
	cy[comando.listar]().then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy[comando.buscar](this.uuid).then((response) => {
			this.response = response
		})
	})
})

When('consulto o catalogo {string} por UUID invalido', function (catalogo) {
	cy[comandos[catalogo].buscar]('3ac751ee-f95d-4d5b-80da-437506b00000')
		.then((response) => {
			this.response = response
		})
})

Then('o catalogo retorna status 200 e campos {string}', function (campos) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys(...campos.split(','))
})

Then('o item do catalogo retorna status 200 e campos {string}', function (campos) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys(...campos.split(','))
	expect(this.response.body.uuid).to.eq(this.uuid)
})

Then('o item do catalogo retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
