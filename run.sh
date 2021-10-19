# Activate virtual environment
source venv/bin/activate

# Setup secrets
source secrets.sh

# Run migrations
python manage.py migrate

# Run script
python manage.py shell < script.py 
