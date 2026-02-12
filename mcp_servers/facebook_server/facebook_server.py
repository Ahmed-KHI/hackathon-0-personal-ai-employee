"""
Facebook MCP Server
Handles Facebook Graph API interactions for page posting and insights

Actions:
- post_message: Post text update to Facebook Page
- post_photo: Post photo with caption to Facebook Page
- get_posts: Retrieve recent posts
- get_insights: Get page engagement metrics
- get_page_info: Get page details
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FacebookServer:
    """Facebook Graph API MCP Server"""
    
    def __init__(self, token_path: str = "./secrets/facebook_token.json"):
        self.token_path = Path(token_path)
        self.tokens = self._load_tokens()
        self.page_id = self.tokens.get('page_id')
        self.access_token = self.tokens.get('page_access_token')
        self.api_version = 'v19.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
    def _load_tokens(self) -> Dict:
        """Load Facebook tokens from secrets"""
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Facebook token not found at {self.token_path}. "
                "Run setup_facebook.py first."
            )
        
        with open(self.token_path, 'r') as f:
            return json.load(f)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request to Facebook Graph API"""
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
            raise Exception(f"Facebook API Error: {error_data}")
    
    def post_message(self, message: str, link: Optional[str] = None, 
                     dry_run: bool = False) -> Dict:
        """
        Post text message to Facebook Page
        
        Args:
            message: Text content to post
            link: Optional URL to include
            dry_run: If True, don't actually post (testing)
        
        Returns:
            Dict with post_id and created_time
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_message',
                'message': message[:100],
                'link': link,
                'timestamp': datetime.now().isoformat()
            }
        
        endpoint = f"{self.page_id}/feed"
        
        data = {
            'message': message,
            'published': True  # Ensure post is published publicly, not as draft
        }
        if link:
            data['link'] = link
        
        result = self._make_request('POST', endpoint, data=data)
        
        return {
            'status': 'success',
            'post_id': result.get('id'),
            'message': 'Post published successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    def post_photo(self, photo_url: str, message: str = "", 
                   dry_run: bool = False) -> Dict:
        """
        Post photo to Facebook Page
        
        Args:
            photo_url: URL of photo to post
            message: Caption for the photo
            dry_run: If True, don't actually post
        
        Returns:
            Dict with post_id and created_time
        """
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_photo',
                'photo_url': photo_url,
                'message': message[:100],
                'timestamp': datetime.now().isoformat()
            }
        
        endpoint = f"{self.page_id}/photos"
        
        data = {
            'url': photo_url,
            'message': message,
            'published': True  # Ensure photo is published publicly, not as draft
        }
        
        result = self._make_request('POST', endpoint, data=data)
        
        return {
            'status': 'success',
            'post_id': result.get('post_id'),
            'photo_id': result.get('id'),
            'message': 'Photo published successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_posts(self, limit: int = 10) -> Dict:
        """
        Get recent posts from Facebook Page
        
        Args:
            limit: Number of posts to retrieve
        
        Returns:
            Dict with posts array and metadata
        """
        endpoint = f"{self.page_id}/feed"
        
        params = {
            'fields': 'id,message,created_time,permalink_url,likes.summary(true),comments.summary(true),shares',
            'limit': limit
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        posts = []
        for post in result.get('data', []):
            posts.append({
                'post_id': post.get('id'),
                'message': post.get('message', '')[:200],
                'created_time': post.get('created_time'),
                'url': post.get('permalink_url'),
                'likes': post.get('likes', {}).get('summary', {}).get('total_count', 0),
                'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                'shares': post.get('shares', {}).get('count', 0)
            })
        
        return {
            'status': 'success',
            'posts': posts,
            'count': len(posts),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_insights(self, metrics: Optional[list] = None, period: str = 'day') -> Dict:
        """
        Get Facebook Page insights/analytics
        
        Args:
            metrics: List of metrics to retrieve (default: engagement metrics)
            period: Time period ('day', 'week', 'days_28')
        
        Returns:
            Dict with insights data
        """
        if metrics is None:
            metrics = [
                'page_impressions',
                'page_engaged_users',
                'page_post_engagements',
                'page_fans',
                'page_views_total'
            ]
        
        endpoint = f"{self.page_id}/insights"
        
        params = {
            'metric': ','.join(metrics),
            'period': period
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        insights = {}
        for metric in result.get('data', []):
            name = metric.get('name')
            values = metric.get('values', [])
            if values:
                insights[name] = values[-1].get('value', 0)
        
        return {
            'status': 'success',
            'insights': insights,
            'period': period,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_page_info(self) -> Dict:
        """Get Facebook Page information"""
        endpoint = f"{self.page_id}"
        
        params = {
            'fields': 'id,name,category,fan_count,followers_count,link,about,website'
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        return {
            'status': 'success',
            'page_info': {
                'id': result.get('id'),
                'name': result.get('name'),
                'category': result.get('category'),
                'likes': result.get('fan_count', 0),
                'followers': result.get('followers_count', 0),
                'url': result.get('link'),
                'about': result.get('about', ''),
                'website': result.get('website', '')
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def process_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """
        Process MCP action request
        
        Args:
            action: Action name (post_message, post_photo, get_posts, etc.)
            params: Action parameters
        
        Returns:
            Dict with action result
        """
        try:
            if action == 'post_message':
                return self.post_message(
                    message=params.get('message', ''),
                    link=params.get('link'),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'post_photo':
                return self.post_photo(
                    photo_url=params.get('photo_url', ''),
                    message=params.get('message', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'get_posts':
                return self.get_posts(
                    limit=params.get('limit', 10)
                )
            
            elif action == 'get_insights':
                return self.get_insights(
                    metrics=params.get('metrics'),
                    period=params.get('period', 'day')
                )
            
            elif action == 'get_page_info':
                return self.get_page_info()
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown action: {action}",
                    'supported_actions': [
                        'post_message', 'post_photo', 'get_posts', 
                        'get_insights', 'get_page_info'
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
    
    server = FacebookServer()
    
    if len(sys.argv) < 2:
        print("Facebook MCP Server")
        print("Usage:")
        print("  python facebook_server.py get_page_info")
        print("  python facebook_server.py get_posts")
        print("  python facebook_server.py get_insights")
        print("  python facebook_server.py post_message 'Your message here'")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'get_page_info':
        result = server.process_action('get_page_info', {})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_posts':
        result = server.process_action('get_posts', {'limit': 5})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_insights':
        result = server.process_action('get_insights', {})
        print(json.dumps(result, indent=2))
    
    elif action == 'post_message' and len(sys.argv) > 2:
        message = sys.argv[2]
        result = server.process_action('post_message', {
            'message': message,
            'dry_run': True  # Set to False to actually post
        })
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown action or missing arguments: {action}")
