function validar_dia_semana(hoje, dias) {
	let data = hoje.add(dias, 'day')
	let diaDaSemana = data.day()

	if (diaDaSemana === 0) {
		return data.add(1, 'day')
	}
	if (diaDaSemana === 6) {
		return data.add(2, 'day')
	} else {
		return data
	}
}

module.exports = {
	validar_dia_semana,
}
