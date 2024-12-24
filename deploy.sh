# Pull the latest changes from the development branch
git fetch --all
git reset --hard origin/development

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart Django app and Celery processes
pm2 restart django_app
pm2 restart celery_worker
pm2 restart celery_beat

echo "Deployment completed successfully!"
