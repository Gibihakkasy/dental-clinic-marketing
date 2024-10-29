# AI Group Chat

AI Group Chat is an interactive web application that allows users to engage in conversations with multiple AI-powered characters from the Star Wars universe. Users can select which characters they want to chat with and have dynamic, multi-character conversations.

## Features

- Chat with multiple AI characters simultaneously
- Dynamic character selection
- Real-time conversation updates
- Responsive design for various screen sizes
- Character-specific avatars and personalities

## Technologies Used

- **Frontend**:
  - **React**: JavaScript library for building user interfaces
  - **Chakra UI**: Component library for accessible and responsive design
  - **Axios**: HTTP client for API calls
- **Backend**:
  - **FastAPI**: Web framework for building APIs with Python
  - **Ollama**: For AI model integration (currently macOS only)
  - **llama_index**: LLM toolkit for managing local large language models

## Project Structure

The project is divided into two main parts:

1. **Frontend** (React application)
2. **Backend** (FastAPI server)

## Setup and Installation

### Prerequisites

- **Node.js** (14 or higher) and **npm**
- **Python 3.7+**
- **Ollama** (for running AI models locally on macOS)

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

1. Open your web browser and go to `http://localhost:3000`.
2. Select the AI characters you want to chat with using the checkboxes on the left panel.
3. Type your message in the input field at the bottom and press Enter or click the send button.
4. The AI characters will respond based on their unique personalities and the conversation context.

## Customizing AI Characters

To add or modify AI characters, edit the `backend/bots_config.json` file. Each character should have a `name`, `model`, and `personality` description.

## Troubleshooting

- **CORS Issues**: Ensure that the backend’s CORS settings allow requests from `http://localhost:3000`.
- **Ollama Compatibility**: Ollama currently supports macOS. For other operating systems, alternatives or hosted models may be needed.
- **Package Conflicts**: Verify compatible versions in `requirements.txt` and `package.json`, especially for FastAPI and React dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE). 
