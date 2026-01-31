#!/usr/bin/env python3
"""
LinkedIn Posting Script
Post content to your LinkedIn profile.
"""

import os
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

def load_tokens():
    """Load saved OAuth tokens."""
    try:
        with open('tokens.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No tokens found. Run linkedin_auth.py first!")
        exit(1)

def post_to_linkedin(text, image_path=None):
    """
    Post text (and optionally an image) to LinkedIn.
    """
    tokens = load_tokens()
    access_token = tokens['access_token']
    person_urn = tokens['person_urn']
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
    }
    
    # If we have an image, upload it first
    image_urn = None
    if image_path and os.path.exists(image_path):
        print(f"📷 Uploading image: {image_path}")
        image_urn = upload_image(access_token, person_urn, image_path)
        if image_urn:
            print(f"✅ Image uploaded: {image_urn}")
    
    # Build the post payload
    post_data = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE" if not image_urn else "IMAGE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    # Add image if uploaded
    if image_urn:
        post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
            "status": "READY",
            "media": image_urn,
        }]
    
    # Post to LinkedIn
    response = requests.post(
        'https://api.linkedin.com/v2/ugcPosts',
        headers=headers,
        json=post_data
    )
    
    if response.status_code == 201:
        result = response.json()
        post_id = result.get('id', 'unknown')
        print(f"✅ Posted successfully!")
        print(f"   Post ID: {post_id}")
        return True
    else:
        print(f"❌ Failed to post: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def upload_image(access_token, person_urn, image_path):
    """Upload an image to LinkedIn and return the asset URN."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    
    # Step 1: Register the upload
    register_data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    
    response = requests.post(
        'https://api.linkedin.com/v2/assets?action=registerUpload',
        headers=headers,
        json=register_data
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to register upload: {response.text}")
        return None
    
    upload_info = response.json()
    upload_url = upload_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = upload_info['value']['asset']
    
    # Step 2: Upload the image
    with open(image_path, 'rb') as image_file:
        upload_headers = {
            'Authorization': f'Bearer {access_token}',
        }
        upload_response = requests.put(
            upload_url,
            headers=upload_headers,
            data=image_file.read()
        )
    
    if upload_response.status_code in [200, 201]:
        return asset_urn
    else:
        print(f"❌ Failed to upload image: {upload_response.status_code}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Post to LinkedIn')
    parser.add_argument('--text', '-t', required=True, help='Post text')
    parser.add_argument('--image', '-i', help='Path to image (optional)')
    
    args = parser.parse_args()
    
    print("📝 Posting to LinkedIn...")
    print(f"   Text: {args.text[:100]}{'...' if len(args.text) > 100 else ''}")
    
    success = post_to_linkedin(args.text, args.image)
    
    if success:
        print("\n🔵 *beep boop* Post complete!")

if __name__ == '__main__':
    main()
