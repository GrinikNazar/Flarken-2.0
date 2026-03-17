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

    def get_list_of_part_types(self, part_type_id):
        url = f'{self.base_url}/warehouse/list-of-part-types/'
        response = requests.get(url, params={'part_type_id': part_type_id}).json()
        return response

    def get_purchase_list_part_supplier(self, supplier_id, part_type_id):
        url = f'{self.base_url}/warehouse/purchase-list-part-type/'
        response = requests.get(url, params={
            'supplier_id': supplier_id,
            'part_type_id': part_type_id
        }).json()
        return response
