import streamlit as st
import requests

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
# session state variable to track whether we are doing the first question
if "first_query" not in st.session_state:
    st.session_state.first_query = True
# stores the current state of the hotel assistant
if "hotel_assitant_state" not in st.session_state:
    st.session_state.hotel_assitant_state = None
# variable use to toggle the developer view on or off
if "developer_view" not in st.session_state:
    st.session_state.developer_view = False

# Base URL of the FastAPI server
BASE_URL = "http://127.0.0.1:8000"


# Function to interact with the /run_workflow/ endpoint
def interact_with_workflow(state):
    try:
        # Send a POST request to the /run_workflow/ endpoint
        response = requests.post(f"{BASE_URL}/run_workflow/", json=state)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse and return the JSON response
            parsed_response = response.json()
            parsed_response = {
                k: v for k, v in parsed_response.items() if v is not None
            }
            return parsed_response
        else:
            # If the request failed, print the error details
            print(f"Error: {response.status_code}, Detail: {response.text}")
    except requests.exceptions.RequestException as e:
        # Handle any request exceptions that may occur
        print(f"Request failed: {e}")


def process_text(prompt):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("processing your request..."):
        # If this is the first message the user is sending to the assistant, we build the payload
        if st.session_state.first_query:
            state = {
                "user_message": prompt,
                "not_filled_keys": [
                    "full_name",
                    "check_in_date",
                    "check_out_date",
                    "num_guests",
                    "payment_method",
                    "breakfast_included",
                ],
            }
            st.session_state.first_query = False
        else:
            state = st.session_state.hotel_assitant_state
            state["user_message"] = prompt

        # Query the api endpoint
        updated_state = interact_with_workflow(state)
        # Update the state
        st.session_state.hotel_assitant_state = updated_state
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": updated_state["response"],
        })

    return updated_state["response"]


# Streamlit UI
st.markdown(
    """
<h2 style='text-align: center;'>DLMAIPAIUC01 - Project AI Use Case</h2>
<h2 style='text-align: center;'>Hotel Booking Application</h2>

<h4 style='text-align: right;'>Hugo Albuquerque Cosme da Siva</h4>
<h5 style='text-align: right;'>matriculation ID: 92126125</h5>
""",
    unsafe_allow_html=True,
)

# Sidebar for developer view
with st.sidebar:
    st.session_state.developer_view = st.checkbox("Developer View")

# Initial introduction (only if it's the first run)
if "introduced" not in st.session_state:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm GrandVista's Hotel booking assistant. How can I assist you today?",
    })
    st.session_state.introduced = True

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a container for the chat input and recording button
input_container = st.container()

prompt = st.chat_input("Type your message here")

# Process text input
if prompt:
    process_text(prompt)
    st.rerun()

# Display assistant state if developer view is toggled
if st.session_state.developer_view:
    st.write(st.session_state.hotel_assitant_state)
