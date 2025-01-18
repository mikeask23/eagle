# dolphin_anty_utils.py
import aiohttp
import asyncio

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

async def stop_profile(profile_id):
    """Stops a running Dolphin Anty profile."""
    url = f"http://localhost:3001/v1.0/browser_profiles/{profile_id}/stop"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("success"):
                    print(f"Profile {profile_id} stopped successfully.")
                    # Wait for the profile to fully stop
                    await asyncio.sleep(5)
                    return True
                else:
                    print(f"Failed to stop profile: {data.get('msg')}")
                    return False
            else:
                print(f"Error stopping profile: {response.status} - {await response.text()}")
                return False

async def launch_profile(profile_id, max_retries=3):
    """Launches a Dolphin Anty profile and returns the port and wsEndpoint."""
    # First try to stop any running instance
    await stop_profile(profile_id)
    
    for attempt in range(max_retries):
        try:
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
                            error_msg = data.get("msg", "Unknown error")
                            if "already running" in error_msg.lower():
                                print(f"Profile {profile_id} is still running, stopping and waiting...")
                                await stop_profile(profile_id)
                                await asyncio.sleep(10)  # Wait longer between retries
                            else:
                                print(f"Failed to launch profile: {error_msg}")
                                return None, None
                    else:
                        print(f"Error launching profile: {response.status} - {await response.text()}")
                        return None, None
        except Exception as e:
            print(f"Error during launch attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
            else:
                return None, None
    
    print(f"Failed to launch profile after {max_retries} attempts")
    return None, None