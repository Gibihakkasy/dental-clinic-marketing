# Dental Clinic Social Media Content Generator

An AI-powered platform that helps dental clinics create engaging social media content from RSS feeds and custom topics, including article summaries, Instagram captions, and AI-generated images.

## ✨ Features

- **Multi-Source Content**
  - RSS Feed Integration from top dental news sources
  - Custom topic-based content generation
  - Background processing for long-running tasks

- **AI-Powered Content Creation**
  - Article summarization with source attribution
  - Engaging Instagram captions with relevant hashtags
  - Creative image prompt generation
  - High-quality AI image generation using GPT-image-1

- **Content Management**
  - Real-time preview of generated content
  - Edit and customize all AI-generated content
  - Regenerate specific components (summary, caption, image)
  - Caching system for quick access to previous generations

- **Media Handling**
  - Automatic image generation from prompts
  - Cloudinary integration for image hosting
  - Image regeneration with different styles

- **Export & Sharing**
  - Download content as Word documents
  - Copy to clipboard functionality
  - Responsive design for all devices

## 🛠️ Technologies Used

### Frontend
- **React 18** - UI library for building interactive interfaces
- **Chakra UI** - Accessible component library with dark mode support
- **Axios** - Promise-based HTTP client
- **React Icons** - Comprehensive icon library
- **React Router** - Client-side routing
- **React Query** - Data fetching and state management

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **OpenAI API** - Powers all AI content generation
  - GPT-4o for text generation
  - GPT-image-1 for AI image generation
- **SQLite** - Lightweight database for caching
- **Cloudinary** - Image storage and CDN
- **Uvicorn** - ASGI server implementation
- **Python 3.11+** - Backend programming language

## 🏗️ Architecture

The application follows a client-server architecture with a clear separation between the frontend and backend:

1. **Frontend**: Single-page application that communicates with the backend via RESTful APIs
2. **Backend**: FastAPI server handling business logic, AI processing, and data persistence
3. **Database**: SQLite for caching generated content and metadata
4. **External Services**:
   - OpenAI API for AI content generation
   - Cloudinary for image storage and delivery
   - RSS feeds for content aggregation

### Project Structure

```
.
├── backend/
│   ├── agents/           # AI agent implementations
│   │   ├── summarizer.py    # Article and topic summarization
│   │   ├── captioner.py     # Social media caption generation
│   │   └── image_prompter.py # Image prompt and generation logic
│   │
│   ├── db/               # Database and caching
│   │   └── cache.py      # SQLite-based caching system
│   │
│   ├── rss/              # RSS feed handling
│   │   ├── fetcher.py    # Feed fetching and parsing
│   │   └── cleaner.py    # Content cleaning utilities
│   │
│   ├── utils/            # Utility functions
│   │   ├── cloudinary.py # Image upload and management
│   │   └── doc_writer.py # Word document generation
│   │
│   ├── config.py         # Application configuration
│   └── main.py          # FastAPI application and endpoints
│
├── frontend/
│   └── src/
│       ├── components/   # Reusable React components
│       │   ├── ArticleCard.js  # Article display component
│       │   ├── ContentEditor.js # Content editing interface
│       │   └── ImageGenerator.js # Image generation UI
│       │
│       ├── App.js        # Main application component
│       └── App.css       # Global styles
│
└── README.md             # Project documentation
```

## 🚀 Setup and Installation

### Prerequisites

- Node.js (v18 or higher) and npm
- Python 3.11+
- OpenAI API key with access to GPT-4o and GPT-image-1
- Cloudinary account (for image storage)
- (Optional) Instagram Business Account for direct posting

### Backend Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone [your-repo-url]
   cd dental-clinic-marketing
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the project root with:
   ```env
   # Required
   OPENAI_API_KEY=your_openai_api_key
   CLOUDINARY_URL=your_cloudinary_url
   
   # Optional
   INSTAGRAM_ACCESS_TOKEN=your_instagram_token
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_business_id
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd ../frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```
   The frontend will be available at `http://localhost:3000`

## 🌟 Usage

1. **Generate Content from RSS Feeds**
   - Browse articles from configured RSS feeds
   - Click on an article to generate a summary, caption, and image prompt
   - Edit any generated content as needed

2. **Create Content from Custom Topics**
   - Enter a topic in the search bar
   - The system will generate content based on web search
   - Customize the generated content

3. **Manage Images**
   - Generate AI images using the image prompt
   - Regenerate images with different styles
   - View and manage generated images

4. **Export and Share**
   - Download content as a Word document
   - Copy content to clipboard
   - (Optional) Post directly to Instagram

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for their powerful AI models
- Cloudinary for image hosting
- The open-source community for various libraries and tools
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
