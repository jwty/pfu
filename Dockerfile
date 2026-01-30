FROM python:alpine
EXPOSE 8080
WORKDIR /pfu
COPY requirements.txt ./
RUN apk add --no-cache tzdata && \
    pip3 install -r requirements.txt
COPY pfu pfu
COPY run.py generate-credentials.py ./
CMD ["python3", "run.py"]
