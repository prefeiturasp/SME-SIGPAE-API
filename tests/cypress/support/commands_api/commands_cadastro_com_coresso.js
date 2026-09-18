/// <reference types='cypress' />

export const rotasCadastroComCoresso = {
	cadastrar: { metodo: 'POST', caminho: '' },
	alterar_email: { metodo: 'PATCH', caminho: '{username}/alterar-email/' },
	alterar_vinculo: { metodo: 'PATCH', caminho: '{username}/alterar-vinculo/' },
	finalizar_vinculo: { metodo: 'POST', caminho: '{username}/finalizar-vinculo/' },
}

Cypress.Commands.add('requisitar_cadastro_com_coresso', (operacao, opcoes = {}) => {
	const rota = rotasCadastroComCoresso[operacao]
	if (!rota) throw new Error(`Operacao CoreSSO desconhecida: ${operacao}`)
	if (rota.caminho.includes('{username}') && !opcoes.username) throw new Error('Informe o username do usuario CoreSSO.')
	return cy.request({
		method: rota.metodo,
		url: `${Cypress.config('baseUrl')}api/cadastro-com-coresso/${rota.caminho.replace('{username}', encodeURIComponent(opcoes.username))}`,
		body: opcoes.dados || {},
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		timeout: 60000,
		failOnStatusCode: false,
	})
})
