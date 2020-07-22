import aiohttp


class CodeforcesAPI:
    def __init__(self):
        self.handle = ""
        self.url = ""

    async def api_response(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as resp:
                    response = await resp.json()
                    return response
        except Exception:
            return None

    async def check_handle(self, handle):
        self.handle = handle
        self.url = "https://codeforces.com/api/user.info?handles=%s" % self.handle
        response = await self.api_response()
        if not response:
            return [False, "Codeforces API Error"]
        if response["status"] != "OK":
            return [False, "Handle not found."]
        else:
            data = response["result"][0]
            if "rating" not in data:
                return [False, "User did not participate in any rated contest."]
            else:
                return [True]

    async def get_rating(self, user):
        self.handle = user
        self.url = "https://codeforces.com/api/user.info?handles=%s" % self.handle
        response = await self.api_response()
        return response["result"][0]["rating"]

    async def get_ratings(self, users):
        self.handle = ";".join(users)
        self.url = "https://codeforces.com/api/user.info?handles=%s" % self.handle
        response = await self.api_response()
        return [res["rating"] for res in response["result"]]

    async def get_best_rating(self, user):
        self.handle = user
        self.url = "https://codeforces.com/api/user.info?handles=%s" % self.handle
        response = await self.api_response()
        return response["result"][0]["maxRating"]

    async def get_first_name(self, user):
        self.handle = user
        self.url = "https://codeforces.com/api/user.info?handles=%s" % self.handle
        response = await self.api_response()
        if not response or "firstName" not in response["result"][0]:
            return None
        return response["result"][0]["firstName"]

    async def get_rating_changes(self, handle, top10=True):
        self.handle = handle
        self.url = "https://codeforces.com/api/user.rating?handle=%s" % self.handle
        response = await self.api_response()
        if not response:
            return None
        else:
            changes = response["result"][::-1]
            if top10:
                changes = changes[:10]
            return [(k["contestName"], k["oldRating"], k["newRating"], k["ratingUpdateTimeSeconds"]) for k in changes]
