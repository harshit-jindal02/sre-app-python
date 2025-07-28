from fastapi import FastAPI, Request, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import os

app = FastAPI()

# For simplicity, use inline HTML (or you can use Jinja2Templates if you prefer)
HTML = """
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
        <form id="uploadForm" method="post" enctype="multipart/form-data">
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
"""

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return HTML.replace("{% if message %}", "").replace("{% endif %}", "")

@app.post("/", response_class=HTMLResponse)
async def upload_csv(request: Request, csvfile: UploadFile = File(...)):
    message = ""
    try:
        file_bytes = await csvfile.read()
        filename = csvfile.filename

        # Get server name from environment variable
        server = os.environ.get("NODE_SERVER", "localhost")
        url = f"http://{server}:6000/receive"

        # Send file to Node.js server
        async with httpx.AsyncClient() as client:
            files = {'csvfile': (filename, file_bytes, 'text/csv')}
            response = await client.post(url, files=files)
            if response.status_code == 200:
                message = "File sent to Node.js server!"
            else:
                message = f"Failed to send file: {response.text}"
    except Exception as e:
        message = f"Error: {str(e)}"

    # Render HTML with message
    html_with_message = HTML.replace(
        "{% if message %}", ""
    ).replace(
        "{% endif %}", ""
    ).replace(
        "{{ message }}", message
    )
    return HTMLResponse(content=html_with_message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
