const { defineConfig } = require('cypress')
const allureWriter = require('@shelex/cypress-allure-plugin/writer')
const { cloudPlugin } = require('cypress-cloud/plugin');

module.exports = defineConfig({
	e2e: {
		setupNodeEvents(on, config) {
			allureWriter(on, config)
			require('./cypress/plugin/index.js')(on, config)
			on('before:browser:launch', (browser = {}, launchOptions) => {
				if (browser.name === 'chrome') {
					launchOptions.args.push('--no-sandbox')
					launchOptions.args.push('--disable-dev-shm-usage')
				}
				return launchOptions
			})
			return cloudPlugin(on, config);
		},
		baseUrl: 'https://hom-sigpae.sme.prefeitura.sp.gov.br/',
		usuario_coordenador_logistica: '07206148808',
		usuario_coordenador_codae_dilog_logistica: '53666852220',
		usuario_coordenador_supervisao_nutricao: '26088238070',
		usuario_dilog_cronograma: '10840346034',
		usuario_abastecimento: '45849486747',
		usuario_diretor_ue: '44331733637',
		usuario_codae: '01341145409',
		usuario_gpcodae: '63133486802',
		usuario_dre: '26755818011',
		senha: 'adminadmin',
		video: false,
		timeout: 60000,
		videoCompression: 0,
		retries: 2,
		screenshotOnRunFailure: true,
		chromeWebSecurity: false,
		experimentalRunAllSpecs: true,
		failOnStatusCode: false,
		specPattern: 'cypress/e2e/**/**/*.{feature,cy.{js,jsx,ts,tsx}}',
	},
})
