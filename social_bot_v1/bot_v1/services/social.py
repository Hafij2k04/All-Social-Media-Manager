"""V4+ : প্ল্যাটফর্ম ক্লায়েন্ট (এখন শুধু কাঠামো, কাজ নেই)।"""


class PlatformClient:
    name = "base"

    async def connect(self, *args, **kwargs):
        raise NotImplementedError

    async def upload_video(self, file_path, title, description, tags):
        raise NotImplementedError


class YouTubeClient(PlatformClient):
    name = "YouTube"      # V4: Google OAuth + YouTube Data API


class FacebookClient(PlatformClient):
    name = "Facebook"     # V5: Meta Graph API


class InstagramClient(PlatformClient):
    name = "Instagram"    # V5: Meta Graph API


class TikTokClient(PlatformClient):
    name = "TikTok"       # V6: Content Posting API


class LinkedInClient(PlatformClient):
    name = "LinkedIn"     # V6: Posts API


CLIENTS = {c.name: c for c in (YouTubeClient, FacebookClient, InstagramClient, TikTokClient, LinkedInClient)}
