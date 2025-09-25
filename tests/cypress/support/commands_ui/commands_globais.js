Cypress.Commands.add('configurar_visualizacao', (device) => {
	switch (device) {
	case 'web':
		cy.viewport(1920, 1080)
		break
	default:
		break
	}
})