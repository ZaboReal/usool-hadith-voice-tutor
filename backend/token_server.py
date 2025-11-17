"""
Token Server for LiveKit
Generates access tokens for frontend clients
"""
import os
from dotenv import load_dotenv
from aiohttp import web
from livekit import api
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_token(request):
    """
    Create LiveKit access token for a user

    Request body:
        {
            "identity": "user-id",
            "roomName": "room-name"
        }

    Returns:
        {
            "token": "access-token"
        }
    """
    try:
        data = await request.json()
        identity = data.get('identity', f'user-{os.urandom(4).hex()}')
        room_name = data.get('roomName', 'hadith-voice-room')

        # Create access token
        token = api.AccessToken(
            api_key=os.getenv('LIVEKIT_API_KEY'),
            api_secret=os.getenv('LIVEKIT_API_SECRET'),
        )

        token.with_identity(identity).with_name(identity).with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )

        jwt_token = token.to_jwt()

        logger.info(f"Generated token for {identity} in room {room_name}")

        return web.json_response({
            'token': jwt_token,
            'url': os.getenv('LIVEKIT_URL')
        })

    except Exception as e:
        logger.error(f"Error generating token: {e}")
        return web.json_response(
            {'error': str(e)},
            status=500
        )


async def health_check(request):
    """Health check endpoint"""
    return web.json_response({'status': 'ok'})


async def handle_options(request):
    """Handle CORS preflight requests"""
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )


@web.middleware
async def cors_middleware(request, handler):
    """Add CORS headers to all responses"""
    if request.method == 'OPTIONS':
        return await handle_options(request)

    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def create_app():
    """Create and configure the web application"""
    app = web.Application(middlewares=[cors_middleware])

    # Add routes
    app.router.add_post('/token', create_token)
    app.router.add_get('/health', health_check)

    return app


if __name__ == '__main__':
    # Verify required environment variables
    required_vars = ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'LIVEKIT_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set them in your .env file")
        exit(1)

    app = create_app()

    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting token server on port {port}")

    web.run_app(app, host='0.0.0.0', port=port)
