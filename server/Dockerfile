FROM python:3.10
WORKDIR /code/app
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN usermod --non-unique --uid 1000 www-data \
    && groupmod --non-unique --gid 1000 www-data

USER www-data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3030"]