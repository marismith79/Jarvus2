# Flask Project Template

A full feature Flask project template.

See also 
- [Python-Project-Template](https://github.com/rochacbruno/python-project-template/) for a lean, low dependency Python app.
- [FastAPI-Project-Template](https://github.com/rochacbruno/fastapi-project-template/) The base to start an openapi project featuring: SQLModel, Typer, FastAPI, JWT Token Auth, Interactive Shell, Management Commands.

<!--  DELETE THE LINES ABOVE THIS AND WRITE YOUR PROJECT README BELOW -->

---
# project_name Flask Application

project_description

## Installation

From source:

```bash
git clone https://github.com/author_name/project_urlname project_name
cd project_name
make install
```

From pypi:

```bash
pip install project_name
```

## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ project_name
```

or

```bash
$ python -m project_name
```

To see the help message and usage instructions.

## First run

```bash
project_name create-db   # run once
project_name populate-db  # run once (optional)
project_name add-user -u admin -p 1234  # ads a user
project_name run
```

Go to:

- Website: http://localhost:5000
- Admin: http://localhost:5000/admin/
  - user: admin, senha: 1234
- API GET:
  - http://localhost:5000/api/v1/product/
  - http://localhost:5000/api/v1/product/1
  - http://localhost:5000/api/v1/product/2
  - http://localhost:5000/api/v1/product/3


> **Note**: You can also use `flask run` to run the application.
