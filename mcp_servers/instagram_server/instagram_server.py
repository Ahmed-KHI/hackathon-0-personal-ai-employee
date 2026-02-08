"""
Instagram MCP Server
Handles Instagram Graph API interactions for Business Account posting

Actions:
- post_photo: Post single photo with caption
- post_carousel: Post multiple photos (2-10 images)
- post_story: Post to Instagram Story (24-hour content)
- get_media: Retrieve recent posts
- get_insights: Get post engagement metrics
- get_account_info: Get account details
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()

class InstagramServer:
    """Instagram Graph API MCP Server"""
    
    def __init__(self, token_path: str = "./secrets/instagram_token.json"):
        self.token_path = Path(token_path)
        self.tokens = self._load_tokens()
        self.instagram_id = self.tokens.get('instagram_business_account_id')
        self.access_token = self.tokens.get('access_token')
        self.api_version = 'v19.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
    def _load_tokens(self) -> Dict:
        """Load Instagram tokens from secrets"""
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Instagram token not found at {self.token_path}. "
                "Run setup_instagram.py first."
            )
        
        with open(self.token_path, 'r') as f:
            return json.load(f)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request to Instagram Graph API"""
        url = f"{self.base_url}/{endpoint}"
        
        # Add access token to params
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        kwargs['params'] = params
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            raise Exception(f"Instagram API Error: {error_data}")
    
    def post_photo(self, image_url: str, caption: str = "", 
                   dry_run: bool = False) -> Dict:
        """
        Post single photo to Instagram
        
        Args:
            image_url: Publicly accessible URL of image (JPG, PNG)
            caption: Caption text (max 2200 characters)
            dry_run: If True, don't actually post (testing)
        
        Returns:
            Dict with media_id and status
        
        Note: Instagram requires 2-step process:
        1. Create media container
        2. Publish container
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_photo',
                'image_url': image_url,
                'caption': caption[:100],
                'timestamp': datetime.now().isoformat()
            }
        
        # Step 1: Create media container
        container_endpoint = f"{self.instagram_id}/media"
        
        container_params = {
            'image_url': image_url,
            'caption': caption
        }
        
        container_result = self._make_request('POST', container_endpoint, params=container_params)
        container_id = container_result['id']
        
        # Wait a moment for media processing
        time.sleep(2)
        
        # Step 2: Publish media container
        publish_endpoint = f"{self.instagram_id}/media_publish"
        
        publish_params = {
            'creation_id': container_id
        }
        
        publish_result = self._make_request('POST', publish_endpoint, params=publish_params)
        
        return {
            'status': 'success',
            'media_id': publish_result['id'],
            'message': 'Photo posted to Instagram successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    def post_carousel(self, image_urls: List[str], caption: str = "",
                     dry_run: bool = False) -> Dict:
        """
        Post carousel (multiple photos) to Instagram
        
        Args:
            image_urls: List of 2-10 publicly accessible image URLs
            caption: Caption text
            dry_run: If True, don't actually post
        
        Returns:
            Dict with media_id and status
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_carousel',
                'image_count': len(image_urls),
                'caption': caption[:100],
                'timestamp': datetime.now().isoformat()
            }
        
        if len(image_urls) < 2 or len(image_urls) > 10:
            raise ValueError("Carousel must have 2-10 images")
        
        # Step 1: Create media containers for each image
        item_ids = []
        for image_url in image_urls:
            container_endpoint = f"{self.instagram_id}/media"
            container_params = {
                'image_url': image_url,
                'is_carousel_item': True
            }
            result = self._make_request('POST', container_endpoint, params=container_params)
            item_ids.append(result['id'])
            time.sleep(1)  # Rate limiting
        
        # Step 2: Create carousel container
        carousel_endpoint = f"{self.instagram_id}/media"
        carousel_params = {
            'media_type': 'CAROUSEL',
            'caption': caption,
            'children': ','.join(item_ids)
        }
        
        carousel_result = self._make_request('POST', carousel_endpoint, params=carousel_params)
        carousel_id = carousel_result['id']
        
        time.sleep(2)
        
        # Step 3: Publish carousel
        publish_endpoint = f"{self.instagram_id}/media_publish"
        publish_params = {
            'creation_id': carousel_id
        }
        
        publish_result = self._make_request('POST', publish_endpoint, params=publish_params)
        
        return {
            'status': 'success',
            'media_id': publish_result['id'],
            'image_count': len(image_urls),
            'message': 'Carousel posted to Instagram successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    def post_story(self, image_url: str, dry_run: bool = False) -> Dict:
        """
        Post to Instagram Story (24-hour ephemeral content)
        
        Args:
            image_url: Publicly accessible image URL (9:16 aspect ratio ideal)
            dry_run: If True, don't actually post
        
        Returns:
            Dict with media_id and status
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_story',
                'image_url': image_url,
                'timestamp': datetime.now().isoformat()
            }
        
        # Step 1: Create story container
        container_endpoint = f"{self.instagram_id}/media"
        
        container_params = {
            'image_url': image_url,
            'media_type': 'STORIES'
        }
        
        container_result = self._make_request('POST', container_endpoint, params=container_params)
        container_id = container_result['id']
        
        time.sleep(2)
        
        # Step 2: Publish story
        publish_endpoint = f"{self.instagram_id}/media_publish"
        publish_params = {
            'creation_id': container_id
        }
        
        publish_result = self._make_request('POST', publish_endpoint, params=publish_params)
        
        return {
            'status': 'success',
            'media_id': publish_result['id'],
            'message': 'Story posted to Instagram successfully (visible for 24 hours)',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_media(self, limit: int = 10) -> Dict:
        """
        Get recent Instagram posts
        
        Args:
            limit: Number of posts to retrieve
        
        Returns:
            Dict with media array and metadata
        """
        endpoint = f"{self.instagram_id}/media"
        
        params = {
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
            'limit': limit
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        media_items = []
        for item in result.get('data', []):
            media_items.append({
                'media_id': item.get('id'),
                'caption': item.get('caption', '')[:200],
                'media_type': item.get('media_type'),
                'media_url': item.get('media_url'),
                'permalink': item.get('permalink'),
                'timestamp': item.get('timestamp'),
                'likes': item.get('like_count', 0),
                'comments': item.get('comments_count', 0)
            })
        
        return {
            'status': 'success',
            'media': media_items,
            'count': len(media_items),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_insights(self, media_id: Optional[str] = None) -> Dict:
        """
        Get Instagram insights/analytics
        
        Args:
            media_id: Specific post ID for post-level insights (optional)
        
        Returns:
            Dict with insights data
        """
        if media_id:
            # Post-level insights
            endpoint = f"{media_id}/insights"
            params = {
                'metric': 'engagement,impressions,reach,saved'
            }
        else:
            # Account-level insights
            endpoint = f"{self.instagram_id}/insights"
            params = {
                'metric': 'impressions,reach,follower_count,profile_views',
                'period': 'day'
            }
        
        result = self._make_request('GET', endpoint, params=params)
        
        insights = {}
        for metric in result.get('data', []):
            name = metric.get('name')
            values = metric.get('values', [])
            if values:
                insights[name] = values[0].get('value', 0)
        
        return {
            'status': 'success',
            'insights': insights,
            'scope': 'post' if media_id else 'account',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_account_info(self) -> Dict:
        """Get Instagram Business Account information"""
        endpoint = f"{self.instagram_id}"
        
        params = {
            'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count,biography,website'
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        return {
            'status': 'success',
            'account_info': {
                'id': result.get('id'),
                'username': result.get('username'),
                'name': result.get('name'),
                'profile_picture': result.get('profile_picture_url'),
                'followers': result.get('followers_count', 0),
                'following': result.get('follows_count', 0),
                'posts': result.get('media_count', 0),
                'bio': result.get('biography', ''),
                'website': result.get('website', '')
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def process_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """
        Process MCP action request
        
        Args:
            action: Action name
            params: Action parameters
        
        Returns:
            Dict with action result
        """
        try:
            if action == 'post_photo':
                return self.post_photo(
                    image_url=params.get('image_url', ''),
                    caption=params.get('caption', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'post_carousel':
                return self.post_carousel(
                    image_urls=params.get('image_urls', []),
                    caption=params.get('caption', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'post_story':
                return self.post_story(
                    image_url=params.get('image_url', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'get_media':
                return self.get_media(
                    limit=params.get('limit', 10)
                )
            
            elif action == 'get_insights':
                return self.get_insights(
                    media_id=params.get('media_id')
                )
            
            elif action == 'get_account_info':
                return self.get_account_info()
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown action: {action}",
                    'supported_actions': [
                        'post_photo', 'post_carousel', 'post_story',
                        'get_media', 'get_insights', 'get_account_info'
                    ]
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': action,
                'timestamp': datetime.now().isoformat()
            }


# CLI testing
if __name__ == "__main__":
    import sys
    
    server = InstagramServer()
    
    if len(sys.argv) < 2:
        print("Instagram MCP Server")
        print("Usage:")
        print("  python instagram_server.py get_account_info")
        print("  python instagram_server.py get_media")
        print("  python instagram_server.py get_insights")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'get_account_info':
        result = server.process_action('get_account_info', {})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_media':
        result = server.process_action('get_media', {'limit': 5})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_insights':
        result = server.process_action('get_insights', {})
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown action: {action}")
