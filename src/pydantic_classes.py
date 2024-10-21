from pydantic import BaseModel, Field
from typing import Optional, Literal, TypedDict


class IntentClassification(BaseModel):
    intent: Literal[
        "make a reservation", "check reservation", "change reservation", "other"
    ] = Field(..., description="The classified intent of the user's message")


class BookingInfo(BaseModel):
    full_name: Optional[str] = Field(None, description="The full name of the guest")
    check_in_date: Optional[str] = Field(
        None, description="Check-in date for the reservation"
    )
    check_out_date: Optional[str] = Field(
        None, description="Check-out date for the reservation"
    )
    num_guests: Optional[int] = Field(
        None, description="Number of guests for the reservation"
    )
    payment_method: Optional[str] = Field(
        None, description="Payment method used for the reservation"
    )
    breakfast_included: Optional[bool] = Field(
        None, description="Whether breakfast is included"
    )


# Define the state using TypedDict
class BookingState(TypedDict):
    user_message: Optional[str]
    intent: Optional[
        Literal[
            "make a reservation", "check reservation", "change reservation", "other"
        ]
    ]
    full_name: Optional[str]
    check_in_date: Optional[str]
    check_out_date: Optional[str]
    num_guests: Optional[int]
    payment_method: Optional[str]
    breakfast_included: Optional[bool]
    valid_info: Optional[bool]
    error: Optional[str]
    not_filled_keys: Optional[list[str]]
    response: Optional[str]
