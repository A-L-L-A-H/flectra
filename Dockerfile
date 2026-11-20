FROM python:3.11-slim-bookworm

# Flectra runtime and Python defaults.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/opt/flectra

# System dependencies required by Flectra and Python wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        dirmngr \
        fonts-noto-cjk \
        gnupg \
        libldap2-dev \
        libpq-dev \
        libsasl2-dev \
        libxml2 \
        libxslt1-dev \
        libffi-dev \
        libjpeg62-turbo \
        libfreetype6 \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxcb1 \
        libxkbcommon0 \
        libssl-dev \
        build-essential \
        gcc \
        node-less \
        npm \
        postgresql-client \
        wget \
    && curl -fsSLo /tmp/wkhtmltox.deb \
        https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/wkhtmltox.deb

# Run the server as an unprivileged user.
RUN useradd \
    --create-home \
    --home-dir /opt/flectra \
    --shell /bin/bash \
    flectra

WORKDIR /opt/flectra

# Copy the Flectra source tree (the Docker build context is filtered by .dockerignore).
COPY --chown=flectra:flectra . /opt/flectra

# Install Flectra and its pinned Python dependencies.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir .

# Install the packaged server configuration and executable wrapper.
COPY --chown=flectra:flectra ./debian/flectra.conf /etc/flectra/flectra.conf
COPY --chown=flectra:flectra ./setup/flectra /usr/local/bin/flectra
COPY --chown=flectra:flectra ./entrypoint.sh /entrypoint.sh

# Persistent and runtime directories must be writable by the flectra user.
RUN sed -i 's/\r$//' /entrypoint.sh \
    && mkdir -p /var/lib/flectra /etc/flectra /opt/flectra/custom-addons \
    && chown -R flectra:flectra /var/lib/flectra /etc/flectra /opt/flectra/custom-addons \
    && chmod 0755 /entrypoint.sh /usr/local/bin/flectra

EXPOSE 8069 8072

USER flectra

# Use Bash explicitly. The entrypoint also detects accidental /bin/sh invocation.
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["flectra"]
