from flask import Blueprint, redirect, url_for, flash, current_app, session, request
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError
from models.user import User
from models.oauth import OAuth
from app import db
import os
import logging

# Enable Flask-Dance debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create blueprint for OAuth routes
oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# Create blueprint for Google OAuth
blueprint = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ],
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False
    ),
    redirect_url=None,  # Let Flask-Dance handle the redirect URL
    reprompt_consent=False  # Don't ask for consent again if already granted
)

@oauth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    logger.debug("Accessing /oauth/google/login route")
    logger.debug(f"GOOGLE_CLIENT_ID present: {bool(os.environ.get('GOOGLE_CLIENT_ID'))}")
    logger.debug(f"GOOGLE_CLIENT_SECRET present: {bool(os.environ.get('GOOGLE_CLIENT_SECRET'))}")
    
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to welcome page")
        return redirect(url_for('main.welcome'))
    
    # Store the next URL in session if provided
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    logger.debug("Starting Google OAuth flow")
    return redirect(url_for('google.login'))

@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    """Handle successful OAuth login"""
    logger.debug("OAuth authorized callback triggered")
    if not token:
        logger.warning("Failed to log in with Google: no token received")
        flash("Failed to log in with Google.", category="error")
        return False

    try:
        resp = blueprint.session.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error(f"Failed to fetch user info: {resp.text}")
            return False

        google_info = resp.json()
        google_user_id = google_info["id"]
        
        # Find or create user
        user = User.query.filter_by(google_id=google_user_id).first()
        if not user:
            logger.debug(f"No user found with Google ID {google_user_id}, checking email {google_info['email']}")
            user = User.query.filter_by(email=google_info['email']).first()
            if user:
                logger.debug("Found existing user with matching email, updating Google ID")
                user.google_id = google_user_id
                user.avatar_url = google_info.get("picture")
            else:
                logger.debug("Creating new user account")
                user = User(
                    username=google_info["name"],
                    email=google_info["email"],
                    google_id=google_user_id,
                    avatar_url=google_info.get("picture")
                )
                db.session.add(user)
            db.session.commit()
            logger.debug(f"Created new user: {user.email}")
        
        # Log in the user
        login_user(user)
        flash("Successfully logged in with Google.", category="success")
        logger.debug(f"Logged in user: {user.email}")
        
        # Return False to let Flask-Dance handle the redirect
        return False

    except (InvalidGrantError, TokenExpiredError) as e:
        logger.error(f"OAuth token error: {str(e)}")
        flash("Your login session expired. Please try again.", category="error")
        return False
    except Exception as e:
        logger.exception("Error in google_logged_in")
        flash("An error occurred during login. Please try again.", category="error")
        return False

@oauth_bp.route('/authorized/google')
def google_authorized():
    """Handle the Google OAuth callback"""
    if not google.authorized:
        logger.warning("Google OAuth not authorized in callback")
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for('auth.login'))

    try:
        # Get user info to confirm authorization worked
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error(f"Failed to get user info in callback: {resp.text}")
            flash("Failed to get user info from Google.", category="error")
            return redirect(url_for('auth.login'))
        
        # Get the next URL from session if it exists
        next_url = session.pop('next_url', None)
        if next_url:
            logger.debug(f"Redirecting to next_url: {next_url}")
            return redirect(next_url)
        
        logger.debug("Redirecting to welcome page")
        return redirect(url_for('main.welcome'))

    except Exception as e:
        logger.exception("Error in google_authorized callback")
        flash("An error occurred during login. Please try again.", category="error")
        return redirect(url_for('auth.login'))

@oauth_bp.route('/logout')
def logout():
    """Log out the user"""
    logout_user()
    # Clear the OAuth token
    token = blueprint.token
    if token:
        del blueprint.token
    return redirect(url_for('auth.login'))