
import json

from django.core.exceptions import ValidationError
from django.core.validators import *

# ---- JSON validators ----


def validate_json(value, python_type=None):
    """
    Validate a text field value. None and "" are treated as empty but valid strings.
    Raises a ValidationError or returns nothing.

    :param value: The text field value
    :param python_type: The type to which the string should evaluate
    """
    if value:
        try:
            val = json.loads(value)
            if python_type:
                if not isinstance(val, python_type):
                    raise ValidationError("Object is not of type %s" % python_type)
            return val
        except ValueError as e:
            raise ValidationError("Invalid JSON: %s" % e)


def validate_json_dict(value):
        """
        Shortcut to validate_json(value, python_type=dict)

        :param value: The text field value
        """
        val = validate_json(value, python_type=dict)
        return val if val else {}


def validate_json_list(value):
    """
    Shortcut to validate_json(value, python_type=list)

    :param value: the text field value
    """
    val = validate_json(value, python_type=list)
    return val if val else []


# ---- parameter validators ----

def validate_numeric_range(value, min_value=None, max_value=None):
    # TODO write numeric range validator
    pass


# ---- validate a list of validators...meta right? ----

def validate_validator_list(value):
    # a json list of strings, all of which are functions in this module or
    # regular expressions
    lst = validate_json_list(value)
    # TODO: complete validator list validator

