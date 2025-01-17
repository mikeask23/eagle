# dolphin_anty_utils.py
import aiohttp

async def authorize_dolphin_anty(api_token):
    """Authorizes Dolphin Anty using the API token."""
    url = "http://localhost:3001/v1.0/auth/login-with-token"
    headers = {"Content-Type": "application/json"}
    data = {"token": api_token}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                print("Dolphin Anty authorized successfully.")
                return True
            else:
                print(f"Authorization failed: {response.status} - {await response.text()}")
                return False

async def launch_profile(profile_id):
    """Launches a Dolphin Anty profile and returns the port and wsEndpoint."""
    url = f"http://localhost:3001/v1.0/browser_profiles/{profile_id}/start?automation=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("success"):
                    port = data["automation"]["port"]
                    ws_endpoint = data["automation"]["wsEndpoint"]
                    print(f"Profile launched: Port={port}, wsEndpoint={ws_endpoint}")
                    return port, ws_endpoint
                else:
                    print(f"Failed to launch profile: {data.get('msg')}")
                    return None, None
            else:
                print(f"Error launching profile: {response.status} - {await response.text()}")
                return None, None