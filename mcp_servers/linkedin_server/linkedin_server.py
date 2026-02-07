"""
LinkedIn MCP Server - Model Context Protocol for LinkedIn Actions

This MCP server handles LinkedIn posting actions for the AI Employee.

Actions:
- post_update: Post a text update to LinkedIn
- post_article: Share a long-form article
- get_profile: Get authenticated user's profile
- get_stats: Get post engagement statistics

Security: All posts require HITL approval (via /Pending_Approval workflow)
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInMCPServer:
    """LinkedIn MCP Server for posting business updates"""
    
    def __init__(self):
        self.token_path = Path(os.getenv('LINKEDIN_TOKEN_PATH', './secrets/linkedin_token.json'))
        self.api_base = 'https://api.linkedin.com/v2'
        self.access_token = None
        self._load_token()
    
    def _load_token(self):
        """Load OAuth access token"""
        try:
            if self.token_path.exists():
                with open(self.token_path, 'r') as f:
                    token_data = json.load(f)
                    self.access_token = token_data.get('access_token')
                    logger.info("✅ LinkedIn token loaded")
            else:
                logger.warning("⚠️  LinkedIn token not found. Run: python setup_linkedin.py")
        except Exception as e:
            logger.error(f"Error loading token: {e}")
    
    def _get_headers(self) -> dict:
        """Get authorization headers for API requests"""
        if not self.access_token:
            raise ValueError("LinkedIn not authenticated. Run: python setup_linkedin.py")
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def get_profile(self) -> dict:
        """
        Get authenticated user's LinkedIn profile (for person URN)
        
        Returns:
            dict: Profile data including id (URN)
        """
        try:
            url = f'{self.api_base}/me'
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            profile = response.json()
            logger.info(f"✅ Retrieved profile for: {profile.get('localizedFirstName', 'User')}")
            return profile
        
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            raise
    
    def post_update(self, text: str, visibility: str = 'PUBLIC') -> dict:
        """
        Post a text update to LinkedIn
        
        Args:
            text: Post content (max 3000 characters)
            visibility: 'PUBLIC' or 'CONNECTIONS'
        
        Returns:
            dict: Response with post ID and status
        """
        try:
            # Get user profile to get person URN
            profile = self.get_profile()
            person_urn = f"urn:li:person:{profile['id']}"
            
            # Build post payload
            post_data = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            # Post to LinkedIn
            url = f'{self.api_base}/ugcPosts'
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=post_data
            )
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get('id', 'unknown')
            
            logger.info(f"✅ Posted to LinkedIn successfully! Post ID: {post_id}")
            
            return {
                'status': 'success',
                'post_id': post_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'text_preview': text[:100] + '...' if len(text) > 100 else text
            }
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"LinkedIn API error: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            raise
        except Exception as e:
            logger.error(f"Failed to post update: {e}")
            raise
    
    def post_article(self, title: str, text: str, url: str = None) -> dict:
        """
        Share a long-form article or link on LinkedIn
        
        Args:
            title: Article title
            text: Commentary about the article
            url: Optional article URL to share
        
        Returns:
            dict: Response with post ID
        """
        try:
            profile = self.get_profile()
            person_urn = f"urn:li:person:{profile['id']}"
            
            share_content = {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "ARTICLE" if url else "NONE"
            }
            
            if url:
                share_content["media"] = [{
                    "status": "READY",
                    "description": {
                        "text": text
                    },
                    "originalUrl": url,
                    "title": {
                        "text": title
                    }
                }]
            
            post_data = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": share_content
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            url_endpoint = f'{self.api_base}/ugcPosts'
            response = requests.post(
                url_endpoint,
                headers=self._get_headers(),
                json=post_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Posted article to LinkedIn: {title}")
            
            return {
                'status': 'success',
                'post_id': result.get('id'),
                'title': title,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to post article: {e}")
            raise
    
    def dry_run_post(self, text: str) -> dict:
        """
        Simulate posting without actually posting (for testing)
        
        Returns:
            dict: Simulated response
        """
        logger.info(f"🧪 DRY RUN: Would post to LinkedIn")
        logger.info(f"📝 Content preview: {text[:200]}...")
        
        return {
            'status': 'success (dry run)',
            'post_id': 'dry_run_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'text_preview': text[:100] + '...' if len(text) > 100 else text,
            'note': 'This was a dry run - nothing was posted'
        }


# MCP Server Interface Functions
def handle_post_update(params: dict) -> dict:
    """
    MCP handler for posting LinkedIn updates
    
    Params:
        text: Post content
        visibility: PUBLIC or CONNECTIONS (default: PUBLIC)
        dry_run: If true, don't actually post (default: false)
    """
    try:
        server = LinkedInMCPServer()
        
        text = params.get('text', '')
        if not text:
            return {'status': 'error', 'message': 'Missing required parameter: text'}
        
        visibility = params.get('visibility', 'PUBLIC')
        dry_run = params.get('dry_run', False)
        
        if dry_run:
            result = server.dry_run_post(text)
        else:
            result = server.post_update(text, visibility)
        
        return result
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def handle_post_article(params: dict) -> dict:
    """
    MCP handler for posting LinkedIn articles
    
    Params:
        title: Article title
        text: Post commentary
        url: Article URL (optional)
        dry_run: If true, don't actually post (default: false)
    """
    try:
        server = LinkedInMCPServer()
        
        title = params.get('title', '')
        text = params.get('text', '')
        url = params.get('url')
        dry_run = params.get('dry_run', False)
        
        if not title or not text:
            return {'status': 'error', 'message': 'Missing required parameters'}
        
        if dry_run:
            result = server.dry_run_post(f"{title}\n\n{text}")
        else:
            result = server.post_article(title, text, url)
        
        return result
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def handle_get_profile(params: dict) -> dict:
    """MCP handler for getting user profile"""
    try:
        server = LinkedInMCPServer()
        profile = server.get_profile()
        return {
            'status': 'success',
            'profile': profile
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


# MCP Server Routes
MCP_ACTIONS = {
    'post_update': handle_post_update,
    'post_article': handle_post_article,
    'get_profile': handle_get_profile
}


def process_action(action: str, params: dict) -> dict:
    """
    Process MCP action request
    
    Args:
        action: Action name (post_update, post_article, get_profile)
        params: Action parameters
    
    Returns:
        dict: Action result
    """
    handler = MCP_ACTIONS.get(action)
    
    if not handler:
        return {
            'status': 'error',
            'message': f'Unknown action: {action}',
            'available_actions': list(MCP_ACTIONS.keys())
        }
    
    return handler(params)


if __name__ == '__main__':
    # Test MCP server
    print("LinkedIn MCP Server - Test Mode")
    print("=" * 60)
    
    # Test dry run
    test_params = {
        'text': 'Excited to share that our AI Employee project has automated 85% of routine business tasks! 🚀\n\n#AI #Automation #BusinessEfficiency',
        'dry_run': True
    }
    
    result = process_action('post_update', test_params)
    print(json.dumps(result, indent=2))
    
    print("\n✅ MCP Server test complete")
    print("💡 To use: Import and call process_action('post_update', params)")
