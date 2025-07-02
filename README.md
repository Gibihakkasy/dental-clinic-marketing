![App Demo](./demo.png)
# AI Group Chat

AI Group Chat is an interactive web application that allows users to engage in conversations with multiple AI-powered characters from the Star Wars universe. Users can select which characters they want to chat with and have dynamic, multi-character conversations.

## Features

- Generate social media content from RSS feeds
- AI-powered article summarization
- Automatic caption generation for social media
- Image prompt generation for visual content
- Edit and customize generated captions
- Post directly to Instagram (with proper credentials)
- Download content as Word documents

## Technologies Used

- **Frontend**:
  - **React**: JavaScript library for building user interfaces
  - **Chakra UI**: Component library for accessible and responsive design
  - **Axios**: HTTP client for API calls
  - **React Icons**: For beautiful icons

- **Backend**:
  - **FastAPI**: Web framework for building APIs with Python
  - **Ollama**: For AI model integration (currently macOS only)
  - **llama_index**: LLM toolkit for managing local large language models
  - **python-docx**: For generating Word documents
  - **python-dotenv**: For managing environment variables

## Project Structure

The project is divided into two main parts:

1. **Frontend** (React application)
2. **Backend** (FastAPI server)

## Setup and Installation

### Prerequisites

- **Node.js** (14 or higher) and **npm**
- **Python 3.7+**
- **Ollama** (for running AI models locally on macOS)
- **Instagram Business Account** (for Instagram posting functionality)

### Backend Setup

1. Navigate to the project root directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On **Windows**: `venv\Scripts\activate`
   - On **macOS and Linux**: `source venv/bin/activate`
4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   *Ensure that `requirements.txt` includes all necessary packages, especially `fastapi`, `uvicorn`, `pydantic`, and `llama_index`.*

### Environment Variables

1. Copy the `.env.example` file to `.env` and update the values as needed:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file and add your API keys and configuration.

#### Instagram Setup

To enable Instagram posting functionality:

1. Create a Facebook Developer account at [developers.facebook.com](https://developers.facebook.com/)
2. Create a new app and add Instagram Basic Display API
3. Get your Instagram Access Token and Business Account ID
4. Add these to your `.env` file:
   ```
   INSTAGRAM_ACCESS_TOKEN=your_access_token_here
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id_here
   ```

> **Note**: The Instagram Graph API requires a Business or Creator account with the appropriate permissions.

### Frontend Setup

1. Navigate to the `frontend` directory.
2. Install the required npm packages:
   ```bash
   npm install
   ```

*Ensure that `package.json` in the `frontend` directory includes `@chakra-ui/react`, `@emotion/react`, `@emotion/styled`, `axios`, `react-icons`, and `framer-motion`.*

## Running the Application

To run both the frontend and backend simultaneously:

1. From the project root directory, run:
   ```bash
   python run_app.py
   ```

This script will start both the FastAPI backend server and the React frontend development server.

## Usage

1. **Fetch Articles**: The app will automatically fetch the latest articles from configured RSS feeds
2. **Select Content**: Choose which articles you want to generate content for
3. **Generate Content**: Click "Generate Plan" to create summaries, captions, and image prompts
4. **Edit & Customize**:
   - Edit any generated caption by clicking the text area
   - Click "Save Changes" to update your edits
5. **Post to Instagram**:
   - Select captions you want to post using the checkboxes
   - Click "Post to Instagram" to post directly to your connected account
   - Or use the bulk post modal to post multiple items at once
6. **Download**: Download all generated content as a Word document

## Customizing AI Characters

To add or modify AI characters, edit the `backend/bots_config.json` file. Each character should have a `name`, `model`, and `personality` description.

## Troubleshooting

- **CORS Issues**: Ensure that the backend’s CORS settings allow requests from `http://localhost:3000`.
- **Ollama Compatibility**: Ollama currently supports macOS. For other operating systems, alternatives or hosted models may be needed.
- **Package Conflicts**: Verify compatible versions in `requirements.txt` and `package.json`, especially for FastAPI and React dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source. 
