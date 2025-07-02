# Dental Clinic Social Media Planner

An AI-powered tool that helps dental clinics generate engaging social media content from RSS feeds, including article summaries, Instagram captions, and image prompts.

## Features

- **RSS Feed Integration**: Pull in articles from configured RSS feeds
- **AI-Powered Summarization**: Automatically generate concise summaries of dental articles
- **Caption Generation**: Create engaging Instagram captions from article content
- **Image Prompt Creation**: Generate creative prompts for AI image generation
- **Content Management**: Edit and customize generated content before posting
- **Instagram Integration**: Select and post content directly to Instagram
- **Export Options**: Download content as Word documents for review

## How It Works

1. **Feed Aggregation**: The system fetches articles from configured RSS feeds
2. **Content Processing**:
   - Articles are summarized using AI
   - Engaging captions are generated for social media
   - Image prompts are created for visual content
3. **Content Review & Customization**:
   - Review and edit generated content
   - Select which posts to publish
   - Customize captions and image prompts
4. **Publishing**:
   - Post directly to Instagram
   - Export content for review

## Technologies Used

### Frontend
- **React**: For building the user interface
- **Chakra UI**: For responsive and accessible UI components
- **Axios**: For making HTTP requests to the backend
- **React Icons**: For a consistent icon set

### Backend
- **FastAPI**: For building the REST API
- **OpenAI API**: For AI-powered content generation
- **SQLite**: For caching article data
- **python-docx**: For generating Word documents
- **python-instagram**: For Instagram integration

## Project Structure

```
.
├── backend/               # Backend server code
│   ├── agents/           # AI agent implementations
│   ├── db/               # Database models and cache
│   ├── rss/              # RSS feed handling
│   ├── utils/            # Utility functions
│   ├── config.py         # Configuration settings
│   └── main.py           # Main FastAPI application
├── frontend/             # Frontend React application
│   └── src/
│       ├── components/   # Reusable React components
│       └── App.js        # Main application component
└── README.md             # This file
```

## Setup and Installation

### Prerequisites

- Node.js (v14 or higher) and npm
- Python 3.7+
- OpenAI API key
- Instagram Business Account (for Instagram posting)

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   INSTAGRAM_ACCESS_TOKEN=your_instagram_token
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Usage

1. **Configure RSS Feeds**: Add your preferred dental/health RSS feed URLs in the backend configuration
2. **Generate Content**: Click "Generate" to fetch and process articles
3. **Review & Edit**: Check the generated content and make any necessary edits
4. **Post to Instagram**: Select which posts to publish and click "Post to Instagram"
5. **Export**: Download content as Word documents for review or scheduling

## Contributing

Contributions are welcome! Please create an issue or submit a pull request with your proposed changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
