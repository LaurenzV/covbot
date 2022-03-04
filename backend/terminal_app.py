import json
import pathlib

from lib.database.querier import Querier
from lib.nlg.answer_generator import AnswerGenerator
from lib.nlu.message import MessageBuilder
from lib.spacy_components.custom_spacy import get_spacy

message_builder = MessageBuilder()
querier = Querier()
answer_generator = AnswerGenerator()
spacy = get_spacy()

if __name__ == '__main__':

    with open(pathlib.Path.cwd() / "tests" / "annotated_queries.json") as query_file:
        queries = json.load(query_file)

    sentences = ["Tell me the number of positive cases in denmark"]

    for sentence in sentences:
        new_sent = list(spacy(sentence).sents)[0]
        message = message_builder.create_message(new_sent)
        print("Reached")
        query_result = querier.query_intent(message)
        print("Passed")
        answer = answer_generator.generate_answer(query_result)
        print(sentence)
        print(answer)
        print()