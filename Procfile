release: bash -c "until python manage.py migrate; do sleep 5; done && python manage.py createsuperuser --noinput || true"
