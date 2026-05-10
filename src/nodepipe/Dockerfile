FROM docker:dind
WORKDIR /usr/src/compute
ENV PYTHONUNBUFFERED=1
COPY backend/ ./backend/
COPY network/ ./network/
COPY session ./session/
COPY shared ./shared/
COPY docker ./docker/
RUN mv ./docker/poetry.lock_container ./poetry.lock
RUN mv ./docker/pyproject.toml_container ./pyproject.toml
RUN chmod +x ./docker/*
RUN ./docker/installEnv.sh
RUN ./docker/installDeps.sh
CMD ["./docker/runCompute.sh"]
EXPOSE 8000/tcp