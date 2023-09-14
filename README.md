# Turn ChatGPT Integration

## Description:

This application serves as an integration layer between the Turn UI interface and any of OpenAI's chat completion models (defaulting to GPT-3.5-turbo). The main functionality is to transform incoming messages from Turn UI and get the model's suggested responses which are then returned as structured replies.

## Setup:

1. **Environment Variables**: Ensure you have the following environment variables set:

   - `OPENAI_API_KEY`: Your OpenAI API Key
   - `SYSTEM_PROMPT`: The initial system prompt for the ChatGPT model (default is a health-oriented prompt).
   - `MODEL`: The OpenAI model being used (default is "gpt-3.5-turbo").
   - `NUMBER_OF_MESSAGES_FOR_CONTEXT`: Number of most recent inbound and outbound messages considered for context (default is 4, maximum value is 10).
   - `CHATGPT_TIMEOUT`: Timeout for OpenAI API calls in seconds (default is 10 seconds).
   - `PORT`: The port on which the application runs (default is 8080).

2. Install necessary packages:

   ```
   python -m pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

The application will now be running, awaiting incoming HTTP requests on the specified port.

## Endpoints:

1. **`/`**: A simple endpoint that informs users about the primary endpoint for integration.

2. **`/integration` (POST)**: The main integration point where incoming messages from Turn UI are transformed and fed to the ChatGPT model for suggested responses.

## Note:

Always keep your `OPENAI_API_KEY` confidential. Avoid hardcoding or exposing it in any public repositories.
