"""AIG-Doggy CLI 入口点。"""

import uvicorn
from doggy.server.bootstrap import app, setup_app


def main():
    setup_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()