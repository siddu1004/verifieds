"""__main__ entrypoint for verifieds.adequacy."""


def main() -> None:
    from verifieds.adequacy.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
