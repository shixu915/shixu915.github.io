import json
import os
import random

class RoleManager:
    def __init__(self, roles):
        self.roles = roles
        self.file_path = 'role.json'
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    def read_role_data(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def write_role_data(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

    def get_role(self, user_id):
        role_data = self.read_role_data()
        return role_data.get(user_id, None)

    def set_role(self, user_id, role):
        role_data = self.read_role_data()
        role_data[user_id] = role
        self.write_role_data(role_data)

    def extract_random_role(self, user_id):
        user_role = self.get_role(user_id)
        if user_role is None:
            chosen_role = random.choice(self.roles)
            role = {
                "name": chosen_role,
                "attack": random.randint(10, 100),
                "defense": random.randint(10, 100),
                "speed": random.randint(10, 100)
            }
            self.set_role(user_id, role)
            return chosen_role
        else:
            return None
