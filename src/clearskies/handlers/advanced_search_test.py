import unittest
from .advanced_search import AdvancedSearch
from ..column_types import String, Integer
from ..di import StandardDependencies
from ..authentication import Public, SecretBearer
from ..model import Model
from ..contexts import test
from collections import OrderedDict


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("id", {"class": String}),
                ("name", {"class": String}),
                ("email", {"class": String}),
                ("age", {"class": Integer}),
            ]
        )


class AdvancedSearchTest(unittest.TestCase):
    def setUp(self):
        self.advanced_search = test(
            {
                "handler_class": AdvancedSearch,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                },
            }
        )
        self.users = self.advanced_search.build(User)
        self.users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        self.users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})
        self.users.create({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": "15"})
        self.users.create({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": "25"})
        self.users.create({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": "35"})

    def test_simple_read(self):
        response = self.advanced_search()
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 5, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": 6}, response_data[0])
        self.assertEqual({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": 8}, response_data[1])
        self.assertEqual({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": 15}, response_data[2])
        self.assertEqual({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": 25}, response_data[3])
        self.assertEqual({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": 35}, response_data[4])

    def test_case_switch(self):
        advanced_search = test(
            {
                "handler_class": AdvancedSearch,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name", "age"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = advanced_search.build(User)
        users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})

        response = advanced_search(
            body={
                "Where": [
                    {"Column": "Age", "Operator": "<", "Value": 7},
                ]
            }
        )

        json_response = response[0]
        response_data = json_response["Data"]
        self.assertEqual("Success", json_response["Status"])
        self.assertEqual({"NumberResults": 1, "NextPage": {}, "Limit": 100}, json_response["Pagination"])
        self.assertEqual({"Id": "1", "Name": "ronoc", "Email": "cmancone1@example.com", "Age": 6}, response_data[0])

    def test_fancy_search(self):
        response = self.advanced_search(
            body={
                "where": [
                    {"column": "name", "operator": "=", "value": "ronoc"},
                ]
            }
        )
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 3, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": 6}, response_data[0])
        self.assertEqual({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": 25}, response_data[1])
        self.assertEqual({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": 35}, response_data[2])

    def test_column_name_search_check(self):
        response = self.advanced_search(
            body={
                "where": [
                    {"column": "name", "operator": "=", "value": "ronoc"},
                    {"column": "age", "operator": "<=", "value": "25"},
                ]
            }
        )
        json_response = response[0]
        self.assertEqual(400, response[1])
        self.assertEqual("client_error", json_response["status"])
        self.assertEqual("Invalid request: invalid search column specified in where entry #2", json_response["error"])

    def test_doc(self):
        advanced_search = AdvancedSearch(StandardDependencies())
        advanced_search.configure(
            {
                "model_class": User,
                "readable_columns": ["id", "name", "email", "age"],
                "searchable_columns": ["name", "email"],
                "default_sort_column": "email",
                "authentication": Public(),
            }
        )

        documentation = advanced_search.documentation()
        self.assertEqual(1, len(documentation))
        search_doc = documentation[0]

        self.assertEqual([""], [doc.relative_path for doc in documentation])
        self.assertEqual([["POST"]], [doc.request_methods for doc in documentation])

        # Check our 'search' endpoint which returns all records with fancy search options
        self.assertEqual(2, len(search_doc.responses))
        self.assertEqual([200, 400], [response.status for response in search_doc.responses])
        self.assertEqual(
            ["status", "data", "pagination", "error", "input_errors"],
            [schema.name for schema in search_doc.responses[0].schema.children],
        )
        data_response_properties = search_doc.responses[0].schema.children[1].item_definition
        self.assertEqual(["id", "name", "email", "age"], [prop.name for prop in data_response_properties.children])
        self.assertEqual(
            ["string", "string", "string", "integer"], [prop._type for prop in data_response_properties.children]
        )
        self.assertEqual(
            ["where", "sort", "limit", "start"], [param.definition.name for param in search_doc.parameters]
        )
        self.assertEqual(3, len(search_doc.parameters[0].definition.item_definition.children))
        self.assertEqual(
            ["column", "operator", "value"],
            [child.name for child in search_doc.parameters[0].definition.item_definition.children],
        )
        self.assertEqual(["name", "email"], search_doc.parameters[0].definition.item_definition.children[0].values)

    def test_doc_with_casing(self):
        advanced_search = AdvancedSearch(StandardDependencies())
        advanced_search.configure(
            {
                "model_class": User,
                "readable_columns": ["id", "name", "email", "age"],
                "searchable_columns": ["name", "email"],
                "default_sort_column": "email",
                "authentication": Public(),
                "internal_casing": "snake_case",
                "external_casing": "TitleCase",
            }
        )

        documentation = advanced_search.documentation()
        self.assertEqual(1, len(documentation))
        search_doc = documentation[0]

        self.assertEqual([""], [doc.relative_path for doc in documentation])
        self.assertEqual([["POST"]], [doc.request_methods for doc in documentation])

        # Check our 'search' endpoint which returns all records with fancy search options
        self.assertEqual(2, len(search_doc.responses))
        self.assertEqual([200, 400], [response.status for response in search_doc.responses])
        self.assertEqual(
            ["Status", "Data", "Pagination", "Error", "InputErrors"],
            [schema.name for schema in search_doc.responses[0].schema.children],
        )
        data_response_properties = search_doc.responses[0].schema.children[1].item_definition
        self.assertEqual(["Id", "Name", "Email", "Age"], [prop.name for prop in data_response_properties.children])
        self.assertEqual(
            ["string", "string", "string", "integer"], [prop._type for prop in data_response_properties.children]
        )
        self.assertEqual(
            ["Where", "Sort", "Limit", "Start"], [param.definition.name for param in search_doc.parameters]
        )
        self.assertEqual(3, len(search_doc.parameters[0].definition.item_definition.children))
        self.assertEqual(
            ["Column", "Operator", "Value"],
            [child.name for child in search_doc.parameters[0].definition.item_definition.children],
        )
        self.assertEqual(["Name", "Email"], search_doc.parameters[0].definition.item_definition.children[0].values)
