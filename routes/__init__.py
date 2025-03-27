from flask import Blueprint

# Import blueprints from different route modules
from .home import home_bp
from .trainer_routes import trainer_bp
from .auth import auth_bp

# List of blueprints to register in app.py
all_blueprints = [home_bp, trainer_bp, auth_bp]