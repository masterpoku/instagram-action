import requests
import time

def getdata(api_url):
    try:
        # Send GET request
        response = requests.get(api_url)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            # Parse and return the response JSON data
            return response.json()
        else:
            # If the request was not successful, return the status code and reason
            return {"error": response.status_code, "message": response.reason}
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        return {"error": "Request failed", "message": str(e)}

# API URL
api_url = "https://e33b-36-71-171-112.ngrok-free.app/slt/api.php?function=getLikerWithStatusZero&func=count"

# Variable to store ID
last_id = None

# Continuous loop
while True:
    print("Fetching data from API")
    result = getdata(api_url)
    
    # Check for errors or empty data
    if 'error' in result or not result or 'id' not in result:
        print("No data loaded or error encountered. Skipping initial loop.")
        print("done")
        time.sleep(10)  # Wait for 10 seconds before retrying
        continue  # Continue to the next iteration of the loop
    
    print(result)
    
    # Perform 10 iterations if data is valid
    for i in range(10):
        print(f"Request {i + 1}: Fetching data from API")
        result = getdata(api_url)
        
        # Check for errors or empty data during the 10 iterations
        if 'error' in result or not result or 'id' not in result:
            print("No data loaded or error encountered during iterations.")
            print("done")
            continue  # Skip further iterations and retry
        
        print(result)
        
        # Store the ID from the result
        if 'id' in result:
            last_id = result['id']
        
        # Optional: delay between requests to avoid spamming the server (e.g., wait 1 second)
        time.sleep(1)  # Wait for 1 second before the next request

    # Check if last_id is valid before making the update request
    if last_id:
        api_update = f"https://e33b-36-71-171-112.ngrok-free.app/slt/api.php?function=getLikerWithStatusZero&func=update&id={last_id}"
        print("\nMaking the update request...")
        update_result = getdata(api_update)
        
        # Check for errors in the update result
        if 'error' in update_result or not update_result:
            print("Error encountered during update request or no data to update.")
        else:
            print(update_result)
        
        # Reset the last_id after update
        last_id = None
    
    # Optional: delay between iterations to avoid overwhelming the server
    time.sleep(10)  # Wait for 10 seconds before the next iteration
