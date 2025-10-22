# Use an official lightweight Python image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirement.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the application code
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Command to run the Streamlit app
# --server.address=0.0.0.0 makes it accessible outside the container
CMD ["streamlit", "run", "streamlit_app.py", "--client.showErrorDetails=false", "--server.address=0.0.0.0"]
