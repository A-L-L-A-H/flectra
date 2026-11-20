
FROM python:3.11-slim-bookworm

# --------------------------------------------------
# Python environment
# --------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --------------------------------------------------
# System dependencies
# --------------------------------------------------

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
        python3-num2words \
        python3-pdfminer \
        python3-renderpm \
        python3-requests \
        postgresql-client \
        wget \
    && curl -fsSLo /tmp/wkhtmltox.deb \
        https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/wkhtmltox.deb

# --------------------------------------------------
# Create Flectra user
# --------------------------------------------------

RUN useradd \
    --create-home \
    --home-dir /opt/flectra \
    --shell /bin/bash \
    flectra

WORKDIR /opt/flectra

# --------------------------------------------------
# Copy Flectra source
# --------------------------------------------------

COPY --chown=flectra:flectra . /opt/flectra

# --------------------------------------------------
# Install Python dependencies
# --------------------------------------------------

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir .

# --------------------------------------------------
# Flectra configuration
# --------------------------------------------------

COPY --chown=flectra:flectra \
    ./debian/flectra.conf \
    /etc/flectra/flectra.conf

# --------------------------------------------------
# Flectra executable
# --------------------------------------------------

COPY --chown=flectra:flectra \
    ./setup/flectra \
    /usr/local/bin/flectra

# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

COPY --chown=flectra:flectra \
    ./entrypoint.sh \
    /entrypoint.sh

# --------------------------------------------------
# Runtime directories and permissions
# --------------------------------------------------

RUN sed -i 's/\r$//' /entrypoint.sh \
    && mkdir -p /var/lib/flectra /etc/flectra \
    && chown -R flectra:flectra \
        /var/lib/flectra \
        /etc/flectra \
    && chmod 0755 \
        /entrypoint.sh \
        /usr/local/bin/flectra

# --------------------------------------------------
# Network ports
# --------------------------------------------------

EXPOSE 8069 8072

# --------------------------------------------------
# Runtime user
# --------------------------------------------------

USER flectra

# --------------------------------------------------
# Entrypoint and default command
# --------------------------------------------------

# IMPORTANT: Explicitly execute using Bash.
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

CMD ["flectra"]
