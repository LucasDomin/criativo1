from flask import Flask, request

# Importa gunicorn para funcionar em produção (Vercel)
try:
    from gunicorn.app.wsgiapp import WSGIApplication
except ImportError:
    pass

app = Flask(__name__)

@app.route('/')
def index():
    return "Olá Mundo! App rodando."

@app.route('/health')
def health():
    return {"status": "ok"}

# A Vercel precisa exportar 'handler' apontando para a instância do app
handler = app