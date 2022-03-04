import json
import pathlib

import pytest

from lib.database.querier import Querier
#from lib.nlg.answer_generator import AnswerGenerator
from lib.nlu.message import MessageBuilder
from lib.spacy_components.custom_spacy import get_spacy

with open(pathlib.Path(__file__).parent / "annotated_queries.json") as query_file:
    queries = json.load(query_file)

spacy = get_spacy()
message_builder = MessageBuilder()
querier = Querier()
#answer_generator = AnswerGenerator()


@pytest.mark.parametrize("query", queries)
@pytest.mark.skip
def test_whole_pipeline(query):
    new_sent = list(spacy(query["query"]).sents)[0]
    message = message_builder.create_message(new_sent)
    query_result = querier.query_intent(message)
    #answer_generator.generate_answer(query_result)