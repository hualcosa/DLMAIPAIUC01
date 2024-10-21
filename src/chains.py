from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pydantic_classes import IntentClassification, BookingInfo
from prompts import (
    intent_prompt,
    booking_info_prompt,
    booking_change_prompt,
    response_chain_sys_prompt,
    response_chain_human_message,
    summarization_chain_sys_prompt,
    summarization_chain_human_message,
    correction_chain_prompt,
)

load_dotenv()


# LangChain setup for intent detection
def create_intent_chain():
    # LangChain setup for intent detection
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Create a structured output chain for intent detection
    intent_chain = intent_prompt | llm.with_structured_output(IntentClassification)

    return intent_chain


def create_booking_info_chain():
    # LangChain setup for booking information extraction
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Create a structured output chain for booking information extraction
    booking_info_chain = booking_info_prompt | llm.with_structured_output(BookingInfo)

    return booking_info_chain


def create_booking_change_chain():
    # LangChain setup for changing information characteristics
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Create a structured output chain for booking information extraction
    booking_change_chain = booking_change_prompt | llm.with_structured_output(
        BookingInfo
    )

    return booking_change_chain


def create_response_generation_chain():
    # Create the chat prompt template
    generate_response_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(response_chain_sys_prompt),
        HumanMessagePromptTemplate.from_template(response_chain_human_message),
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response_chain = generate_response_prompt | llm | StrOutputParser()

    return response_chain


def create_summarization_chain():
    # Create the chat prompt template
    summarize_booking_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(summarization_chain_sys_prompt),
        HumanMessagePromptTemplate.from_template(summarization_chain_human_message),
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    summarize_booking_chain = summarize_booking_prompt | llm | StrOutputParser()

    return summarize_booking_chain


def create_correction_chain():
    # Create the chain
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    correction_chain = correction_chain_prompt | llm | StrOutputParser()
    return correction_chain
