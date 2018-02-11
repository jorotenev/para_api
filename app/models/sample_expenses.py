from json import load

import os

_dir_path = os.path.dirname(os.path.realpath(__file__))

with open(_dir_path + "/../para-common/sample_expenses.json") as file:  # todo better way to reference the file
    sample_expenses = load(file)
