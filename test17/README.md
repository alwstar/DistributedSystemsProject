# P2P Chat Application

This is a peer-to-peer chat application with leader election functionality.

## Usage

To run the server:
python main.py server -p 6000 -u 5000

To run the client:
python main.py client -u 5000

Use the following commands in the client:
- 'm': Send a message
- 'e': Start an election
- 'q': Quit the application

## Requirements

- Python 3.7+

## Files

- `main.py`: Entry point for both client and server
- `network.py`: Network operations for both client and server
- `election.py`: Election algorithm implementation
- `message.py`: Message creation, parsing, and types
- `config.py`: Configuration and argument parsing
- `logger.py`: Logging setup and configuration
- `client.py`: Client-specific functionality
- `server.py`: Server-specific functionality
- `ui.py`: User interface for client