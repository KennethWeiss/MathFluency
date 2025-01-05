from flask import Blueprint, url_for, redirect, flash, current_app, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user, logout_user
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from models.user import User
from datetime import datetime, timedelta
import os

##DEBUGGING
# Add this temporarily at the top of your routes to debug
print("GOOGLE_CLIENT_ID:", os.environ.get("GOOGLE_CLIENT_ID"))
print("GOOGLE_CLIENT_SECRET:", os.environ.get("GOOGLE_CLIENT_SECRET", "exists but hidden"))

# Create blueprint for Google OAuth
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_url="oauth/google/callback",
    offline=True,
    reprompt_consent=True,  # Always ask for consent
    )

oauth_bp = Blueprint('oauth', __name__)
url_prefix = '/oauth'

# List of allowed school domain endings
ALLOWED_DOMAINS = [
    'k12.ca.us',  # California K-12 schools
    'lausd.net',  # Los Angeles schools
    'gmail.com', #for testing purposes
    '*',
    # Add more school domains as needed
]

def is_school_email(email):
    """Check if email is from an allowed school domain."""
    return True #Temporarily allow all emails
    # domain = email.split('@')[1].lower()
    # return any(domain.endswith(allowed_domain) for allowed_domain in ALLOWED_DOMAINS)

@oauth_bp.before_request
def check_session_timeout():
    """Check if the session has timed out"""
    return None #Temporarily disable session timeout
    # if current_user.is_authenticated:
    #     last_active = session.get('last_active')
    #     if last_active:
    #         last_active = datetime.fromisoformat(last_active)
    #         if datetime.utcnow() - last_active > timedelta(hours=24):
    #             logout_user()
    #             session.clear()
    #             flash('Your session has expired. Please log in again.', 'info')
    #             return redirect(url_for('auth.login'))
    #     session['last_active'] = datetime.utcnow().isoformat()


@oauth_bp.route('/login/google')
def google_login():
    if not google.authorized:
        login_url = url_for('google.login', prompt='select_account', _external=True)
        print(f"Redirecting to: {login_url}")  # Debug print
        return redirect(login_url)
       # return redirect(url_for('google.login', prompt='select_account'))
    
    try:
        resp = google.get('/oauth2/v2/userinfo')
        assert resp.ok, resp.text
        
        google_info = resp.json()
        google_id = google_info['id']
        email = google_info['email']
        
        # Verify email domain
        if not is_school_email(email):
            flash('Please use your school email address to sign in.', 'error')
            return redirect(url_for('auth.login'))
            
        # Verify email is verified by Google
        if not google_info.get('verified_email', False):
            flash('Please verify your Google email address first.', 'error')
            return redirect(url_for('auth.login'))

        username = email.split('@')[0]  # Use part before @ as username
        avatar_url = google_info.get('picture')
        
        # Get or create user
        user = User.get_or_create_google_user(
            google_id=google_id,
            email=email,
            username=username,
            avatar_url=avatar_url
        )

        # Check if user is active
        if not getattr(user, 'is_active', True):
            flash('Your account has been deactivated. Please contact support.', 'error')
            return redirect(url_for('auth.login'))
        
        # Log in the user
        login_user(user)
        flash('Successfully signed in with Google.', 'success')
        
        # Add session security measures
        session['user_id'] = user.id
        session['google_id'] = google_id
        session['last_active'] = datetime.utcnow().isoformat()
        
        # Redirect to dashboard or home page
        return redirect(url_for('main.index'))
        
    except TokenExpiredError:
        return redirect(url_for('google.login'))
    except Exception as e:
        flash(f'Failed to log in with Google: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@oauth_bp.route('/login/google/callback')
def google_callback():
    if not google.authorized:
        flash('Failed to log in with Google.', 'error')
        return redirect(url_for('auth.login'))
    return redirect(url_for('oauth.google_login'))

@oauth_bp.route('/logout')
def logout():
    """Handle user logout"""
    if google.authorized:
        # Revoke Google OAuth token
        token = google.token
        if token:
            try:
                resp = google.post(
                    'https://accounts.google.com/o/oauth2/revoke',
                    params={'token': token['access_token']},
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
            except:
                pass  # Token revocation failed, but we'll logout anyway
    
    # Clear Flask-Login
    logout_user()
    
    # Clear session data
    session.clear()
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))