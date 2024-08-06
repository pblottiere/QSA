FROM qgis/qgis:release-3_34

RUN apt-get update \
    && apt-get upgrade -y \
    virtualenv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /qsa
ADD qsa-api/pyproject.toml .

RUN rm -rf venv \
    && virtualenv --system-site-packages -p /usr/bin/python3 venv \
    && . venv/bin/activate \
    && pip install poetry \
    && pip install gunicorn \
    && poetry install

ADD qsa-api/qsa_api /qsa/qsa_api
ENV PATH=/qsa/venv/bin:$PATH
EXPOSE 5000
CMD ["gunicorn"  , "-b", "0.0.0.0:5000", "--workers", "1", "--threads", "1", "qsa_api.app:app"]
