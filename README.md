# Hotel Room Booking Chatbot

This project implements a simple chatbot for hotel room bookings as part of the course "Project AI Use Case" from IU Master of Science in Artificial Intelligence. The chatbot is designed to handle basic room reservation inquiries and collect essential information from users.

## Project Overview

The chatbot is built to assist users in booking hotel rooms by gathering key information through a series of questions and answers. It utilizes LangChain for conversation management, LangGraph for flow control, and GPT-4o calls to enhance the quality of responses. The entire ChatEngine logic was encapsulated in a class called BookingWorkflow, which allowed the graph to be converted into an API using FastAPI. The frontend was developed using Streamlit.

## Demo
(Youtube Video)[]

## Technologies Used

- **Python**: Core language for developing chatbot logic.
- **FastAPI**: Used to build an API to interact with the chatbot workflow.
- **Streamlit**: Provides a user-friendly interface to interact with the chatbot.
- **LangChain & LangGraph**: Manage conversation flow and decision making.
- **GPT-4o**: Powers natural language understanding and response generation.
- **SQLite**: Database used for saving conversation checkpoints.
- **Pydantic**: Defines data models for API requests and responses.

## Repository Structure

- `src/`: Contains the source code for the chatbot implementation
  - **`hotel_booking_api.py`**: Defines the FastAPI endpoint and handles interactions with the BookingWorkflow class. It acts as the main entry point for the API that processes booking requests and manages the workflow states.
  - **`pydantic_classes.py`**: Defines Pydantic models for structuring LLM chain outputs and validating user input and booking details, ensuring data consistency throughout the workflow.
  - **`agent.py`**: Contains the core `BookingWorkflow` class that encapsulates the entire logic of the chatbot. It manages the conversation flow using LangGraph, interacts with different language model chains for intent detection, information extraction, response generation, and booking updates.
  - **`frontend.py`**: Implements the Streamlit-based frontend, which interacts with the FastAPI backend. This script provides a graphical user interface for users to communicate with the chatbot in real-time.
  - **`chains.py`**: Sets up different LangChain chains for specific tasks such as intent detection, booking information extraction, response generation, summarization, and correction.
  - **`prompts.py`**: Contains the prompt templates used by the different chains to interact with the language model, guiding the conversation and response generation.
  - **`api_tests.ipynb`**: Development code to test the hotel booking workflow using the API calls.
  - **`hotel_agent_tests.ipynb`**: Implement tests for the BookingWorkflow class to ensure the Hotel Assistant is behaving correctly.
- `interactive_solution.ipynb`: Jupyter notebook with the interactive chatbot solution.
- `requirements.txt`: List of Python dependencies required for the project.
- `hotelBooking3.jpg`: Conception phase diagram file.
- `Project_ai_use_case.pdf`: Conception phase document.

## Getting Started

To run this project locally:

1. Clone the repository:
   `git clone https://github.com/hualcosa/DLMAIPAIUC01.git`

2. Export your OpenAI api key to your active terminal:
   `EXPORT OPENAI_API_KEY="sk-********"`

3. Install the required dependencies:

  `pip install -r requirements.txt`

4. Start the FastAPI server:
```
   cd src\
   uvicorn hotel\_booking\_api\:app --reload --port 8000
```
5. Open a separate terminal. Navigate to the src folder and launch the streamlit app:
```
   cd src

   streamlit run frontend.py --server.port 8501
```
The app will be automatically launched in your browser.

Optionally, open and run the `interactive_solution.ipynb` notebook in Jupyter for a notebook-based interaction. 

## Usage

Follow the prompts and provide the requested information to simulate a hotel room booking process. The chatbot uses API calls to the backend to manage state transitions, ensuring smooth flow and data consistency.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
