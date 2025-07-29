import os
import sys


sys.path.append(os.path.dirname(__file__))

from app import create_app

app = create_app()


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
