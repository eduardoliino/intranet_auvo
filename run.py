from app import create_app

# create_app() agora retorna 'app' e 'socketio'
app, socketio = create_app()

if __name__ == '__main__':
    # O debug será controlado pela variável de ambiente FLASK_ENV
    socketio.run(app, host='0.0.0.0')
