web: gunicorn --worker-class eventlet -w 1 app:app
release: python manage.py db upgrade; python manage.py load_grounds;