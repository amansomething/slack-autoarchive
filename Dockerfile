FROM python:3
COPY requirements.txt main.py messages.py config.py /
RUN pip install -r requirements.txt
CMD [ "python", "./main.py" ]
