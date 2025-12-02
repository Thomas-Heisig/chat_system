# Chat System Frontend

## Structure

The frontend files are organized as follows:

- **Static files**: Located in `../static/`
  - `../static/js/` - JavaScript files (chat.js, admin.js, etc.)
  - `../static/css/` - CSS stylesheets (style.css)
  
- **Templates**: Located in `../templates/`
  - `../templates/index.html` - Main HTML template

## Development

The frontend is served directly by the FastAPI backend. No separate build process is required.

### Running the Frontend

1. Start the backend server:
   ```bash
   cd ..
   python main.py
   ```

2. Access the frontend at: http://localhost:8000

### Frontend Technologies

- Vanilla JavaScript (ES6+)
- WebSocket for real-time communication
- CSS3 for styling
- No build tools or frameworks required

### Key Files

- `chat.js` - Main chat functionality and WebSocket handling
- `admin.js` - Admin dashboard functionality
- `avatar-renderer.js` - Avatar rendering system
- `virtual-room.js` - Virtual room functionality
- `webrtc.js` - WebRTC video chat integration
- `gesture-detector.js` - Gesture detection features
- `style.css` - Main stylesheet

## Adding New Features

1. Add JavaScript files to `../static/js/`
2. Add CSS files to `../static/css/`
3. Reference them in `../templates/index.html`
4. The FastAPI backend will automatically serve them

## Notes

- Frontend is tightly integrated with the FastAPI backend
- WebSocket connections are handled through `/ws` endpoint
- Static files are mounted at `/static/` route
- Templates use Jinja2 templating engine
