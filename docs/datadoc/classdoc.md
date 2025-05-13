Documenting abstract resources
------------------------------
Resources that do not exist are called *abstract resources*.
A typical example of an abstract resource is a procedure that has not been performed (yet), like a general description of a task in a workflow.

It is highly desirable to document such a resource as a class (i.e. in the TBox).
It is consistent with the physicalistic/nominalistic approach taken by major ontological frameworks for applied sciences and makes it easy to document actual executions of such a workflow task as an individual of this class.

```python
{
    "@id": "ex:MySimulation",
    "@type": "owl:Class",
    "subClassOf": "PhysicsBasedSimulation",
    "prefLabel": "MySimulation",
    "elucidation": "A simulation using my physics-based materials models.",
    "isParticipatedBy": {
        "@id": "ex:MyModel",
        "@type": "owl:Class"  # restrictionType defaults to some
    },
    "command": "mymodel infile.txt -o outfile.txt",  # Command to execute the model
    "workdir": ".",  # Relative path to working directory
    "environment": {"VAR1": "val1", "VAR2": "val2"},  # Environment variables (JSON-encoded)
    "install_command": "pip install git+ssh://git@github.com:MyProj/myrepo.git@master",
    "hasInput": [
        {
            "@id": "ex:MyInputDataset",
            "@type": "owl:Class",
            "subClassOf": ["dcat:Dataset", "emmo:Dataset"],
            "restrictionType": "exactly 1",  # defaults to "some"
            "prefLabel": "MyInputDataset.",
            "elucidation": "My input dataset.",
            "distribution": {
                "accessURL": "file:./infile.txt",
                "accessService": {
                    "conformsTo": "https://github.com/SINTEF/dlite/",
                    "generator": "ex:inputplugin"  # for generating input
                }
            }
        }
    ],
    "hasOutput": [
        {
            "@id": "ex:MyOutputDataset",
            "@type": "owl:Class",
            "subClassOf": ["dcat:Dataset", "emmo:Dataset"],
            "restrictionType": "exactly 1",  # defaults to "some"
            "prefLabel": "MyOutputDataset.",
            "elucidation": "My output dataset.",
            "distribution": {
                "accessURL": "file:./outfile.txt",
                "accessService": {
                    "conformsTo": "https://github.com/SINTEF/dlite/",
                    "parser": "ex:outputplugin",  # for parsing output
                    "generator": "ex:outputplugin"  # for storing output to external storage
                }
            }
        }
    ]
}
```
