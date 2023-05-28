FROM python:3.11.3-slim
COPY requirements.txt main.py messages.py config.py /
RUN pip install -r requirements.txt
CMD [ "python", "./main.py" ]
