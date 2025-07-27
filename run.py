# run.py

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Esta é a linha que torna a aplicação visível na sua rede.
    # Confirme que está exatamente assim.
    app.run(host='0.0.0.0', debug=True)
