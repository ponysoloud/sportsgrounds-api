web: gunicorn app:app
release: python manage.py db upgrade; python manage.py populate_activities; python manage.py update_grounds;