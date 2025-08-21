from app import create_app

app = create_app()

if __name__ == '__main__':
    # Torna a aplicação acessível em toda a rede.
    app.run(host='0.0.0.0', debug=True)
