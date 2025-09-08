#!/usr/bin/env python3
"""Test WordPress.com connection using environment variables."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_wordpress_connection():
    """Test connection to WordPress.com."""
    
    print("WordPress.com Connection Test")
    print("=" * 40)
    
    # Get credentials from environment
    site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
    oauth_token = os.getenv('WORDPRESS_OAUTH_TOKEN')
    
    if not site_domain:
        print("FAILED: WORDPRESS_SITE_DOMAIN not found in .env")
        return False
    
    if not oauth_token:
        print("FAILED: WORDPRESS_OAUTH_TOKEN not found in .env")
        return False
    
    print(f"Testing site: {site_domain}")
    print(f"Token length: {len(oauth_token)} chars")
    
    # Test endpoints
    base_url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_domain}"
    headers = {"Authorization": f"Bearer {oauth_token}"}
    
    tests = [
        ("Site info", ""),
        ("User info", "/../../me"),
        ("Posts", "/posts?per_page=1"),
    ]
    
    print("\nTest Results:")
    print("-" * 30)
    
    success_count = 0
    for name, endpoint in tests:
        try:
            url = base_url + endpoint
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"OK {name}")
                if endpoint == "":
                    data = response.json()
                    print(f"   Site: {data.get('name', 'Unknown')}")
                elif endpoint == "/../../me":
                    data = response.json()
                    print(f"   User: {data.get('display_name', 'Unknown')}")
                success_count += 1
            elif response.status_code == 403:
                print(f"FAILED {name}: Permission denied (check token scope)")
            elif response.status_code == 404:
                print(f"FAILED {name}: Not found (check site domain)")
            else:
                print(f"WARNING {name}: Status {response.status_code}")
                
        except requests.RequestException as e:
            print(f"ERROR {name}: Connection error - {str(e)[:50]}...")
    
    print("-" * 30)
    
    if success_count == len(tests):
        print("SUCCESS: All tests passed! Ready to migrate.")
        
        # Create a test draft post
        test_create_post(base_url, headers)
        return True
    else:
        print("FAILED: Some tests failed. Check your .env file.")
        return False


def test_create_post(base_url, headers):
    """Test creating a draft post."""
    
    print("\nTesting post creation...")
    
    test_post = {
        "title": "Migration Test - DELETE ME",
        "content": "This is a test post created by the migration tool. You can safely delete this.",
        "status": "draft"
    }
    
    try:
        response = requests.post(
            f"{base_url}/posts/new",
            headers=headers,
            json=test_post,
            timeout=10
        )
        
        if response.status_code == 200:
            post = response.json()
            print(f"SUCCESS: Test post created (ID: {post.get('ID')})")
            print(f"   Edit at: https://wordpress.com/post/{os.getenv('WORDPRESS_SITE_DOMAIN')}/{post.get('ID')}")
        else:
            print(f"WARNING: Could not create test post: {response.status_code}")
            
    except Exception as e:
        print(f"WARNING: Error creating test post: {str(e)}")


if __name__ == "__main__":
    test_wordpress_connection()