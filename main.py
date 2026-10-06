from datetime import datetime

from normalize import (
    extract_commands,
    save_latest,
    save_all
)

from execute import execute_commands


def main():

    print("=" * 50)
    print("JARVIS")
    print("=" * 50)

    while True:

        prompt = input(
            "\nEnter command: "
        ).strip()

        if prompt.lower() in [
            "exit",
            "quit"
        ]:

            print("Jarvis stopped.")

            break

        if not prompt:

            continue

        # ----------------------------
        # UNDERSTAND COMMAND
        # ----------------------------

        normalized, commands = (
            extract_commands(prompt)
        )

        print(
            "\nNormalized:",
            normalized
        )

        print(
            "\nCommands:"
        )

        for number, command in enumerate(
            commands,
            1
        ):

            print(
                number,
                command
            )

        # ----------------------------
        # HISTORY RECORD
        # ----------------------------

        record = {

            "timestamp":
                datetime.now().isoformat(
                    timespec="seconds"
                ),

            "original":
                prompt,

            "normalized":
                normalized,

            "commands":
                commands
        }

        save_latest(record)

        save_all(record)

        # ----------------------------
        # EXECUTE
        # ----------------------------

        execute_commands(commands)


if __name__ == "__main__":

    main()