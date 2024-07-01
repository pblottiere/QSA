FROM qgis/qgis:ltr-noble

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends --no-install-suggests -y \
    python3-dev \
    virtualenv \
    qgis \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /qsa
ADD ./ ./
RUN rm -rf venv \
	&& virtualenv -p /usr/bin/python3 venv \
    && . venv/bin/activate \
    && pip install poetry \
    && poetry install

ENV PATH=/qsa/venv/bin:$PATH
ENV PYTHONPATH=/usr/lib/python3/dist-packages/:$PYTHONPATH
WORKDIR /tmp
ENTRYPOINT ["qsa"]