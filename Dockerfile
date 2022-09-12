# TODO: Health checks
FROM python:alpine
WORKDIR /pfu-workdir
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
ENV PFU_UPLOAD_DIR='/uploads' \
	PFU_FILE_URL_PREFIX='files/' \
	PFU_DATABASE='/data/database.db' \
	PFU_CHUNK_SIZE=4194304 \
	PFU_SECRET_KEY=secret \
	PFU_AUTH_SECRET='pbkdf2:sha256:260000$HGnxHKS9Ffbe8K3l$e003b7963e4cf49d4e075087a55e90c85345754306a35fc2d9c571c31f19c393'
EXPOSE 8080
COPY . .
CMD ["python3", "run.py"]