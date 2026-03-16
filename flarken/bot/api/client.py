import os
import requests
from dotenv import load_dotenv


load_dotenv()


class APIClient:

    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL')

    def get_purchase_list(self, supplier_id):
        url = f'{self.base_url}/warehouse/purchase-list/'
        response = requests.get(url, params={'supplier_id': supplier_id}).json()
        return response
