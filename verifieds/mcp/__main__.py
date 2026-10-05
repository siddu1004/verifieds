from verifieds.mcp.server import mcp_server


def main() -> None:
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
