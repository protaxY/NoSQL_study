FROM python:3.11
WORKDIR /code
COPY ./ /code/
RUN pip install --no-cache-dir -r /code/requirements.txt
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]
