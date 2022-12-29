# start by pulling the python image
#FROM python:3.8-alpine
FROM python:3

#copy the json for GCP
COPY ./deshmukhr-cep.json /quoteapp/deshmukhr-cep.json

# copy the requirements file into the image
COPY ./requirements.txt /quoteapp/requirements.txt

# switch working directory
WORKDIR /quoteapp

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /quoteapp

# set environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/quoteapp/deshmukhr-cep.json

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["quoteapp.py" ]