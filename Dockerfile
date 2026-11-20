FROM python:3.11-slim

# Flectra (Odoo fork) server image.
# Matches the officially supported distro set in requirements.txt (Debian 11 / Ubuntu 22.04).

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# System deps: build tools + runtime libs required by python packages and wkhtmltopdf.
RUN apt-get update && apt-get install -y --no-install-recommends \
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
        python3-pip \
        python3-num2words \
        python3-pdfminer \
        python3-renderpm \
        python3-requests \
        postgresql-client \
        wget \
    && curl -o wkhtmltox.deb -sSL \
        https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Add Flectra user
RUN useradd --create-home --home-dir /opt/flectra --shell /bin/bash flectra

WORKDIR /opt/flectra

COPY --chown=flectra:flectra . /opt/flectra

# Install flectra (this pulls requirements.txt via setup.py)
RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir .

# Copy entrypoint and default config
COPY --chown=flectra:flectra ./debian/flectra.conf /etc/flectra/flectra.conf
COPY --chown=flectra:flectra ./setup/flectra /usr/local/bin/flectra
COPY --chown=flectra:flectra ./entrypoint.sh /entrypoint.sh

# Mount /var/lib/flectra to allow restoring filestore and sessions
RUN mkdir -p /var/lib/flectra \
    && chown -R flectra:flectra /var/lib/flectra /etc/flectra \
    && chmod +x /entrypoint.sh /usr/local/bin/flectra

# Expose flectra services
EXPOSE 8069 8072

ENV HOST=db \
    PORT=5432 \
    USER=flectra \
    PASSWORD=flectra \
    DB=postgres

USER flectra

ENTRYPOINT ["/entrypoint.sh"]
CMD ["flectra"]