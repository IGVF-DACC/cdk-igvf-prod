FROM public.ecr.aws/docker/library/python:3.11.4-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

ENV VIRTUAL_ENV=/opt/venv

ARG VERSION=v2.7.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m ift

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN chown -R ift:ift $VIRTUAL_ENV

WORKDIR /ift

RUN git clone -b ${VERSION} --depth 1 https://github.com/IGVF-DACC/igvf-file-transfer .

RUN pip install -e .

RUN pip install -r requirements.txt

COPY --chown=ift:ift . .

RUN chmod +x *.sh

USER ift

ENTRYPOINT ["./entrypoint.sh"]

CMD ["./run-sync.sh"]
