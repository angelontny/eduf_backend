# Unused, structured outputs in cohere requires tool usage
from pydantic import BaseModel, Field

class Flash(BaseModel):
    ''' A question and answer pair with a topic describing them from the given information. '''
    topic: str = Field(description="Short topic of the question and answer pair.")
    question: str = Field(description="A question regarding a single topic from the given information.")
    answer: str = Field(description="The answer for the above question.")

class FlashCards(BaseModel):
    ''' Collection of question and answer generated from the text'''
    cards: list[Flash] = Field(description="A collection of question and answers for all the topics in the documents")

class QA(BaseModel):
    ''' A multiple choice question along with the answer generated from the given information '''
    question: str = Field(description="The question")
    opta: str = Field(description="Option A of the question")
    optb: str = Field(description="Option B of the question")
    optc: str = Field(description="Option C of the question")
    optd: str = Field(description="Option D of the question")
    answer: str = Field(description="The correct option for the questions. Can  only be a, b, c or d")

class QAS(BaseModel):
    ''' A list of multiple choice questions '''
    qas: list[QA] = Field(description="A list of multiple choice questions")
