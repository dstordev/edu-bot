FROM python:3.14.6
WORKDIR /app

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh
# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin:$PATH"
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

RUN uv sync --frozen
ENV PYTHONPATH /app/src
CMD ["uv", "run", "src/"]
