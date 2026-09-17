/// <reference types='cypress' />

// Uma entrada por operacao publicada no Swagger de CEI.
export const rotasCardapioCei = {
	listar: { metodo: 'GET', caminho: '' },
	cadastrar: { metodo: 'POST', caminho: '' },
	detalhar: { metodo: 'GET', caminho: '{uuid}/' },
	atualizar: { metodo: 'PUT', caminho: '{uuid}/' },
	parcial: { metodo: 'PATCH', caminho: '{uuid}/' },
	excluir: { metodo: 'DELETE', caminho: '{uuid}/' },
	autorizar: { metodo: 'PATCH', caminho: '{uuid}/codae-autoriza-pedido/' },
	cancelar_codae: { metodo: 'PATCH', caminho: '{uuid}/codae-cancela-pedido/' },
	questionar: { metodo: 'PATCH', caminho: '{uuid}/codae-questiona-pedido/' },
	nao_validar_dre: { metodo: 'PATCH', caminho: '{uuid}/diretoria-regional-nao-valida-pedido/' },
	validar_dre: { metodo: 'PATCH', caminho: '{uuid}/diretoria-regional-valida-pedido/' },
	cancelar_escola: { metodo: 'PATCH', caminho: '{uuid}/escola-cancela-pedido-48h-antes/' },
	iniciar: { metodo: 'PATCH', caminho: '{uuid}/inicio-pedido/' },
	conferir: { metodo: 'PATCH', caminho: '{uuid}/marcar-conferida/' },
	relatorio: { metodo: 'GET', caminho: '{uuid}/relatorio/' },
	responder: { metodo: 'PATCH', caminho: '{uuid}/terceirizada-responde-questionamento/' },
	minhas: { metodo: 'GET', caminho: 'minhas-solicitacoes/' },
	pedidos_codae: { metodo: 'GET', caminho: 'pedidos-codae/{filtro}/' },
	pedidos_dre: { metodo: 'GET', caminho: 'pedidos-diretoria-regional/{filtro}/' },
	pedidos_terceirizada: { metodo: 'GET', caminho: 'pedidos-terceirizadas/{filtro}/' },
}

Cypress.Commands.add('requisitar_alteracoes_cardapio_cei', (operacao, opcoes = {}) => {
	const rota = rotasCardapioCei[operacao]
	if (!rota) throw new Error(`Operacao CEI desconhecida: ${operacao}`)
	if (rota.caminho.includes('{uuid}') && !opcoes.uuid) throw new Error('Informe o UUID da solicitacao CEI.')
	const caminho = rota.caminho.replace('{uuid}', opcoes.uuid).replace('{filtro}', opcoes.filtro || 'sem_filtro')
	return cy.request({
		method: rota.metodo,
		url: `${Cypress.config('baseUrl')}api/alteracoes-cardapio-cei/${caminho}`,
		qs: opcoes.query,
		body: opcoes.dados,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		encoding: operacao === 'relatorio' ? 'binary' : 'utf8',
		timeout: 120000,
		failOnStatusCode: false,
	})
})
