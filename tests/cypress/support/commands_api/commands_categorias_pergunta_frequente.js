/// <reference types='cypress' />
export const rotasCategoriasPerguntaFrequente = {
	listar: ['GET', ''], cadastrar: ['POST', ''],
	detalhar: ['GET', '{uuid}/'], atualizar: ['PUT', '{uuid}/'],
	parcial: ['PATCH', '{uuid}/'], excluir: ['DELETE', '{uuid}/'],
	opcoes: ['GET', 'opcoes/'], perguntas: ['GET', 'perguntas-por-categoria/'],
}
Cypress.Commands.add('requisitar_categorias_pergunta_frequente', (operacao, opcoes = {}) => {
	const rota = rotasCategoriasPerguntaFrequente[operacao]
	if (!rota) throw new Error(`Operacao de categoria desconhecida: ${operacao}`)
	if (rota[1].includes('{uuid}') && !opcoes.uuid) throw new Error('Informe o UUID da categoria')
	return cy.request({
		method: rota[0],
		url: `${Cypress.config('baseUrl')}api/categorias-pergunta-frequente/${rota[1].replace('{uuid}', opcoes.uuid)}`,
		qs: opcoes.query, body: opcoes.dados,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		timeout: 60000, failOnStatusCode: false,
	})
})
