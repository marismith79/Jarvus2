
---
# Jarvus Flask Application

Awesome jarvus2 created by marismith79

## Installation

From source:

```bash
git clone https://github.com/marismith79/Jarvus2 jarvus
cd jarvus
make virtualenv
source .venv/bin/activate
make install
```


## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ jarvus
```

or

```bash
$ python -m jarvus
```

To see the help message and usage instructions.

## First run

```bash
jarvus create-db   # run once
jarvus populate-db  # run once (optional)
jarvus add-user -u admin -p 1234  # ads a user
jarvus run
```

Go to:

- Website: http://localhost:5001
- Admin: http://localhost:5001/admin/
  - user: admin, senha: 1234
- API GET:
  - http://localhost:5001/api/v1/product/
  - http://localhost:5001/api/v1/product/1
  - http://localhost:5001/api/v1/product/2
  - http://localhost:5001/api/v1/product/3


> **Note**: You can do `flask run --port=5001` to run the application. 
> **Note**: You can also do `python run_dev.py` to run the application with automatic rendering.