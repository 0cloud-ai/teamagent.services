import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="teamagent.services")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=3000, help="Bind port (default: 3000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run("teamagent.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
