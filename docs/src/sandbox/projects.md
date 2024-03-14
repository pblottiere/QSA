# Sandbox : manage projects

### Create and delete projects

To create a project:

```` shell
$ curl "http://localhost:5000/api/projects/" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{
        "name":"my_project",
        "author":"pblottiere"
    }'
true
````

In this case, a project has been created on the filesystem:

```` shell
$ file projects/qgis/my_project/my_project.qgs
QGIS XML document
````

To create another project and list available projects:

```` shell
$ curl "http://localhost:5000/api/projects/" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{
        "name":"my_project_2",
        "author":"pblottiere"
    }'
true
$ curl "http://localhost:5000/api/projects/"
["my_project_2","my_project"]
````

To delete a project:

```` shell
$ curl -X DELETE "http://localhost:5000/api/projects/my_project_2"
true
$ curl "http://localhost:5000/api/projects/"
["my_project"]
````

To list project metadata:

```` shell
$ curl http://localhost:5000/api/projects/my_project | jq
{
  "author": "pblottiere",
  "creation_datetime": "2024-03-14T20:17:45",
  "crs": ""
}
````
