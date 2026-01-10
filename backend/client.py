import requests
import time

def wait_for_server(url: str, timeout: int = 60):
    start_time = time.time()

    while True:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        if time.time() - start_time > timeout:
            print("Timeout waiting for server.")
            return False

        time.sleep(1)

import uuid

def main():
    base_url = "http://localhost:8000"
    print(f"Connecting to Obsidian Backend at {base_url}/chat")

    if not wait_for_server(base_url):
        print("Could not connect to server. Exiting.")
        return
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            # Send request to backend
            try:
                # Check for file command
                file_path = None
                message = user_input
                
                if user_input.startswith("/file:"):
                    parts = user_input.split(" ", 1)
                    file_part = parts[0]
                    file_path = file_part[len("/file:"):].strip()
                    
                    if len(parts) > 1:
                        message = parts[1]
                    else:
                        message = "Processed file."
                
                print("AI: ", end="", flush=True)
                with requests.post(
                    "http://localhost:8000/chat",
                    json={"message": message, "session_id": session_id, "file_path": file_path},
                    stream=True
                ) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            print(chunk, end="", flush=True)
                print() # Newline when finish generation
            except requests.exceptions.ConnectionError:
                print("Error: Could not connect to backend. Is the server running?")
            except requests.exceptions.HTTPError as e:
                print(f"Server Error: {e}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
