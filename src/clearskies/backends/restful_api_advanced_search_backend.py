from .api_backend import ApiBackend
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger
class RestfulApiAdvancedSearchBackend(ApiBackend):
    _requests = None
    _auth = None
    _records = None

    _allowed_configs = [
        'wheres',
        'sorts',
        'limit',
        'pagination',
        'table_name',
        'model_columns',
    ]

    _empty_configs = [
        'group_by_column',
        'selects',
        'joins',
    ]

    def __init__(self, requests):
        self._requests = requests

    def configure(self, auth=None):
        self._auth = auth

    def update(self, id, data, model):
        [url, method, json_data, headers] = self._build_update_request(id, data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        if not response.content:
            return {**model.data, **data}
        return self._map_update_response(response.json())

    def _build_update_request(self, id, data, model):
        url = model.table_name().rstrip('/')
        return [f'{url}/{id}', 'PATCH', data, {}]

    def _map_update_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected API response to update request")
        return json['data']

    def create(self, data, model):
        [url, method, json_data, headers] = self._build_create_request(data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_create_response(response.json())

    def _build_create_request(self, data, model):
        return [model.table_name().rstrip('/'), 'POST', data, {}]

    def _map_create_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected API response to create request")
        return json['data']

    def delete(self, id, model):
        [url, method, json_data, headers] = self._build_delete_request(id, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._validate_delete_response(response.json())

    def _build_delete_request(self, id, model):
        url = model.table_name().rstrip('/')
        return [f'{url}/{id}', 'DELETE', {}, {}]

    def _validate_delete_response(self, json):
        if 'status' not in json:
            raise ValueError("Unexpected response to delete API request")
        return json['status'] == 'success'

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_count_request(configuration, model)
        response = self._execute_request(url, method, json=json_data, headers=headers, retry_auth=True)
        return self._map_count_response(response.json())

    def _build_count_request(self, configuration, model):
        url = model.table_name().rstrip('/') + '/search'
        return [url, 'POST', {**{'count_only': True}, **self._as_post_data(configuration)}, {}]

    def _map_count_response(self, json):
        if not 'total_matches' in json:
            raise ValueError("Unexpected API response when executing count request")
        return json['total_matches']

    def records(self, configuration, model, next_page_data=None):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration, model)
        response = self._execute_request(url, method, json=json_data, headers=headers, retry_auth=True)
        records = self._map_records_response(response.json())
        if type(next_page_data) == dict:
            limit = configuration.get('limit', None)
            start = configuration.get('pagination', {}).get('start', 0)
            if limit and len(records) == limit:
                next_page_data['start'] = start + limit
        return records

    def _build_records_request(self, configuration, model):
        url = model.table_name().rstrip('/') + '/search'
        return [url, 'POST', self._as_post_data(configuration), {}]

    def _map_records_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected response from records request")
        return json['data']

    def _as_post_data(self, configuration):
        data = {
            'where': list(map(lambda where: self._where_for_post(where), configuration['wheres'])),
            'sort': configuration['sorts'],
            'start': configuration['pagination'].get('start', 0),
            'limit': configuration['limit'],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where):
        return {
            'column': where['column'],
            'operator': where['operator'],
            'value': where['values'][0],
        }