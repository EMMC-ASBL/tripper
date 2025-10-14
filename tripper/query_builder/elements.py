"""
SPARQL query element classes

These classes represent different SPARQL query patterns and constructs
(triple patterns, OPTIONAL blocks, UNION blocks, etc.)
"""

from typing import List, Optional, Union

from .formatter import (
    format_subject,
    format_predicate,
    format_object,
    sanitize_variable,
    sanitize_uri,
)


class SPARQLElement:
    """Base class for SPARQL query elements"""

    def to_sparql(self, indent: int = 2) -> str:
        """Convert element to SPARQL string"""
        raise NotImplementedError


class TripleElement(SPARQLElement):
    """Represents a single triple pattern"""

    _anon_counter = 0  # Class-level counter for anonymous variables

    def __init__(self, subject: Union[str, None], predicate: Union[str, None],
                 obj: Union[str, int, float, bool, None],
                 datatype: Optional[str] = None, lang: Optional[str] = None):
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.datatype = datatype
        self.lang = lang
        self._anon_vars = {}

    def _format_subject(self, term: Union[str, None]) -> str:
        """Format a subject term (can be URI, variable, or blank node)

        Handles None for anonymous variables, then delegates to format_subject().
        """
        # None represents an anonymous variable
        if term is None:
            key = ('subject', id(self))
            if key not in self._anon_vars:
                TripleElement._anon_counter += 1
                self._anon_vars[key] = f"?anon{TripleElement._anon_counter}"
            return self._anon_vars[key]

        # Delegate to formatter function for all other cases
        return format_subject(term)

    def _format_predicate(self, term: Union[str, None]) -> str:
        """Format a predicate term (can be URI, variable, property path, or 'a')

        Handles None for anonymous variables, then delegates to format_predicate().
        """
        # None represents an anonymous variable
        if term is None:
            key = ('predicate', id(self))
            if key not in self._anon_vars:
                TripleElement._anon_counter += 1
                self._anon_vars[key] = f"?anon{TripleElement._anon_counter}"
            return self._anon_vars[key]

        # Delegate to formatter function for all other cases
        return format_predicate(term)

    def _format_object(self, term: Union[str, int, float, bool, None],
                       datatype: Optional[str] = None,
                       lang: Optional[str] = None) -> str:
        """Format an object term (can be URI, variable, or literal)

        Handles None for anonymous variables, then delegates to format_object().
        """
        # None represents an anonymous variable
        if term is None:
            key = ('object', id(self), datatype, lang)
            if key not in self._anon_vars:
                TripleElement._anon_counter += 1
                self._anon_vars[key] = f"?anon{TripleElement._anon_counter}"
            return self._anon_vars[key]

        # Delegate to formatter function for all other cases
        return format_object(term, datatype, lang)

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL triple pattern"""
        subj_str = self._format_subject(self.subject)
        pred_str = self._format_predicate(self.predicate)
        obj_str = self._format_object(self.obj, datatype=self.datatype, lang=self.lang)

        return f"{' ' * indent}{subj_str} {pred_str} {obj_str} ."


class OptionalBlock(SPARQLElement):
    """Represents an OPTIONAL block"""

    def __init__(self, patterns: List[SPARQLElement]):
        self.patterns = patterns

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL OPTIONAL block"""
        lines = [f"{' ' * indent}OPTIONAL {{"]
        for pattern in self.patterns:
            lines.append(pattern.to_sparql(indent + 2))
        lines.append(f"{' ' * indent}}}")
        return "\n".join(lines)


class UnionBlock(SPARQLElement):
    """Represents a UNION block"""

    def __init__(self, pattern_groups: List[List[SPARQLElement]]):
        self.pattern_groups = pattern_groups

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL UNION"""
        union_parts = []
        for i, group in enumerate(self.pattern_groups):
            if i > 0:
                union_parts.append(f"{' ' * indent}UNION")
            union_parts.append(f"{' ' * indent}{{")
            for pattern in group:
                union_parts.append(pattern.to_sparql(indent + 2))
            union_parts.append(f"{' ' * indent}}}")
        return "\n".join(union_parts)


class MinusBlock(SPARQLElement):
    """Represents a MINUS block"""

    def __init__(self, patterns: List[SPARQLElement]):
        self.patterns = patterns

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL MINUS block"""
        lines = [f"{' ' * indent}MINUS {{"]
        for pattern in self.patterns:
            lines.append(pattern.to_sparql(indent + 2))
        lines.append(f"{' ' * indent}}}")
        return "\n".join(lines)


class FilterElement(SPARQLElement):
    """Represents a FILTER condition"""

    def __init__(self, condition: str):
        self.condition = condition

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL FILTER"""
        return f"{' ' * indent}FILTER ({self.condition})"


class GraphBlock(SPARQLElement):
    """Represents a GRAPH block for named graphs"""

    def __init__(self, graph_uri: Union[str, None], patterns: List[SPARQLElement]):
        self.graph_uri = graph_uri
        self.patterns = patterns

    def to_sparql(self, indent: int = 2) -> str:
        """Convert to SPARQL GRAPH block"""
        if self.graph_uri:
            if self.graph_uri.startswith('?'):
                graph_ref = sanitize_variable(self.graph_uri)
            else:
                graph_ref = f"<{sanitize_uri(self.graph_uri)}>"
            lines = [f"{' ' * indent}GRAPH {graph_ref} {{"]
        else:
            lines = [f"{' ' * indent}{{"]

        for pattern in self.patterns:
            lines.append(pattern.to_sparql(indent + 2))
        lines.append(f"{' ' * indent}}}")
        return "\n".join(lines)
