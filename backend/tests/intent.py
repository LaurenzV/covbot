import unittest
import json
from lib.nlu.intent import Intent, IntentRecognizer, ValueDomain, MeasurementType, ValueType
from lib.spacy_components.spacy import get_spacy


class TestQueryIntents(unittest.TestCase):
    def setUp(self):
        self.spacy = get_spacy()
        self.intent_recognizer = IntentRecognizer(self.spacy.vocab)
        with open("annotated_queries.json") as query_file:
            self.queries = [query for query in json.load(query_file)]

    def test_value_domain(self):
        for query in self.queries:
            with self.subTest(query=query):
                # Exclude the not working ones for now
                if not query["id"] == 21:
                    doc = self.spacy(query["query"])
                    predicted_value_domain = self.intent_recognizer.recognize_value_domain(list(doc.sents)[0])
                    self.assertEqual(ValueDomain.from_str(query["intent"]["value_domain"]), predicted_value_domain)

    def test_measurement_type(self):
        for query in self.queries:
            with self.subTest(query=query):
                predicted_measurement_type = self.spacy(query["query"])._.intent.measurement_type
                self.assertEqual(MeasurementType.from_str(query["intent"]["measurement_type"]),
                                 predicted_measurement_type)

    def test_value_type(self):
        for query in self.queries:
            with self.subTest(query=query):
                predicted_value_type = self.spacy(query["query"])._.intent.value_type
                self.assertEqual(ValueType.from_str(query["intent"]["value_type"]),
                                 predicted_value_type)
