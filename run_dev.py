# development run script
#!/usr/bin/env python
from jarvus_app import create_app

def main():
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=True)

if __name__ == "__main__":
    main()