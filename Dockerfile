FROM alpine:3.4


RUN apk add --no-cache python3 python3-dev postgresql-dev gcc musl-dev

# Bundle app source
COPY . /src/

# Install app dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r /src/requirements.txt


CMD ["python3", "/src/main.py"]
