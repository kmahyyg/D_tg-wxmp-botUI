FROM python:3.7-alpine
RUN apk add --no-cache build-base libffi-dev openssl-dev
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

FROM python:3.7-alpine
RUN apk add --no-cache libstdc++ libffi openssl
WORKDIR /usr/local/wxmpbot
COPY . /usr/local/wxmpbot/
COPY --from=0 /usr/local/lib/python3.7/site-packages/ /usr/local/lib/python3.7/site-packages/
ENTRYPOINT [ "/usr/local/wxmpbot/main.py" ]
