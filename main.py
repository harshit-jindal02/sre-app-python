import os
import httpx
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Use Jinja2Templates for proper HTML rendering
templates = Jinja2Templates(directory="templates")

# Create a templates directory and an index.html file for this to work
# For simplicity here, we define it inline, but a separate file is best practice.
if not os.path.exists("templates"):
    os.makedirs("templates")

with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>CSV Upload</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; }
        .container { margin-top: 60px; max-width: 500px; }
        .spinner-border { display: none; }
    </style>
</head>
<body>
    <div class="container shadow p-4 bg-white rounded">
        <h2 class="mb-4 text-center">Upload CSV File</h2>
        {% if message %}
            <div class="alert alert-info" role="alert">
                {{ message }}
            </div>
        {% endif %}
        <form id="uploadForm" action="/" method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <input class="form-control" type="file" name="csvfile" accept=".csv" required onchange="updateFileName()">
                <div id="fileName" class="form-text"></div>
            </div>
            <button class="btn btn-primary w-100" type="submit">Upload</button>
            <div class="d-flex justify-content-center mt-3">
                <div class="spinner-border text-primary" role="status" id="spinner">
                  <span class="visually-hidden">Uploading...</span>
                </div>
            </div>
        </form>
    </div>
    <script>
        function updateFileName() {
            var input = document.querySelector('input[type="file"]');
            var fileNameDiv = document.getElementById('fileName');
            if (input.files.length > 0) {
                fileNameDiv.textContent = "Selected file: " + input.files[0].name;
            } else {
                fileNameDiv.textContent = "";
            }
        }
        document.getElementById('uploadForm').onsubmit = function() {
            document.getElementById('spinner').style.display = 'block';
        };
    </script>
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def upload_csv(request: Request, csvfile: UploadFile = File(...)):
    message = ""
    try:
        file_bytes = await csvfile.read()
        filename = csvfile.filename

        # Get Node.js service host and port from environment variables
        # These will be set by the Kubernetes deployment.yaml
        node_host = os.environ.get("NODE_SERVICE_HOST", "localhost")
        node_port = os.environ.get("NODE_SERVICE_PORT", "6000")
        url = f"http://{node_host}:{node_port}/receive"

        async with httpx.AsyncClient() as client:
            files = {'csvfile': (filename, file_bytes, 'text/csv')}
            response = await client.post(url, files=files)
            
            response.raise_for_status() # Raise an exception for bad status codes
            
            message = "File successfully processed and sent to Node.js service!"

    except httpx.HTTPStatusError as e:
        message = f"Failed to send file to Node.js service: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        message = f"An error occurred: {str(e)}"

    return templates.TemplateResponse("index.html", {"request": request, "message": message})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
