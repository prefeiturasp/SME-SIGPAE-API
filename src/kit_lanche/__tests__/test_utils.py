import datetime

import pytest

from ..utils import date_to_string, string_to_date


def test_datetime_to_string():
    date_one = datetime.datetime(2019, 1, 1)
    date_two = datetime.datetime(2019, 12, 31)
    assert date_to_string(date_one) == "01/01/2019"
    assert date_to_string(date_two) == "31/12/2019"


def test_datetime_to_string_tratando_excecoes():
    with pytest.raises(AssertionError, match="date precisa ser `datetime.date`"):
        date_to_string(1)
    with pytest.raises(AssertionError, match="date precisa ser `datetime.date`"):
        date_to_string("datetime(2019, 1, 1).date()")


def test_string_to_date():
    date_one = "01/01/2019"
    date_two = "31/12/2019"
    assert string_to_date(date_one) == datetime.date(2019, 1, 1)
    assert string_to_date(date_two) == datetime.date(2019, 12, 31)


def test_string_to_date_tratando_excecoes():
    with pytest.raises(AssertionError, match="date_string precisa ser `string`"):
        string_to_date(1)
    with pytest.raises(AssertionError, match="date_string precisa ser `string`"):
        string_to_date(True)
    with pytest.raises(
        ValueError, match="time data 'abc' does not match format '%d/%m/%Y"
    ):
        string_to_date("abc")
    with pytest.raises(
        ValueError, match="time data '20190108' does not match format '%d/%m/%Y"
    ):
        string_to_date("20190108")
