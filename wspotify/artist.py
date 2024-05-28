from concurrent.futures import as_completed, Future, ThreadPoolExecutor
from enum import Enum
from urllib.parse import urlencode

from httpx import Response

from wspotify.authorization.base import AuthorizationFlow
from wspotify.base import APIReference
from wspotify.schemas import Albums, ArtistData, SimplifiedAlbum, Track
from wspotify.exceptions import ResponseError


class Group(str, Enum):
    ALBUM = "album"
    SINGLE = "single"
    APPEARS_ON = "appears_on"
    COMPILATION = "compilation"


class Artist(APIReference):
    def __init__(self, authorization_flow: AuthorizationFlow) -> None:
        super().__init__(authorization_flow)

    def get_artist(self, id: str) -> ArtistData:
        """Get spotify catalog information for a single artist identified
        by their unique Spotify ID.

        Parameters
        ----------
        id : str
            Spotify ID of the artist

        Returns
        -------
        ArtistData

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-artist
        """
        self.check_access_token()

        response = self.client.get(f"{self.base_url}/artists/{id}")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        return ArtistData(**data)

    def get_artists(self, ids: list[str]) -> list[ArtistData]:
        """Get spotify catalog information for several artists based on
        their Spotify IDs.

        Parameters
        ----------
        ids : list[str]
            List of Spotify IDs for the artists

        Returns
        -------
        list[ArtistData]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-multiple-artists
        """
        self.check_access_token()

        futures: list[Future[Response]] = []
        with ThreadPoolExecutor() as executor:
            # Maximum 100 IDs can be requested at once
            for index in range(0, len(ids), 100):
                params = {"ids": ",".join(ids[index : index + 100])}
                url = f"{self.base_url}/artists?{urlencode(params)}"
                future = executor.submit(self.client.get, url)
                futures.append(future)

        result: list[ArtistData] = []
        for future in as_completed(futures):
            response = future.result()
            data = response.json()
            if response.status_code != 200:
                error = data.get("error", "unknown")
                raise ResponseError(error)

            for artist in data["artists"]:
                result.append(ArtistData(**artist))

        return result

    def get_artist_albums(
        self,
        id: str,
        *,
        include_groups: list[Group] = [],
        market: str | None = None,
        limit: int | None = 20,
        offset: int = 0,
    ) -> list[SimplifiedAlbum]:
        """Get spotify catalog information about an artist's albums.

        Parameters
        ----------
        id : str
            Spotify ID of the artist
        include_groups : list[Group], default=[]
            List of keywords that will be used to filter the response
        market : str | None, default=None
            2 letter country code
        limit : int | None, default=20
            Maximum number of items to return
        offset : int, default=0
            Index of the first item to return

        Returns
        -------
        list[SimplifiedAlbum]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-artists-albums
        """
        self.check_access_token()

        params = {
            "limit": 50 if limit is None else min(limit, 50),
            "offset": offset,
        }
        if include_groups:
            params["include_groups"] = ",".join(group.value for group in Group)
        if market:
            params["market"] = market
        url = f"{self.base_url}/artists/{id}/albums"

        response = self.client.get(f"{url}?{urlencode(params)}")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        albums = Albums(**data)
        result = albums.items

        if (limit is None or limit > 50) and albums.total > 50:
            limit = albums.total if limit is None else limit
            futures: list[Future[Response]] = []
            with ThreadPoolExecutor() as executor:
                for offset in range(50, limit, 50):
                    params["offset"] = offset
                    future = executor.submit(
                        self.client.get, f"{url}?{urlencode(params)}"
                    )
                    futures.append(future)

            for future in as_completed(futures):
                response = future.result()
                data = response.json()
                if response.status_code != 200:
                    error = data.get("error", "unknown")
                    raise ResponseError(error)

                albums = Albums(**data)
                result.extend(albums.items)

        return result

    def get_artist_top_tracks(
        self, id: str, *, market: str | None = None
    ) -> list[Track]:
        """Get spotify catalog information about an artist's top tracks
        by country.

        Parameters
        ----------
        id : str
            Spotify ID of the artist
        market : str | None, default=None
            2 letter country code

        Returns
        -------
        list[Track]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-artists-top-tracks
        """
        self.check_access_token()

        url = f"{self.base_url}/artists/{id}/top-tracks"
        if market:
            url += f"?market={market}"

        response = self.client.get(url)
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        result: list[Track] = []
        for track in data["tracks"]:
            result.append(Track(**track))

        return result

    def get_artist_related_artists(self, id: str) -> list[ArtistData]:
        """Get spotify catalog information about artists similar to a given
        artist. Similarity is based on analysis of the spotify community's
        listening history.

        Parameters
        ----------
        id : str
            Spotify ID of the artist

        Returns
        -------
        list[ArtistData]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-artists-related-artists
        """
        self.check_access_token()

        response = self.client.get(f"{self.base_url}/artists/{id}/related-artists")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        result: list[ArtistData] = []
        for artist in data["artists"]:
            result.append(ArtistData(**artist))

        return result
