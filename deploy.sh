# Pull the latest changes from the development branch
git fetch --all
git reset --hard origin/development

# Path to the .env file
ENV_FILE="$HOME/../etc/api_projects/.env"
BASHRC="$HOME/.bashrc"  # Target file to store variables persistently

# Check if the .env file exists
if [ -f "$ENV_FILE" ]; then
  # Backup the original .bashrc
  cp "$BASHRC" "$BASHRC.bak"

  # Remove old variables from .bashrc
  sed -i '/# BEGIN .env variables/,/# END .env variables/d' "$BASHRC"

  # Add a marker to indicate .env variables
  echo "# BEGIN .env variables" >> "$BASHRC"

  # Read each line and process valid key=value pairs
  while IFS='=' read -r key value; do
    # Skip empty lines and comments
    if [[ -n "$key" && ! "$key" =~ ^# ]]; then
      # Export the variable and append it to .bashrc
      export $key=$value
      echo "export $key=$value" >> "$BASHRC"
    fi
  done < "$ENV_FILE"

  # End marker
  echo "# END .env variables" >> "$BASHRC"

  echo "Environment variables loaded and saved to $BASHRC."
else
  echo "Environment file not found: $ENV_FILE"
fi

source $BASHRC

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate --settings=api.config.settings.development

# Restart Django app and Celery processes
pm2 restart django_app
pm2 restart celery_worker
pm2 restart celery_beat

echo "Deployment completed successfully!"

