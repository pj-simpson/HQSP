
# HQSP

HQSP is a Python web-framework for Legal Technologists to rapidly prototype integrations with 
their chosen legal tech platform*. It provides many '_magicals_' to abstract away the more _tricky_
parts of consuming  an external service, allowing it's users to easily surface data from the
3rd party system in web pages which they've authored. 

## Influence

There are many tutorials out there where you can learn to build your own WSGI Server/ Web Framework, but the most influential,
in terms of this project, has been [Jahongir Rahmonov's](http://rahmonov.me/posts/write-python-framework-part-one/).

## Example

Here is a simple app which consumes the REST API of Virtual Data Room provider, 
getting the metadata pertaining to a specific VDR. 

```python
# demo.py

from hqsp import Application
import requests as http_handler

app = Application()

@app.set_headers
def dataroom_detail(headers, base_url, request, response, vdr_id):

    external_response = http_handler.get(
        f"{base_url}/api/1/dataroom/{vdr_id}", headers=headers
    )

    response.body = app.template("VDR.html", context=external_response.json())



app.add_routes({"/site/{vdr_id}": dataroom_detail})
```
The whole example program is structured like so:

```bash
static
|--css
   |--frontend-framework.min.css
|--js
   |--frontend-framework.min.css

templates
|—sites.html

demo.py
```

To run the above application locally, a WSGI server is used, like so:

```bash
gunicorn demo:app
```

## Features

* WSGI compliant (courtsey [WebOb](https://webob.org/))
* Function based controllers
* Route declaration in a single method call
* Path parameters
* Decorators to pass headers object to function controllers
* Token management entirely taken care of by the framework
* [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/) templates
* [Whienoise](http://whitenoise.evans.io/en/stable/) static file management

## Note

This is incredibly rough and ready as it is, _in effect_, a POC for a framework to build POCs. I do not advise using it.
Python Web Frameworks are plentiful and essentially represent a problem already solved,
however, I have found learning how to build one a valuable exercise in and of itself. 
I hope that the notion of a framework for non developers wanting to leverage a particular API, is clear.
I will undoubtedly use this code as a foundation for another web framework in the future. 

***HQSP was built with a particular legal tech vendor in mind**, but I have obfuscated who exactly that is. The 'auth' 
part of the framework was made to work for their particular authentication 'flow'. The repository could
easily be forked and that part of the code ripped out and/or re-written for a different system. 
