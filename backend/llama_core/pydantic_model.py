# Unused, structured outputs in cohere requires tool usage
from pydantic import BaseModel, Field

class Flash(BaseModel):
    ''' A single flash card with useful information '''
    topic: str = Field(description="Short topic of the flash card")
    question: str = Field(description="A question regarding a topic")
    answer: str = Field(description="The answer for the question")

class FlashCards(BaseModel):
    ''' Collection of flash cards generated from the text'''
    cards: list[Flash] = Field(description="A collection of flash cards for all the topics in the documents")
