# Activate virtual environment
source venv/bin/activate

# Setup secrets
source secrets.sh

# Run script
python manage.py shell < script.py 
