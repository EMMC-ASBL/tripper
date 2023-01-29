import os
import io
import stardog
from tripper import Literal
from typing import TYPE_CHECKING
from SPARQLWrapper import GET, JSON, POST, RDFXML, SPARQLWrapper

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Dict, Generator

    from SPARQLWrapper import QueryResult
    from tripper.triplestore import Triple


TRIPLESTORE_HOST = "localhost"
TRIPLESTORE_PORT = "5820"

class StardogStrategy():

    ## Class attributes
    __default_uname = "admin"
    __default_pwd = "admin"
    __serialization_format_supported = ["turtle", "rdf"]
    __parsing_format_supported = ["turtle", "rdf"]
    __content_types = {
        "turtle": "text/turtle",
        "rdf": "application/rdf+xml"
    }
    __file_extension = {
        "turtle": ".ttl",
        "rdf": ".rdf"
    }

    __sparql_endpoints = {}

    def __init__(self, base_iri: str, database: str, **kwargs) -> None:
        self.__uname = self.__default_uname
        self.__pwd = self.__default_pwd
        self.__database_name = database
        self.__admin = stardog.Admin(endpoint = base_iri)
        self.__database = self.__admin.database(database)
        self.__connection_details = {
            'endpoint': base_iri,
            'username': self.__uname,
            'password': self.__pwd
        }

        ## Setting SPARQLWrapper system
        stardog_query_endpoint = "{}/{}/query".format(base_iri, database)
        __sparql_query = SPARQLWrapper(endpoint=stardog_query_endpoint, **kwargs)
        __sparql_query.setCredentials(self.__uname, self.__pwd)
        self.__sparql_endpoints["query"] = __sparql_query

        stardog_update_endpoint = "{}/{}/update".format(base_iri, database)
        __sparql_update = SPARQLWrapper(endpoint=stardog_update_endpoint, **kwargs)
        __sparql_update.setCredentials(self.__uname, self.__pwd)
        self.__sparql_endpoints["update"] = __sparql_update

        self.__set_sparql_endpoint("query")

        try:
            self.__connection = stardog.Connection(self.__database_name, **self.__connection_details)
        except Exception as err:
            print("Unable to connect to Stardog instance: {}".format(self.__connection_details))


    @classmethod
    def list_databases(cls, **kwargs):
        __stardog_endpoint = "http://{}:{}".format(TRIPLESTORE_HOST, TRIPLESTORE_PORT)
        __admin: stardog.Admin = stardog.Admin(endpoint=__stardog_endpoint)
        databases = []

        try:
            databases = list(map(lambda x : x.name ,  __admin.databases()))
        except Exception as err:
            print("Exception occurred during databases listing: {}".format(err))

        return databases


    @classmethod
    def create_database(cls, database: str, **kwargs):
        __stardog_endpoint = "http://{}:{}".format(TRIPLESTORE_HOST, TRIPLESTORE_PORT)
        __admin: stardog.Admin = stardog.Admin(endpoint=__stardog_endpoint)

        databases = list(map(lambda x : x.name ,__admin.databases()))
        if not database in databases: 
            __admin.new_database(database)
        else:
            print("Database {} already exists".format(database))


    @classmethod
    def remove_database(cls, database: str, **kwargs):
        __stardog_endpoint = "http://{}:{}".format(TRIPLESTORE_HOST, TRIPLESTORE_PORT)
        __admin: stardog.Admin = stardog.Admin(endpoint=__stardog_endpoint)

        databases = list(map(lambda x : x.name , __admin.databases()))
        if not database in databases: 
            print("Database {} does not exists".format(database))
        else:
            __admin.database(database).drop()


    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        self.__set_sparql_endpoint("query")

        variables = [
            f"?{triple_name}"
            for triple_name, triple_value in zip("spo", triple)
            if triple_value is None
        ]
        if not variables: variables.append("*")
        where_spec = " ".join(
            f"?{triple_name}"
            if triple_value is None
            else triple_value
            if triple_value.startswith("<")
            else f"<{triple_value}>"
            for triple_name, triple_value in zip("spo", triple)
        )
        query = "\n".join(
            [
                f"SELECT {' '.join(variables)} WHERE {{",
                f"  {where_spec} .",
                "}",
            ]
        )
        self.sparql.setReturnFormat(JSON)
        self.sparql.setMethod(GET)
        self.sparql.setQuery(query)
        ret = self.sparql.queryAndConvert()
        for binding in ret["results"]["bindings"]:  # type: ignore              
            yield tuple(
                self.__convert_json_entrydict(binding[name]) if name in binding else value  # type: ignore
                for name, value in zip("spo", triple)
            )


    def add_triples(self, triples: "Sequence[Triple]") -> "QueryResult":
        self.__set_sparql_endpoint("update")
        spec = "\n".join(
            "  "
            + " ".join(
                value.n3()
                if isinstance(value, Literal)
                else value
                if value.startswith("<") or value.startswith("\"")
                else f"<{value}>"
                for value in triple
            )
            + " ."
            for triple in triples
        )
        query = f"INSERT DATA {{\n{spec}\n}}"
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()


    def remove(self, triple: "Triple") -> "QueryResult":
        self.__set_sparql_endpoint("update")

        spec = " ".join(
            f"?{name}"
            if value is None
            else value.n3()
            if isinstance(value, Literal)
            else value
            if value.startswith("<") or value.startswith("\"")
            else f"<{value}>"
            for name, value in zip("spo", triple)
        )
        query = f"DELETE WHERE {{ {spec} }}"
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()


    def query(self, query_object, **kwargs):

        query_str = str(query_object).strip()
        reasoning = kwargs.pop("reasoning", False)

        query_result = self.__connection.select(query_str, reasoning=reasoning)
        query_vars = query_result["head"]["vars"]    # type: ignore
        query_bindings = query_result["results"]["bindings"]     # type: ignore

        triples_res = []
        for binding in query_bindings:
            current_triple = ()
            for var in query_vars:
                current_triple = current_triple + (self.__convert_json_entrydict(binding[var]),)
            triples_res.append(current_triple)

        return triples_res


    def namespaces(self) -> dict:

        namespaces = {}
        for namespace in self.__database.namespaces():
            namespaces[namespace["prefix"]] = namespace["name"]

        return namespaces


    def bind(self, prefix: str, namespace: str):

        try:
            if namespace is None:
                self.__database.remove_namespace(prefix)
            else:
                self.__database.add_namespace(prefix, namespace)
        except Exception as err:
            print(err)


    def serialize(self, destination=None, format='turtle', **kwargs):

        if format not in self.__serialization_format_supported:
            print("Format {} not supported".format(format))
            return None

        stardog_content_type = stardog.content_types.TURTLE
        if format == "rdf":
            stardog_content_type = stardog.content_types.RDF_XML

        serialized_content = self.__connection.export(stardog_content_type)
        serialized_content = serialized_content if isinstance(serialized_content, str) else serialized_content.decode()  # type: ignore

        if destination is None:                     # Serialization on variable
            return serialized_content
        elif isinstance(destination, str):          # Serialization based on filename
            with open(destination, "w") as f:
                f.write(serialized_content)
            
            return None
        else:                                       # Serialization based on file object
            destination.write(serialized_content)
            
            return None
        
        
    def parse(self, source=None, location=None, data=None, format="turtle", **kwargs):

        if format not in self.__parsing_format_supported:
            raise Exception("Format not supported")

        specific_content = ""
        content_type = self.__content_types[format]

        if source is not None and isinstance(source, (io.IOBase, io.TextIOBase, io.BufferedIOBase, io.RawIOBase)):
            content = source.read()
            specific_content = stardog.content.Raw(content, content_type)

        elif (source is not None and isinstance(source, str)) or (location is not None):
            to_parse = source if source is not None else location
            filename, file_extension = os.path.splitext(str(to_parse))
            if self.__file_extension[format] != file_extension:
                raise Exception("File extensione not coherent with format")
            specific_content = stardog.content.File(to_parse, content_type)

        elif data is not None:
            specific_content = stardog.content.Raw(data, content_type)

        else:
            raise Exception("Error during argument checking\nOnly one among source, location and data must be provided\n")

        self.__connection.begin()
        self.__connection.add(specific_content)
        self.__connection.commit()


    ## Private methods
    def __set_sparql_endpoint(self, type: str = "query"):

        print("Swapping active sparql endpoint to {}".format(type))
        
        self.sparql = self.__sparql_endpoints[type]


    def __convert_json_entrydict(self, entrydict: "Dict[str, str]") -> str:  # type: ignore
        if entrydict["type"] == "uri":
            return entrydict["value"]

        if entrydict["type"] == "literal":
            return Literal(
                entrydict["value"],
                lang=entrydict.get("xml:lang"),
                datatype=entrydict.get("datatype"),
            )

        if entrydict["type"] == "bnode":
            return (
                entrydict["value"]
                if entrydict["value"].startswith("_:")
                else f"_:{entrydict['value']}"
            )

        raise ValueError(f"unexpected type in entrydict: {entrydict}")