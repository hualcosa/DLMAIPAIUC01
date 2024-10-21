from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List
from agent import BookingWorkflow

# Initialize FastAPI app
app = FastAPI()

# Initialize the BookingWorkflow instance
workflow = BookingWorkflow(debug=True)


# Define the request and response models for FastAPI
class BookingState(BaseModel):
    user_message: Optional[str] = None
    intent: Optional[
        Literal[
            "make a reservation", "check reservation", "other", "change reservation"
        ]
    ] = None
    full_name: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    num_guests: Optional[int] = None
    payment_method: Optional[str] = None
    breakfast_included: Optional[bool] = None
    valid_info: Optional[bool] = None
    error: Optional[List[str]] = None
    not_filled_keys: Optional[List[str]] = None
    response: Optional[str] = None


@app.post("/run_workflow/", response_model=BookingState)
async def run_workflow(state: BookingState):
    try:
        # Convert Pydantic model to dictionary
        state_dict = state.dict(exclude_unset=True)
        # Run the workflow graph with the given state
        updated_state = workflow.run_graph(state_dict)
        # Return the updated state
        return BookingState(**updated_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
