FROM python:alpine
EXPOSE 8080
WORKDIR /pfu
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY pfu pfu
COPY run.py gensecretkey.py ./
CMD ["python3", "run.py"]
