"""
Twitter (X) MCP Server
Handles Twitter API v2 interactions for posting tweets

Actions:
- post_tweet: Post single tweet (max 280 characters)
- post_thread: Post tweet thread (multiple connected tweets)
- reply_to_tweet: Reply to a specific tweet
- get_tweets: Get recent tweets from authenticated user
- get_mentions: Get mentions of authenticated user
- get_user_info: Get user profile information
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TwitterServer:
    """Twitter API v2 MCP Server"""
    
    def __init__(self, token_path: str = "./secrets/twitter_token.json"):
        self.token_path = Path(token_path)
        self.tokens = self._load_tokens()
        self.access_token = self.tokens.get('access_token')
        self.refresh_token = self.tokens.get('refresh_token')
        self.base_url = 'https://api.twitter.com/2'
        
    def _load_tokens(self) -> Dict:
        """Load Twitter tokens from secrets"""
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Twitter token not found at {self.token_path}. "
                "Run setup_twitter.py first."
            )
        
        with open(self.token_path, 'r') as f:
            return json.load(f)
    
    def _get_headers(self) -> Dict:
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request to Twitter API v2"""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
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
            raise Exception(f"Twitter API Error: {error_data}")
    
    def post_tweet(self, text: str, dry_run: bool = False) -> Dict:
        """
        Post a single tweet
        
        Args:
            text: Tweet text (max 280 characters)
            dry_run: If True, don't actually post (testing)
        
        Returns:
            Dict with tweet_id and status
        """
        if len(text) > 280:
            raise ValueError(f"Tweet exceeds 280 characters (length: {len(text)})")
        
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_tweet',
                'text': text,
                'character_count': len(text),
                'timestamp': datetime.now().isoformat()
            }
        
        payload = {
            'text': text
        }
        
        result = self._make_request('POST', 'tweets', json=payload)
        
        return {
            'status': 'success',
            'tweet_id': result['data']['id'],
            'text': result['data']['text'],
            'message': 'Tweet posted successfully',
            'url': f"https://twitter.com/i/web/status/{result['data']['id']}",
            'timestamp': datetime.now().isoformat()
        }
    
    def post_thread(self, tweets: List[str], dry_run: bool = False) -> Dict:
        """
        Post a tweet thread (multiple connected tweets)
        
        Args:
            tweets: List of tweet texts (each max 280 characters)
            dry_run: If True, don't actually post
        
        Returns:
            Dict with thread_id and status
        """
        if not tweets:
            raise ValueError("Thread must have at least one tweet")
        
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                raise ValueError(f"Tweet {i+1} exceeds 280 characters (length: {len(tweet)})")
        
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'post_thread',
                'tweet_count': len(tweets),
                'tweets': [{'text': t, 'length': len(t)} for t in tweets],
                'timestamp': datetime.now().isoformat()
            }
        
        tweet_ids = []
        previous_tweet_id = None
        
        for i, text in enumerate(tweets):
            payload = {
                'text': text
            }
            
            # Reply to previous tweet to create thread
            if previous_tweet_id:
                payload['reply'] = {
                    'in_reply_to_tweet_id': previous_tweet_id
                }
            
            result = self._make_request('POST', 'tweets', json=payload)
            tweet_id = result['data']['id']
            tweet_ids.append(tweet_id)
            previous_tweet_id = tweet_id
        
        return {
            'status': 'success',
            'thread_id': tweet_ids[0],  # First tweet ID
            'tweet_ids': tweet_ids,
            'tweet_count': len(tweet_ids),
            'message': f'Thread of {len(tweet_ids)} tweets posted successfully',
            'url': f"https://twitter.com/i/web/status/{tweet_ids[0]}",
            'timestamp': datetime.now().isoformat()
        }
    
    def reply_to_tweet(self, tweet_id: str, text: str, dry_run: bool = False) -> Dict:
        """
        Reply to a specific tweet
        
        Args:
            tweet_id: ID of tweet to reply to
            text: Reply text (max 280 characters)
            dry_run: If True, don't actually post
        
        Returns:
            Dict with reply_id and status
        """
        if len(text) > 280:
            raise ValueError(f"Reply exceeds 280 characters (length: {len(text)})")
        
        if dry_run:
            return {
                'status': 'dry_run',
                'action': 'reply_to_tweet',
                'in_reply_to': tweet_id,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
        
        payload = {
            'text': text,
            'reply': {
                'in_reply_to_tweet_id': tweet_id
            }
        }
        
        result = self._make_request('POST', 'tweets', json=payload)
        
        return {
            'status': 'success',
            'reply_id': result['data']['id'],
            'in_reply_to': tweet_id,
            'text': result['data']['text'],
            'message': 'Reply posted successfully',
            'url': f"https://twitter.com/i/web/status/{result['data']['id']}",
            'timestamp': datetime.now().isoformat()
        }
    
    def get_tweets(self, user_id: Optional[str] = None, limit: int = 10) -> Dict:
        """
        Get recent tweets from user
        
        Args:
            user_id: Twitter user ID (if None, get authenticated user's tweets)
            limit: Number of tweets to retrieve (max 100)
        
        Returns:
            Dict with tweets array and metadata
        """
        if not user_id:
            # Get authenticated user ID first
            me_result = self._make_request('GET', 'users/me')
            user_id = me_result['data']['id']
        
        endpoint = f'users/{user_id}/tweets'
        
        params = {
            'max_results': min(limit, 100),
            'tweet.fields': 'created_at,public_metrics,referenced_tweets',
            'expansions': 'referenced_tweets.id'
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        tweets = []
        for tweet in result.get('data', []):
            tweets.append({
                'tweet_id': tweet['id'],
                'text': tweet['text'],
                'created_at': tweet.get('created_at'),
                'metrics': tweet.get('public_metrics', {}),
                'url': f"https://twitter.com/i/web/status/{tweet['id']}"
            })
        
        return {
            'status': 'success',
            'tweets': tweets,
            'count': len(tweets),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_mentions(self, limit: int = 10) -> Dict:
        """
        Get mentions of authenticated user
        
        Args:
            limit: Number of mentions to retrieve
        
        Returns:
            Dict with mentions array and metadata
        """
        # Get authenticated user ID
        me_result = self._make_request('GET', 'users/me')
        user_id = me_result['data']['id']
        
        endpoint = f'users/{user_id}/mentions'
        
        params = {
            'max_results': min(limit, 100),
            'tweet.fields': 'created_at,author_id,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'username,name'
        }
        
        result = self._make_request('GET', endpoint, params=params)
        
        # Build user lookup
        users = {}
        if 'includes' in result and 'users' in result['includes']:
            for user in result['includes']['users']:
                users[user['id']] = {
                    'username': user['username'],
                    'name': user['name']
                }
        
        mentions = []
        for tweet in result.get('data', []):
            author_id = tweet.get('author_id')
            author = users.get(author_id, {})
            
            mentions.append({
                'tweet_id': tweet['id'],
                'text': tweet['text'],
                'created_at': tweet.get('created_at'),
                'author': author,
                'metrics': tweet.get('public_metrics', {}),
                'url': f"https://twitter.com/i/web/status/{tweet['id']}"
            })
        
        return {
            'status': 'success',
            'mentions': mentions,
            'count': len(mentions),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_user_info(self) -> Dict:
        """Get authenticated user information"""
        params = {
            'user.fields': 'id,username,name,description,public_metrics,created_at'
        }
        
        result = self._make_request('GET', 'users/me', params=params)
        user = result['data']
        
        return {
            'status': 'success',
            'user_info': {
                'id': user['id'],
                'username': user['username'],
                'name': user['name'],
                'bio': user.get('description', ''),
                'followers': user.get('public_metrics', {}).get('followers_count', 0),
                'following': user.get('public_metrics', {}).get('following_count', 0),
                'tweet_count': user.get('public_metrics', {}).get('tweet_count', 0),
                'created_at': user.get('created_at')
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
            if action == 'post_tweet':
                return self.post_tweet(
                    text=params.get('text', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'post_thread':
                return self.post_thread(
                    tweets=params.get('tweets', []),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'reply_to_tweet':
                return self.reply_to_tweet(
                    tweet_id=params.get('tweet_id', ''),
                    text=params.get('text', ''),
                    dry_run=params.get('dry_run', False)
                )
            
            elif action == 'get_tweets':
                return self.get_tweets(
                    user_id=params.get('user_id'),
                    limit=params.get('limit', 10)
                )
            
            elif action == 'get_mentions':
                return self.get_mentions(
                    limit=params.get('limit', 10)
                )
            
            elif action == 'get_user_info':
                return self.get_user_info()
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown action: {action}",
                    'supported_actions': [
                        'post_tweet', 'post_thread', 'reply_to_tweet',
                        'get_tweets', 'get_mentions', 'get_user_info'
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
    
    server = TwitterServer()
    
    if len(sys.argv) < 2:
        print("Twitter MCP Server")
        print("Usage:")
        print("  python twitter_server.py get_user_info")
        print("  python twitter_server.py get_tweets")
        print("  python twitter_server.py get_mentions")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'get_user_info':
        result = server.process_action('get_user_info', {})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_tweets':
        result = server.process_action('get_tweets', {'limit': 5})
        print(json.dumps(result, indent=2))
    
    elif action == 'get_mentions':
        result = server.process_action('get_mentions', {'limit': 5})
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown action: {action}")
