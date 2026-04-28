FROM nextflow/nextflow:26.03.2-edge
WORKDIR /usr/src/compute
ENV PYTHONUNBUFFERED=1
COPY __init__.py .
COPY backend/ ./backend/
COPY network/ ./network/
COPY session ./session/
COPY shared ./shared/
COPY pyproject.toml .
COPY poetry.lock .
COPY docker ./docker/
RUN chmod +x ./docker/*
RUN ./docker/installEnv.sh
RUN ./docker/installDeps.sh
CMD ["./docker/runCompute.sh"]
EXPOSE 8000/tcp