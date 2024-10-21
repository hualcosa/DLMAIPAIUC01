import re
import uuid
import sqlite3
import json
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from pydantic_classes import (
    BookingState,
    IntentClassification,
    BookingInfo,
)
from chains import (
    create_intent_chain,
    create_booking_info_chain,
    create_booking_change_chain,
    create_response_generation_chain,
    create_summarization_chain,
    create_correction_chain,
)


class BookingWorkflow:
    NECESSARY_INFORMATION = [
        "full_name",
        "check_in_date",
        "check_out_date",
        "num_guests",
        "payment_method",
        "breakfast_included",
    ]

    def __init__(self, db_path: str = "conversation_history.db", debug: bool = False):
        """
        Initializes the BookingWorkflow.

        Args:
            db_path (str): Path to the SQLite database.
            debug (bool): If True, enables debug mode to print state before and after each node execution.
        """
        self.debug = debug

        # Initialize chains
        self.intent_chain = create_intent_chain()
        self.booking_info_chain = create_booking_info_chain()
        self.booking_change_chain = create_booking_change_chain()
        self.response_chain = create_response_generation_chain()
        self.summarization_chain = create_summarization_chain()
        self.correction_chain = create_correction_chain()

        # Setup state graph
        self.workflow = StateGraph(BookingState)
        self._setup_graph()

        # Setup SQLite checkpointer
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(self.conn)

        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    def _setup_graph(self):
        # Define state transitions
        self.workflow.add_node("detect_intent", self.detect_intent)
        self.workflow.add_node("collect_information", self.collect_information)
        self.workflow.add_node("validate_information", self.validate_information)
        self.workflow.add_node("generate_response", self.generate_response)
        self.workflow.add_node("summarize_booking", self.summarize_booking)
        self.workflow.add_node("change_information", self.change_information)
        self.workflow.add_node("ask_for_correction", self.ask_for_correction)

        # Define edges
        self.workflow.set_entry_point("detect_intent")

        # Add conditional edges based on the intent
        self.workflow.add_conditional_edges(
            "detect_intent",
            lambda state: state.get("intent", "other"),
            {
                "make a reservation": "collect_information",
                "check reservation": "summarize_booking",
                "change reservation": "change_information",
                "other": "generate_response",
            },
        )
        self.workflow.add_edge("collect_information", "validate_information")

        # Conditional edge after validate_information
        self.workflow.add_conditional_edges(
            "validate_information",
            lambda state: "ask_for_correction"
            if not state.get("valid_info", False)
            else "generate_response",
            {
                "ask_for_correction": "ask_for_correction",
                "generate_response": "generate_response",
            },
        )

        self.workflow.add_edge("change_information", "summarize_booking")
        self.workflow.add_edge("generate_response", END)
        self.workflow.add_edge("summarize_booking", END)
        self.workflow.add_edge("ask_for_correction", END)

    def _print_state(self, state: dict, message: str):
        """
        Helper method to print the current state in a formatted manner.

        Args:
            state (dict): The current state of the booking.
            message (str): Custom message to display.
        """
        print(f"\n=== {message} ===")
        print(json.dumps(state, indent=4, default=str))
        print("========================\n")

    def detect_intent(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before detect_intent")

        payload = {
            "assistant_question": state["response"] if "response" in state else None,
            "answer": state["user_message"],
        }
        result = self.intent_chain.invoke(payload)
        state["intent"] = result.intent

        if self.debug:
            self._print_state(state, "After detect_intent")

        return state

    def collect_information(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before collect_information")

        # Invoke the booking_info_chain to extract booking information
        extracted_info = self.booking_info_chain.invoke({
            "message": state["user_message"]
        })

        # Update the state with the extracted information
        if (
            extracted_info.full_name is not None
            and "full_name" in state["not_filled_keys"]
        ):
            state["full_name"] = extracted_info.full_name
            state["not_filled_keys"].remove("full_name")
        if (
            extracted_info.check_in_date is not None
            and "check_in_date" in state["not_filled_keys"]
        ):
            state["check_in_date"] = extracted_info.check_in_date
            state["not_filled_keys"].remove("check_in_date")
        if (
            extracted_info.check_out_date is not None
            and "check_out_date" in state["not_filled_keys"]
        ):
            state["check_out_date"] = extracted_info.check_out_date
            state["not_filled_keys"].remove("check_out_date")
        if (
            extracted_info.num_guests is not None
            and "num_guests" in state["not_filled_keys"]
        ):
            state["num_guests"] = extracted_info.num_guests
            state["not_filled_keys"].remove("num_guests")
        if (
            extracted_info.payment_method is not None
            and "payment_method" in state["not_filled_keys"]
        ):
            state["payment_method"] = extracted_info.payment_method
            state["not_filled_keys"].remove("payment_method")
        if (
            extracted_info.breakfast_included is not None
            and "breakfast_included" in state["not_filled_keys"]
        ):
            state["breakfast_included"] = extracted_info.breakfast_included
            state["not_filled_keys"].remove("breakfast_included")

        if self.debug:
            self._print_state(state, "After collect_information")

        return state

    def change_information(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before change_information")

        # Invoke the booking_change_chain to identify the booking information that needs to be changed
        payload = {
            "message": state["user_message"],
            "full_name": state.get("full_name"),
            "check_in_date": state.get("check_in_date"),
            "check_out_date": state.get("check_out_date"),
            "num_guests": state.get("num_guests"),
            "payment_method": state.get("payment_method"),
            "breakfast_included": state.get("breakfast_included"),
        }
        info_to_change = self.booking_change_chain.invoke(payload)

        # Change the information requested by the user
        for key, value in info_to_change.dict().items():
            if value is not None:
                state[key] = value
                if key in state["not_filled_keys"]:
                    state["not_filled_keys"].remove(key)

        # Change intent back to make a reservation in case there is still information to be collected
        if len(state["not_filled_keys"]) > 0:
            state["intent"] = "make a reservation"
        else:
            state["intent"] = "check reservation"

        if self.debug:
            self._print_state(state, "After change_information")

        return state

    def validate_information(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before validate_information")

        def is_valid_date_format(date_string):
            pattern = r"^\d{4}-\d{2}-\d{2}$"
            if not re.match(pattern, date_string):
                return False
            try:
                datetime.strptime(date_string, "%Y-%m-%d")
                return True
            except ValueError:
                return False

        errors = []

        # Validate full_name
        if "full_name" in state and len(state["full_name"]) < 3:
            errors.append("Full name must be at least 3 characters long.")
            state.setdefault("not_filled_keys", []).append("full_name")

        # Validate check_in_date
        if "check_in_date" in state:
            if not is_valid_date_format(state["check_in_date"]):
                errors.append("Check-in date format is invalid (YYYY-MM-DD).")
                state.setdefault("not_filled_keys", []).append("check_in_date")
            elif (
                datetime.strptime(state["check_in_date"], "%Y-%m-%d") < datetime.today()
            ):
                errors.append("Check-in date cannot be in the past.")
                state.setdefault("not_filled_keys", []).append("check_in_date")

        # Validate check_out_date
        if "check_out_date" in state:
            if not is_valid_date_format(state["check_out_date"]):
                errors.append("Check-out date format is invalid (YYYY-MM-DD).")
                state.setdefault("not_filled_keys", []).append("check_out_date")
            elif (
                datetime.strptime(state["check_out_date"], "%Y-%m-%d")
                < datetime.today()
            ):
                errors.append("Check-out date cannot be in the past.")
                state.setdefault("not_filled_keys", []).append("check_out_date")

        # Validate date order
        if "check_in_date" in state and "check_out_date" in state:
            if datetime.strptime(
                state["check_out_date"], "%Y-%m-%d"
            ) <= datetime.strptime(state["check_in_date"], "%Y-%m-%d"):
                errors.append("Check-out date must be after check-in date.")
                state.setdefault("not_filled_keys", []).extend([
                    "check_in_date",
                    "check_out_date",
                ])

        # Validate num_guests
        if "num_guests" in state and state["num_guests"] <= 0:
            errors.append("Number of guests must be positive.")
            state.setdefault("not_filled_keys", []).append("num_guests")

        # Validate payment_method
        valid_payment_methods = ["credit card", "debit card", "cash", "paypal"]
        if (
            "payment_method" in state
            and state["payment_method"].lower() not in valid_payment_methods
        ):
            errors.append(
                f"Invalid payment method. Please choose from: {', '.join(valid_payment_methods)}."
            )
            state.setdefault("not_filled_keys", []).append("payment_method")

        # Update the state
        state["valid_info"] = len(errors) == 0
        state["error"] = errors

        if self.debug:
            self._print_state(state, "After validate_information")

        return state

    def generate_response(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before generate_response")

        payload = {
            "intent": state["intent"],
            "full_name": state.get("full_name"),
            "check_in_date": state.get("check_in_date"),
            "check_out_date": state.get("check_out_date"),
            "num_guests": state.get("num_guests"),
            "payment_method": state.get("payment_method"),
            "breakfast_included": state.get("breakfast_included"),
        }

        state["response"] = self.response_chain.invoke(input=payload)

        if self.debug:
            self._print_state(state, "After generate_response")

        return state

    def summarize_booking(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before summarize_booking")

        payload = {
            "intent": state["intent"],
            "full_name": state.get("full_name"),
            "check_in_date": state.get("check_in_date"),
            "check_out_date": state.get("check_out_date"),
            "num_guests": state.get("num_guests"),
            "payment_method": state.get("payment_method"),
            "breakfast_included": state.get("breakfast_included"),
        }

        state["response"] = self.summarization_chain.invoke(input=payload)

        if self.debug:
            self._print_state(state, "After summarize_booking")

        return state

    def ask_for_correction(self, state: BookingState) -> BookingState:
        if self.debug:
            self._print_state(state, "Before ask_for_correction")

        payload = {
            "full_name": state.get("full_name"),
            "check_in_date": state.get("check_in_date"),
            "check_out_date": state.get("check_out_date"),
            "num_guests": state.get("num_guests"),
            "payment_method": state.get("payment_method"),
            "breakfast_included": state.get("breakfast_included"),
            "errors": state.get("error"),
        }

        state["response"] = self.correction_chain.invoke(input=payload)
        print("next question: ", state["response"])

        if self.debug:
            self._print_state(state, "After ask_for_correction")

        return state

    def run_graph(self, payload: dict) -> dict:
        """
        Runs the booking workflow graph with the given payload.

        Args:
            payload (dict): Initial payload containing at least the 'user_message' and other optional fields.

        Returns:
            dict: The final state after running the workflow.
        """
        # Ensure 'not_filled_keys' exists in the payload
        if "not_filled_keys" not in payload:
            payload["not_filled_keys"] = self.NECESSARY_INFORMATION.copy()

        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        return self.app.invoke(payload, config=config)


# Example usage:
if __name__ == "__main__":
    # Initialize the workflow in debug mode
    workflow = BookingWorkflow(debug=True)

    # Initial payload
    initial_payload = {
        "user_message": "I want to book a room.",
        "intent": "make a reservation",
        "not_filled_keys": workflow.NECESSARY_INFORMATION.copy(),
    }

    # Run the workflow
    result_state = workflow.run_graph(initial_payload)

    # Final state
    print("Final State:", json.dumps(result_state, indent=4, default=str))
