import os

from app_core import create_app

app = create_app()


def configure_runtime():
    os.environ.setdefault('OMP_NUM_THREADS', '20')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '20')


if __name__ == '__main__':
    configure_runtime()
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
