# Tracker: Saúde, Hidratação e Calculadora de ICMS

Pequeno projeto em Flask que registra altura, peso e consumo de água; exibe gráficos com Chart.js e inclui uma calculadora de ICMS.

## Requisitos
- Python 3.8+
- Windows (testado), também funciona em macOS/Linux

## Instalação (sugestão)
No terminal (pasta do projeto):

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS / Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

## Executar
```bash
python app.py
```
Abra no navegador: http://127.0.0.1:5000

## Estrutura
- `app.py` — servidor Flask e rotas
- `models/` — local para modelos (arquivo placeholder)
- `database/app.db` — criado automaticamente
- `templates/index.html` — interface principal
- `static/js/main.js` — lógica frontend e Charts
- `static/css/style.css` — estilos

## Uso
- Preencha o formulário com altura (cm), peso (kg) e água (L).
- Veja o histórico, gráficos e indicadores no dashboard.
- Use a calculadora de ICMS (insira valor e alíquota).

## Notas
- Dados são armazenados localmente em `database/app.db`.
- Para remoção de dados, apague o arquivo `database/app.db` e reinicie a aplicação.
