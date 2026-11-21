FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Build-time compilers and header packages for Python C-extension wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libldap2-dev \
        libpq-dev \
        libsasl2-dev \
        libssl-dev \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip wheel \
    && python -m pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

COPY setup.py setup.cfg MANIFEST.in LICENSE README.md ./
COPY flectra ./flectra
COPY setup ./setup
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir=/wheels .


FROM python:3.11-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="MoonWitness" \
      org.opencontainers.image.description="MoonWitness ERP distribution powered by Flectra 3.0" \
      org.opencontainers.image.source="https://github.com/A-L-L-A-H/flectra" \
      org.opencontainers.image.licenses="LGPL-3"

# Flectra runtime and Python defaults.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/opt/flectra

# Runtime-only system libraries, PostgreSQL client, wkhtmltopdf, and CJK fonts.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        fonts-noto-cjk \
        libffi8 \
        libfreetype6 \
        libjpeg62-turbo \
        liblcms2-2 \
        libldap-2.5-0 \
        libmagic1 \
        libopenjp2-7 \
        libpq5 \
        libsasl2-2 \
        libssl3 \
        libtiff6 \
        libwebp7 \
        libx11-6 \
        libxcb1 \
        libxext6 \
        libxkbcommon0 \
        libxrender1 \
        libxml2 \
        libxslt1.1 \
        node-less \
        postgresql-client \
        zlib1g \
    && arch="$(dpkg --print-architecture)" \
    && curl -fsSLo /tmp/wkhtmltox.deb \
        "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_${arch}.deb" \
    && apt-get install -y --no-install-recommends /tmp/wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/wkhtmltox.deb

# Run the server as an unprivileged user.
RUN useradd \
    --create-home \
    --home-dir /opt/flectra \
    --shell /bin/bash \
    flectra

# Install prebuilt wheels without compilers or build headers.
COPY --from=builder /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
    && python -m pip install --no-cache-dir --no-index --no-deps --find-links=/wheels flectra \
    && rm -rf /wheels /tmp/requirements.txt

WORKDIR /opt/flectra

# Copy the Flectra source tree (the Docker build context is filtered by .dockerignore).
COPY --chown=flectra:flectra . /opt/flectra

# Install the packaged server configuration and executable wrapper.
COPY --chown=flectra:flectra ./debian/flectra.conf /etc/flectra/flectra.conf
COPY --chown=flectra:flectra ./setup/flectra /usr/local/bin/flectra
COPY --chown=flectra:flectra ./entrypoint.sh /entrypoint.sh

# Persistent and runtime directories must be writable by the flectra user.
RUN sed -i 's/\r$//' /entrypoint.sh /usr/local/bin/flectra \
    && mkdir -p /var/lib/flectra /etc/flectra /opt/flectra/custom-addons \
    && chown -R flectra:flectra /var/lib/flectra /etc/flectra /opt/flectra/custom-addons \
    && chmod 0755 /entrypoint.sh /usr/local/bin/flectra

EXPOSE 8069 8072

USER flectra

# Use Bash explicitly. The entrypoint also detects accidental /bin/sh invocation.
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["flectra"]
