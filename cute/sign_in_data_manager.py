import json
import os
from common.log import logger

class SignInDataManager:

    def __init__(self, file_name='sign_in_data.json'):
        self.file_name = file_name
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.file_name):
            with open(self.file_name, "w") as f:
                json.dump({}, f)

    def get_data(self):
        try:
            with open(self.file_name) as file:
                return json.load(file)
        except Exception as e:
            logger.debug('Load data failed: %s' % str(e))
            return {}

    def save_data(self, sign_in_data):
        try:
            with open(self.file_name, 'w') as file:
                json.dump(sign_in_data, file)
        except Exception as e:
            logger.debug('Save data failed: %s' % str(e))

