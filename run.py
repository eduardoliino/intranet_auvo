from app import create_app

app = create_app()

if __name__ == '__main__':
    # Escuta em todas interfaces de rede (0.0.0.0), na porta 8000
    app.run(debug=True, host='0.0.0.0', port=8000)
