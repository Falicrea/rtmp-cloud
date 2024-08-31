FROM python:3.10
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN addgroup --gid 1000 livesparkgp \
    && adduser --uid 1000 --gid 1000 --disabled-password livespark \
    && usermod -aG sudo livespark

USER livespark

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3030"]