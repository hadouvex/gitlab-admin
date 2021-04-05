import pathlib

from dotenv import dotenv_values


ENV_FILE_NAME='.env'
curr_path = pathlib.Path().absolute()
env = dotenv_values(f'{curr_path}/{ENV_FILE_NAME}')