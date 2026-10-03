# Sandbox image for running model-generated code against the hidden tests.
# Network is only used here, at build time; checks run with --network none.
# python:3.12-slim (Python 3.12.15), pinned by digest:
FROM python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
RUN pip install --no-cache-dir \
      pytest==9.1.1 pytest-timeout==2.4.0 \
      iniconfig==2.3.0 packaging==26.3 pluggy==1.6.0 Pygments==2.21.0 \
 && pip freeze > /pip-freeze.txt
COPY harness.py /harness/harness.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "/harness/harness.py"]
