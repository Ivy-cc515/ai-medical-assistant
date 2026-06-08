import os
import urllib.parse
import urllib.request
import json


class ClinicService:
    """
    階段四：實體資源對接
    使用 Google Maps Places API 搜尋附近診所。
    需要設定環境變數 GOOGLE_MAPS_API_KEY。
    """

    PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_API_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")

    def find_nearby_clinics(
        self,
        department: str,
        location: str,
        max_results: int = 3,
    ) -> list[dict]:
        """
        搜尋指定地點附近、符合科別的診所。

        Parameters
        ----------
        department : str   推薦科別，例如 "耳鼻喉科"
        location   : str   行政區或地址，例如 "台北市大安區"
        max_results: int   最多回傳幾筆

        Returns
        -------
        list of dict，每筆包含：
            name, address, rating, open_now, maps_url
        """
        if not self.api_key:
            # 未設定 API Key 時回傳 mock 資料，方便開發測試
            return self._mock_results(department, location)

        query = f"{location} {department} 診所"
        params = urllib.parse.urlencode({
            "query": query,
            "language": "zh-TW",
            "key": self.api_key,
        })

        try:
            with urllib.request.urlopen(
                f"{self.PLACES_API_URL}?{params}", timeout=5
            ) as resp:
                data = json.loads(resp.read().decode())

            results = data.get("results", [])[:max_results]
            clinics = []

            for place in results:
                place_id = place.get("place_id", "")
                clinics.append({
                    "name": place.get("name", ""),
                    "address": place.get("formatted_address", ""),
                    "rating": place.get("rating", "N/A"),
                    "open_now": (
                        place.get("opening_hours", {}).get("open_now", None)
                    ),
                    "maps_url": (
                        f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                        if place_id else ""
                    ),
                })

            return clinics

        except Exception as e:
            # API 呼叫失敗時靜默降級，回傳空清單
            print(f"[ClinicService] Google Maps API error: {e}")
            return []

    @staticmethod
    def _mock_results(department: str, location: str) -> list[dict]:
        """開發用 mock 資料（未設定 GOOGLE_MAPS_API_KEY 時使用）"""
        return [
            {
                "name": f"範例{department}診所（Mock）",
                "address": f"{location}某路1號",
                "rating": 4.5,
                "open_now": True,
                "maps_url": "https://maps.google.com",
            },
            {
                "name": f"聯合{department}醫療院所（Mock）",
                "address": f"{location}某路99號",
                "rating": 4.2,
                "open_now": True,
                "maps_url": "https://maps.google.com",
            },
        ]