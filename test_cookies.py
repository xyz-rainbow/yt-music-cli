import json
from ytmusicapi import YTMusic
import sys

cookies = """YSC=qKnrfiAWew8; LOGIN_INFO=AFmmF2swRgIhAP7BxRce9LGeDzx0hfzXeXeTqemJLj_s8eLtoNv7Q9X4AiEA2iabZbtff6Yb9ZeMcdSOUC8sRPyFT3QuNN_QA57pNXI:QUQ3MjNmd2FQR1pwRDZXWVF3Vjg2S1VLS0JHc3JOZWNSMXV6MkpZaHNqSDRPM3hScWpWSlVfcEg1cTl4Mkp2RmRkQU85WkEwMERMajh2SXYyVHBSSDlrTWdnNjBDR3A4THVsek9DY3VTNXdLMVJldjJvZVh6UzRaekFMNVp3c29ZbkE0MzJSNGhUbHVhUXR3VEpEM0JYQW9nNl80NXluQm1B; HSID=AOR63LWiJbQctOITt; SSID=AUppE3sPHEuNGlCf7; APISID=2DeTlmQf5yXkXg4i/A-CkTpWnTl-BxR8dP; SAPISID=4eQ54PVIOIMJAAt9/AEHbbPFieyAr6RhL6; __Secure-1PAPISID=4eQ54PVIOIMJAAt9/AEHbbPFieyAr6RhL6; __Secure-3PAPISID=4eQ54PVIOIMJAAt9/AEHbbPFieyAr6RhL6; SID=g.a0006ghyQTiwykdtVdancP04teLUBNTc43u9prraCbGuU7PVNiLUShNwE9LLiI0LKE6bce9OmQACgYKAXESARUSFQHGX2Mivnptw6kQ0Gj4fm1X2WO1xxoVAUF8yKqAALz6M6IytC7VQZ68PLOy0076; __Secure-1PSID=g.a0006ghyQTiwykdtVdancP04teLUBNTc43u9prraCbGuU7PVNiLUT63dwtTPSj-OFv8jCL4RdwACgYKAdQSARUSFQHGX2MiBSTJQJq_5qro34eniklGWxoVAUF8yKooJOg4wqwdIxolO8KiiJ970076; __Secure-3PSID=g.a0006ghyQTiwykdtVdancP04teLUBNTc43u9prraCbGuU7PVNiLUgdKWxkhtHPWzjcNXPL7shwACgYKASgSARUSFQHGX2MisqodWLluRVAXHGBfye_9BhoVAUF8yKoXU4R4elRgYTpLsGOJiZHO0076; __Secure-ROLLOUT_TOKEN=CKrynp2riJvoRhCZrt6Pm8-SAxjD-OP08dGSAw%3D%3D; wide=1; PREF=f6=40000000&tz=Atlantic.Canary&f7=100&repeat=NONE&volume=34; __Secure-1PSIDTS=sidts-CjMB7I_69IxW8CVVnj1iJwqKz0lLCcsCcXnh50f9TH0qA6A9KMSSDg6rAUj3wQozy3nOfeUQAA; __Secure-3PSIDTS=sidts-CjMB7I_69IxW8CVVnj1iJwqKz0lLCcsCcXnh50f9TH0qA6A9KMSSDg6rAUj3wQozy3nOfeUQAA; VISITOR_PRIVACY_METADATA=CgJFUxIhEh0SGwsMDg8QERITFBUWFxgZGhscHR4fICEiIyQlJiA_; __Secure-YEC=CgtZbEdlZmZRZWJfMCiG4bXMBjInCgJFUxIhEh0SGwsMDg8QERITFBUWFxgZGhscHR4fICEiIyQlJiA_; SIDCC=AKEyXzVs7NR5vdeBrXuNyQjAd6_wqlipEC0BjLbgOXZcpLSXPyGNPH5xr0zAC7vlo9NYlrm4nA; __Secure-1PSIDCC=AKEyXzVw0YpzhAHTA8rGEGMOPdVqo1G-C9LzP8l16Hkp7gb-vZug40E11CLcps5u91NHYtyMUA; __Secure-3PSIDCC=AKEyXzUGo6NBKsf09dRvT7zAFtHAZ_1PZQdcSgH7Ll_df2BJF1BSMILtI_L7IIm1iDV8WpmkhQ"""

def test_login():
    auth_dict = {
        "Cookie": cookies,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print("Testing cookies...")
        yt = YTMusic(auth=json.dumps(auth_dict))
        playlists = yt.get_library_playlists(limit=1)
        print(f"Success! Found {len(playlists)} playlists.")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    if test_login():
        sys.exit(0)
    else:
        sys.exit(1)
