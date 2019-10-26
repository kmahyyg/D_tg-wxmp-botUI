FROM python:3.7-alpine
RUN apk add --no-cache build-base libffi-dev openssl-dev
COPY . /tmp/wxmpbot
RUN pip install -r /tmp/wxmpbot/requirements.txt

FROM python:3.7-alpine
RUN apk add --no-cache libstdc++ libffi openssl
WORKDIR /usr/local/wxmpbot
COPY --from=0 /tmp/wxmpbot/ /usr/local/wxmpbot
COPY --from=0 /usr/local/lib/python3.7/site-packages/ /usr/local/lib/python3.7/site-packages/
ENTRYPOINT [ "/usr/local/wxmpbot/main.py" ]
