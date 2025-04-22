# Flask Project Template

A full feature Flask project template.

See also 
- [Python-Project-Template](https://github.com/rochacbruno/python-project-template/) for a lean, low dependency Python app.
- [FastAPI-Project-Template](https://github.com/rochacbruno/fastapi-project-template/) The base to start an openapi project featuring: SQLModel, Typer, FastAPI, JWT Token Auth, Interactive Shell, Management Commands.

<!--  DELETE THE LINES ABOVE THIS AND WRITE YOUR PROJECT README BELOW -->

---
# jarvus2 Flask Application

Awesome jarvus2 created by marismith79

## Installation

From source:

```bash
git clone https://github.com/marismith79/Jarvus2 jarvus2
cd jarvus2
make install
```

From pypi:

```bash
pip install jarvus2
```

## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ jarvus2
```

or

```bash
$ python -m jarvus2
```

To see the help message and usage instructions.

## First run

```bash
jarvus2 create-db   # run once
jarvus2 populate-db  # run once (optional)
jarvus2 add-user -u admin -p 1234  # ads a user
jarvus2 run
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
