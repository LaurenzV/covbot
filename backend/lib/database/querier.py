from datetime import datetime, timedelta, date
from dataclasses import dataclass
from typing import Union, Optional, List, Type
from sqlalchemy.sql import func, functions

import calendar

from lib.database.database_connection import DatabaseConnection
from sqlalchemy.orm import Session
from enum import Enum
from sqlalchemy import and_

from lib.database.entities import Case, Vaccination
from lib.nlu.intent.calculation_type import CalculationType
from lib.nlu.intent.measurement_type import MeasurementType
from lib.nlu.intent.value_domain import ValueDomain
from lib.nlu.intent.value_type import ValueType
from lib.nlu.message import MessageBuilder, Message
from lib.nlu.topic.topic import Topic
from lib.spacy_components.spacy import get_spacy


class QueryResultCode(Enum):
    SUCCESS = 1
    UNKNOWN_TOPIC = 2
    AMBIGUOUS_TOPIC = 3
    UNKNOWN_MEASUREMENT_TYPE = 4
    UNKNOWN_VALUE_DOMAIN = 5
    UNKNOWN_CALCULATION_TYPE = 6
    UNKNOWN_VALUE_TYPE = 7
    NO_WORLDWIDE_SUPPORTED = 8


@dataclass
class QueryResult:
    message: Message
    result_code: QueryResultCode
    result: Optional[Union[str, int]]
    information: Optional[dict]


class Querier:
    def __init__(self):
        self.engine = DatabaseConnection().create_engine("covbot")
        self.session = Session(self.engine, future=True)
        self.case_query = self.session.query(Case)
        self.vaccination_query = self.session.query(Vaccination)

    def query_intent(self, msg: Message) -> QueryResult:
        validation_result = self._validate_msg(msg)
        print(msg)

        if validation_result:
            return validation_result

        table_dict = {
            Topic.CASES: Case,
            Topic.VACCINATIONS: Vaccination
        }

        column_dict = {
            MeasurementType.DAILY: {
                ValueDomain.POSITIVE_CASES: Case.cases,
                ValueDomain.ADMINISTERED_VACCINES: Vaccination.daily_vaccinations,
                ValueDomain.VACCINATED_PEOPLE: Vaccination.daily_people_vaccinated
            },
            MeasurementType.CUMULATIVE: {
                ValueDomain.POSITIVE_CASES: Case.cumulative_cases,
                ValueDomain.ADMINISTERED_VACCINES: Vaccination.total_vaccinations,
                ValueDomain.VACCINATED_PEOPLE: Vaccination.people_vaccinated
            }
        }

        table = table_dict[msg.topic]
        considered_column = column_dict[msg.intent.measurement_type][msg.intent.value_domain]
        time_condition = self._get_time_from_condition(table, msg)
        country_condition = self._get_country_from_condition(table, msg)

        if msg.intent.calculation_type == CalculationType.RAW_VALUE:
            query = self.session.query(table).with_entities(considered_column)
        elif msg.intent.calculation_type == CalculationType.SUM:
            query = self.session.query(functions.sum(considered_column))
        elif msg.intent.calculation_type == CalculationType.MAXIMUM:
            query = self.session.query(functions.max(considered_column))
        elif msg.intent.calculation_type == CalculationType.MINIMUM:
            query = self.session.query(functions.min(considered_column))
        else:
            raise NotImplementedError()


        query = query.where(and_(
            *time_condition, *country_condition
        ))

        print(query.all())





    def _get_country_from_condition(self, table: Type[Union[Case, Vaccination]], msg: Message) -> List[bool]:
        if msg.slots.location is None:
            raise NotImplementedError()
        else:
            return [table.country_normalized == msg.slots.location]

    def _get_time_from_condition(self, table: Type[Union[Case, Vaccination]], msg: Message) -> List[bool]:
        # We assume the user is asking for today if no timeframe is specified
        if msg.slots.date is None:
            return [table.date == datetime.now().date()]

        date_type = msg.slots.date.value["time"]
        date_value = msg.slots.date.value["value"]
        if date_type == "DAY":
            return [table.date == msg.slots.date.value["value"]]
        elif date_type == "WEEK":
            start = date_value - timedelta(days=date_value.weekday())
            end = start + timedelta(days=6)
            return [table.date >= start, table.date <= end]
        elif date_type == "MONTH":
            start = date_value.replace(day=1)
            end = date_value.replace(day=calendar.monthrange(date_value.year, date_value.month)[1])
            return [table.date >= start, table.date <= end]
        elif date_type == "YEAR":
            start = date(date_value.year, 1, 1)
            end = date(date_value.year, 12, 31)
            return [table.date >= start, table.date <= end]
        else:
            raise NotImplementedError()


    def _validate_msg(self, msg: Message) -> Optional[QueryResult]:
        if msg.topic == Topic.UNKNOWN:
            return QueryResult(msg, QueryResultCode.UNKNOWN_TOPIC, None, None)
        if msg.topic == Topic.AMBIGUOUS:
            return QueryResult(msg, QueryResultCode.AMBIGUOUS_TOPIC, None, None)
        if msg.intent.measurement_type == MeasurementType.UNKNOWN:
            return QueryResult(msg, QueryResultCode.UNKNOWN_MEASUREMENT_TYPE, None, None)
        if msg.intent.value_domain == ValueDomain.UNKNOWN:
            return QueryResult(msg, QueryResultCode.UNKNOWN_VALUE_DOMAIN, None, None)
        if msg.intent.calculation_type == CalculationType.UNKNOWN:
            return QueryResult(msg, QueryResultCode.UNKNOWN_CALCULATION_TYPE, None, None)
        if msg.intent.value_type == ValueType.UNKNOWN:
            return QueryResult(msg, QueryResultCode.UNKNOWN_VALUE_TYPE, None, None)
        if msg.intent.value_type != ValueType.LOCATION and msg.slots.location is None:
            return QueryResult(msg, QueryResultCode.NO_WORLDWIDE_SUPPORTED, None, None)

        return None


if __name__ == '__main__':
    sentence = "What is the lowest number of vaccinated people in Germany last week?"
    spacy = get_spacy()
    doc = spacy(sentence)
    querier = Querier()

    mb = MessageBuilder()
    msg = mb.create_message(list(doc.sents)[0])
    querier.query_intent(msg)
