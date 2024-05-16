FROM python:3.10.0
WORKDIR /
COPY Pipfile Pipfile.lock requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "steam2buff"]
EXPOSE 5000
