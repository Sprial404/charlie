# Charlie

This is a Python program for a Discord counting bot.

## Notice

Please note that this bot is a **personal project** and that support is not guaranteed. Feel free to fork the repository
and modify the code to suit your needs.

If you encounter any issues, you can open an issue on GitHub, and I will try to address it when I have time to do so.

You can also submit a pull request if you have a fix or an improvement that you would like to contribute, but I cannot
guarantee that it will be accepted.

## Features

- Users can count numbers in a Discord channel.
- Recognizes when a user counts two numbers in a row and resets the count.
- Automatically resets the count if a user makes a mistake.
- Records the highest count achieved by users.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Sprial404/charlie.git
    ```

2. Install the dependencies using pip:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Make sure you have Python 3.12 installed.

2. Create a `.env` file in the root directory of the project with the following content:

    ```plaintext
    TOKEN=your-discord-bot-token
    CHANNEL_ID=your-discord-counting-channel-id
    ```

   Replace `your-discord-bot-token` with your actual Discord bot token and `your-discord-counting-channel-id` with the
   ID of the Discord channel where you want the bot to operate.

   To get the channel ID, enable Developer Mode in Discord settings, right-click on the channel, and select "Copy ID".

3. Run the program using the following command:

    ```bash
    python -m charlie.bot
    ```

## Deployment with Docker

1. Install Docker and Docker Compose.

2. Create a `docker-compose.yml` file with the following content:

    ```yaml
    version: '3'
    services:
        bot:
            build: .
            volumes:
                - ./data:/app/data
            environment:
                - TOKEN=your-discord-bot-token
                - CHANNEL_ID=your-discord-counting-channel-id
    ```

3. Replace `your-discord-bot-token` with your actual Discord bot token and `your-discord-counting-channel-id` with the
   ID of the Discord channel where you want the bot to operate.

   To get the channel ID, enable Developer Mode in Discord settings, right-click on the channel, and select "Copy ID".

4. Run the following command to start the bot using Docker Compose:

    ```bash
    docker-compose up -d
    ```

5. The bot will be running inside a Docker container. The `data` directory will be mounted as a volume, allowing you to
   persist data across container restarts.

### Using a Named Volume

If you prefer to use a named volume instead of a bind mount, you can modify the `volumes` section in
the `docker-compose.yml` file as follows:

```yaml
volumes:
  data:
```

Then, replace the `volumes` section in the `bot` service with the following:

```yaml
volumes:
  - data:/app/data
```