#!/usr/bin/env python3
"""
LinkedIn OAuth Authentication Script
Run this once to get access tokens for posting.
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8080/callback')

# Scopes for posting to personal profile
SCOPES = ['openid', 'profile', 'w_member_social']

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            auth_code = query['code'][0]
            print(f"\n✅ Got authorization code!")
            
            # Exchange code for access token
            token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Get user profile to store the person URN
                headers = {'Authorization': f"Bearer {tokens['access_token']}"}
                profile_response = requests.get(
                    'https://api.linkedin.com/v2/userinfo',
                    headers=headers
                )
                
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    tokens['person_urn'] = f"urn:li:person:{profile['sub']}"
                    tokens['name'] = profile.get('name', 'Unknown')
                    print(f"✅ Authenticated as: {tokens['name']}")
                
                # Save tokens
                with open('tokens.json', 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                print(f"✅ Tokens saved to tokens.json")
                print(f"   Access token expires in: {tokens.get('expires_in', 'unknown')} seconds")
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>&#x2705; LinkedIn Connected!</h1>
                    <p>You can close this window and return to your terminal.</p>
                    <p>R2-D2 is ready to post! <em>beep boop</em></p>
                    </body></html>
                """)
            else:
                print(f"❌ Token exchange failed: {response.text}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Token exchange failed")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code received")
        
        # Shutdown server after handling
        raise KeyboardInterrupt

    def log_message(self, format, *args):
        pass  # Suppress logging

def main():
    print("🔗 LinkedIn OAuth Setup")
    print("=" * 40)
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}"
    
    print(f"\nOpening browser for authorization...")
    print(f"If it doesn't open, visit this URL:\n{auth_url}\n")
    
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print("Waiting for authorization callback...")
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    
    try:
        server.handle_request()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    
    print("\n✅ Setup complete!")

if __name__ == '__main__':
    main()
