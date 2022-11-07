import warnings
from typing import TYPE_CHECKING

import requests
import io
import os

from tripper import Literal as tripperLiteral
from rdflib import URIRef, BNode, Variable
from rdflib import Literal as rdflibLiteral

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator
    from tripper import Triple

def convertToSPARQLTerm(value, var_name = None):
    """
    Value can be one of:
    * Literal (plain or typed)
    * URI (prefixed type is not addressed)
    * Blank node
    * None (variable)
    """

    # Case None
    var_name_def = var_name if var_name is not None else "var"
    if value is None:
        return Variable(var_name_def)

    # Case Blank Node
    if value.startswith("_:"):
        return BNode(value[2:])

    # Case Literal
    if isinstance(value, tripperLiteral):
        return value

    # Case URI
    return URIRef(value)



class OntorecStrategy:
    """
    Triplestore strategy for OntoREC and OntoKB
    """

    def __init__(self, base_iri: str, database_name: str, ip: str, port: int):
        self.db_name = database_name
        self.ip = ip
        self.port = port

        # Test if service is running on specified endpoint
        try:
            welcome_page_response = requests.get("http://{}:{}".format(self.ip, self.port))
        except Exception:
            raise Exception("Service not active on http://{}:{}".format(self.ip, self.port))
        
        if welcome_page_response.status_code != 200:
            raise Exception("Service not active on http://{}:{}".format(self.ip, self.port))

        # Test if database exists
        databases_page_response = requests.get("http://{}:{}/databases".format(self.ip, self.port))
        json_response = databases_page_response.json()
        if self.db_name not in json_response["dbs"]:
            raise Exception("Database {} does not exists".format(self.db_name))

        if base_iri is None:
            return

        # Check if the base iri is already that
        base_namespace_response = requests.get("http://{}:{}/databases/{}/namespaces/base".format(self.ip, self.port, self.db_name))
        
        if base_namespace_response.status_code == 200:
            # The database has a base namespace active
            base_namespace = base_namespace_response.json()
            current_base_iri = base_namespace["iri"]
            if current_base_iri == base_iri:
                return

            try:
                delete_response = requests.delete("http://{}:{}/databases/{}/namespaces/base".format(self.ip, self.port, self.db_name))
            except Exception:
                raise Exception("Cannot delete old namespace {}".format(current_base_iri))

            if delete_response.status_code != 204:
                raise Exception("Cannot delete old namespace {}".format(current_base_iri))

            base_substitute={}
            base_substitute["prefix"] = "stardog-api" if current_base_iri == "http://api.stardog.com/" else current_base_iri.split("/")[-1]
            base_substitute["prefix"] = base_substitute["prefix"][:-1] if base_substitute["prefix"].endswith("#") else base_substitute["prefix"]
            base_substitute["iri"] = current_base_iri

            response = requests.post(
                "http://{}:{}/databases/{}/namespaces".format(self.ip, self.port, self.db_name),
                json=base_substitute
            )

            if response.status_code != 201:
                raise Exception("Cannot add new replaced namespace {}".format(current_base_iri))

        # Set the new base iri
        new_base={}
        new_base["prefix"] = "base"
        new_base["iri"] = base_iri

        response = requests.post(
            "http://{}:{}/databases/{}/namespaces".format(self.ip, self.port, self.db_name),
            json=new_base
        )

        if response.status_code != 201:
            raise Exception("Cannot add new base namespace {}".format(current_base_iri))


    def triples(self, triple: "Triple") -> "Generator":
        """
        Returns a generator over matching triples
        """
        s, p, o = triple
        s_varname, p_varname, o_varname = ("s", "p", "o")
        s_var, p_var, o_var = (Variable(s_varname), Variable(p_varname), Variable(o_varname))
        
        s_converted = convertToSPARQLTerm(s, s_varname)
        p_converted = convertToSPARQLTerm(p, p_varname)
        o_converted = convertToSPARQLTerm(o, o_varname)

        query_fields = {}
        query_fields["s"] = (s_var.n3(), s_converted.n3())
        query_fields["p"] = (p_var.n3(), p_converted.n3())
        query_fields["o"] = (o_var.n3(), o_converted.n3())
        query = {}
        query["reasoning"] = False
        query["query"] = "SELECT " + query_fields["s"][0] + " " + query_fields["p"][0] + " " + query_fields["o"][0] + " WHERE { " + query_fields["s"][1] + " " + query_fields["p"][1] + " " + query_fields["o"][1] + " }"
    
        query_response = requests.post("http://{}:{}/databases/{}/query".format(self.ip, self.port, self.db_name), json=query)
        if query_response.status_code != 200:
            raise Exception("Error during query: {}".format(query_response.text))

        json_response = query_response.json()
        bindings = json_response["results"]["bindings"]

        for binding in bindings:
            triple_res = []
            triple_res.append(s if isinstance(s_converted, Variable) == False else binding["s"]["value"])
            triple_res.append(p if isinstance(p_converted, Variable) == False else binding["p"]["value"])
            triple_res.append(o if isinstance(o_converted, Variable) == False else binding["o"]["value"])

            yield triple_res

    #
    #   It levarages on the '/single' POST endpoint to save the set of triples
    #   The triples must be in turtle format.
    #

    def add_triples(self, triples: "Sequence[Triple]"):
        """
        Add a sequence of triples
        """
        
        content={}
        content["triples"] = []
        for triple in triples:
            s, p, o = triple
            entry = {}
            entry["s"] = convertToSPARQLTerm(s).n3()
            entry["p"] = convertToSPARQLTerm(p).n3()
            entry["o"] = convertToSPARQLTerm(o).n3()
            content["triples"].append(entry)

        print(content)
        response = requests.post(
            "http://{}:{}/databases/{}/single".format(self.ip, self.port, self.db_name),
            json=content
        )

    #
    #   It levarages on the '/single' DELETE endpoint to delete the set of triples
    #   The triples must be in turtle format.
    #

    def remove(self, triple: "Triple"):
        """
        Remove triple from the backend
        """
       
        content={}
        content["triples"] = []
        s, p, o = triple
        entry = {}
        entry["s"] = convertToSPARQLTerm(s).n3()
        entry["p"] = convertToSPARQLTerm(p).n3()
        entry["o"] = convertToSPARQLTerm(o).n3()
        content["triples"].append(entry)

        response = requests.delete(
            "http://{}:{}/databases/{}/single".format(self.ip, self.port, self.db_name),
            json=content
        )

    #
    #   It levarages on the '/query' POST endpoint to submit a generic SPARQL query - only reading, no UPDATE query
    #   It assumes that query_object is the string of SPARQL query
    #
    
    def query(self, query_object, **kwargs):
        """
        SPARQL query
        """

        query_structure = {}
        query_structure["query"] = str(query_object)
        query_structure["reasoning"] = False

        response = requests.post(
            "http://{}:{}/databases/{}/query".format(self.ip, self.port, self.db_name),
            json=query_structure
        )
        # return response.json()

        json_response = response.json()
        bindings = json_response["results"]["bindings"]
        vars = json_response["head"]["vars"]
        triples = []

        for binding in bindings:
            triple_res = ()
            for var in vars:
                triple_res = triple_res + (binding[var]["value"],)
            triples.append(triple_res)

        return triples

    #
    #   It levarages on the '/namespaces' GET endpoint to get all the namespace for a specific database
    #

    def namespaces(self) -> dict:
        """
        Returns a dict mapping prefixes to namespaces.
        """

        namespaces_dict = {}
        namespaces = requests.get("http://{}:{}/databases/{}/namespaces".format(self.ip, self.port, self.db_name))

        for namespace in (namespaces.json())["namespaces"]:
            namespaces_dict[namespace["prefix"]] = namespace["iri"]

        return namespaces_dict

    def bind(self, prefix: str, namespace: str):
        """
        Bind prefix to namespace.
        """

        namespace_obj={}
        namespace_obj["prefix"] = prefix
        namespace_obj["iri"] = str(namespace)

        print(namespace_obj)

        response = requests.post(
            "http://{}:{}/databases/{}/namespaces".format(self.ip, self.port, self.db_name),
            json=namespace_obj
        )

        if response.status_code == 409:
            print("Namespace already exists...skipping")
        elif response.status_code != 201:
            raise Exception("Error during namespace binding: {}".format(response.text))

    
    def serialize(self, destination=None, format='turtle', **kwargs):
        """
        Serialise to destination.

        Parameters:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            kwargs: Additional backend-specific parameters controlling
                the serialisation.

        Returns:
            Serialised string if `destination` is None.
        """

        if format!="turtle":
            raise Exception("Only turtle format is supported")

        serialized_content_response = requests.get("http://{}:{}/databases/{}/serialization".format(self.ip, self.port, self.db_name))

        if serialized_content_response.status_code != 200:
            raise Exception("Error during database serialization")

        serialized_content = (serialized_content_response.json())["content"]
        
        if destination is None:                     # Serialization on file
            return serialized_content
        elif isinstance(destination, str):          # Serialization based on filename
            with open(destination, "w") as f:
                f.write(serialized_content)
            
            return None
        else:                                       # Serialization based on file object
            destination.write(serialized_content)
            
            return None


    def parse(self, source=None, location=None, data=None, format="turtle", **kwargs):
        """
        Parse source and add the resulting triples to triplestore.

        The source is specified using one of `source`, `location` or `data`.

        Parameters:
            source: File-like object or file name.
            location: String with relative or absolute URL to source.
            data: String containing the data to be parsed.
            format: Needed if format can not be inferred from source.
            kwargs: Additional backend-specific parameters controlling
                the parsing.
        """

        content = ""

        if source is not None and isinstance(source, (io.IOBase, io.TextIOBase, io.BufferedIOBase, io.RawIOBase)) and format == "turtle":
            content = source.read()
        elif (source is not None and isinstance(source, str)) or (location is not None):
            to_parse = source if source is not None else location
            filename, file_extension = os.path.splitext(location)
            if file_extension != ".ttl":
                raise Exception("Only turtle format is supported")
            with open(to_parse, "r") as f:
                content = f.read()
        elif format == "turtle":
            content = data
        else:
            raise Exception("Error during argument checking\nOnly one among source, location and data must be provided\nOnly turtle format is supported")

        response = requests.post(
            "http://{}:{}/databases/{}".format(self.ip, self.port, self.db_name),
            files={"ontology": ("data.ttl", content)},
        )

        if response.status_code != 200:
            raise Exception("Error during database inserting")