from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '../.env_test')  # will fail silently if file is missing
load_dotenv(dotenv_path, verbose=True)
