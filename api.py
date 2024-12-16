from app.api import app
import uvicorn
from argparse import ArgumentParser
from fastapi.middleware.cors import CORSMiddleware

if __name__ != "__main__":
    raise Exception("This script should not be imported")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


parser = ArgumentParser()

parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")

args = parser.parse_args()

# run
uvicorn.run(app, host=args.host, port=args.port)