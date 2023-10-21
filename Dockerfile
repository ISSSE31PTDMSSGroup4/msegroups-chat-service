# Use an official Python runtime as the parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
# Note: .dockerignore will prevent copying unwanted files/folders
COPY . /app
COPY .env .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5005 available to the world outside this container 
EXPOSE 5005

# Define environment variable (optional, for any environment variables your app uses)
# ENV NAME=Value

# Run app.py when the container launches, with custom attributes if needed
CMD ["python", "./app.py"]
