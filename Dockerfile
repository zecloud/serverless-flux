# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.10-appservice
#FROM mcr.microsoft.com/azure-functions/python:4-python3.10
FROM zecloud.azurecr.io/diffazfunc@sha256:cbd5dac8af4f4c0794e37c62af05dec9d38cd91f772e242b1868ba0e6f1d9e19

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot