class Login_SME_Localizadores {
	logo_sigpae_login = () => {
		return '.logo-sigpae > img'
	}
	campo_usuario = () => {
		return '[data-cy="login"]'
	}
	campo_senha = () => {
		return '[data-cy="password"]'
	}
	botao_acessar = () => {
		return '[data-cy="Acessar"]'
	}
	mensagem = () => {
		return '.border'
	}
	mensagem_erro = () => {
		return '.Toastify__toast--error'
	}
	mensagem_erro_campo_em_branco = () => {
		return '.error-message'
	}
}

export default Login_SME_Localizadores
