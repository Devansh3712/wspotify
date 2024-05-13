from concurrent.futures import as_completed, Future, ThreadPoolExecutor
from urllib.parse import urlencode

from httpx import Response

from wspotify.authorization import Scope
from wspotify.authorization.base import AuthorizationFlow
from wspotify.base import APIReference
from wspotify.exceptions import ResponseError
from wspotify.schemas import (
    AlbumData,
    Albums,
    SavedAlbum,
    SimplifiedAlbum,
    SimplifiedTrack,
    Tracks,
    UserSavedAlbums,
)


class Album(APIReference):
    def __init__(self, authorization_flow: AuthorizationFlow) -> None:
        super().__init__(authorization_flow)

    def _get_all_tracks(self, url: str, total: int) -> list[SimplifiedTrack]:
        """Fetch all tracks of an album.

        Parameters
        ----------
        url : str
            Spotify URL of album tracks
        total : int
            Total number of tracks

        Returns
        -------
        list[SimplifiedTrack]
        """
        futures: list[Future[Response]] = []
        params = {"limit": 50}
        with ThreadPoolExecutor() as executor:
            for offset in range(50, total, 50):
                params["offset"] = offset
                future = executor.submit(self.client.get, f"{url}?{urlencode(params)}")
                futures.append(future)

        result: list[SimplifiedTrack] = []
        for future in as_completed(futures):
            response = future.result()
            data = response.json()
            if response.status_code != 200:
                error = data.get("error", "unknown")
                raise ResponseError(error)

            tracks = Tracks(**data)
            result.extend(tracks.items)

        return result

    def get_album(self, id: str, *, market: str | None = None) -> AlbumData:
        """Get spotify catalog information for a single album

        Parameters
        ----------
        id : str
            Spotify ID of the album
        market : str or None, default=None
            2 letter country code

        Returns
        -------
        AlbumData

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-album
        """
        self.check_access_token()

        url = f"{self.base_url}/albums/{id}"
        if market:
            url += f"&market={market}"

        response = self.client.get(url)
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        album = AlbumData(**data)
        tracks_page = album.tracks
        tracks = tracks_page.items

        if tracks_page.total > 50:
            remaining_tracks = self._get_all_tracks(url, tracks_page.total)
            tracks.extend(remaining_tracks)

        album.tracks = tracks
        return album

    def get_albums(
        self, ids: list[str], *, market: str | None = None
    ) -> list[AlbumData]:
        """Get spotify catalog information for multiple albums identified
        by their Spotify IDs.

        Parameters
        ----------
        ids : list[str]
            List of the Spotify IDs for the albums
        market : str or None, default=None
            2 letter country code

        Returns
        -------
        list[AlbumData]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-multiple-albums
        """
        self.check_access_token()

        params: dict[str, str] = {}
        if market:
            params["market"] = market

        # API limits maximum IDs to 20, use a loop to request
        # in chunks of 20. Use multiprocessing to make parallel
        # requests.
        futures: list[Future[Response]] = []
        with ThreadPoolExecutor() as executor:
            for index in range(0, len(ids), 20):
                params["ids"] = ",".join(ids[index : index + 20])
                url = f"{self.base_url}/albums?{urlencode(params)}"
                future = executor.submit(self.client.get, url)
                futures.append(future)

        result: list[AlbumData] = []
        for future in as_completed(futures):
            response = future.result()
            data = response.json()
            if response.status_code != 200:
                error = data.get("error", "unknown")
                raise ResponseError(error)

            for album in data["albums"]:
                result.append(AlbumData(**album))

        return result

    def get_album_tracks(
        self,
        id: str,
        *,
        market: str | None = None,
        limit: int | None = 20,
        offset: int = 0,
    ) -> list[SimplifiedTrack]:
        """Get spotify catalog information about an album's tracks.

        Parameters
        ----------
        id : str
            Spotify ID of the album
        market : str or None, default=None
            2 letter country code
        limit : int or None, default=20
            Maximum number of items to return
            (use None to return all tracks)
        offset : int, default=0
            Index of the first item to return

        Returns
        -------
        list[SimplifiedTrack]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-an-albums-tracks
        """
        self.check_access_token()
        # Maximum value of limit can be 50
        # If all tracks need to be returned (limit=None), set
        # limit to 50 as _get_all_tracks will take lesser iterations
        # else min(limit, 50)
        params = {
            "limit": 50 if limit is None else min(limit, 50),
            "offset": offset,
        }
        if market:
            params["market"] = market
        url = f"{self.base_url}/albums/{id}/tracks"
        # Get total tracks, pass is as the limit for _get_all_tracks
        response = self.client.get(f"{url}?{urlencode(params)}")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        tracks_page = Tracks(**data)
        result = tracks_page.items

        if (limit is None or limit > 50) and tracks_page.total > 50:
            remaining_tracks = self._get_all_tracks(url, tracks_page.total)
            result.extend(remaining_tracks)

        return result

    def get_users_saved_albums(
        self,
        *,
        market: str | None = None,
        limit: int | None = 20,
        offset: int = 0,
    ) -> list[SavedAlbum]:
        """Get a list of the albums saved in the current Spotify user's
        'Your Music' library.

        Parameters
        ----------
        market : str or None, default=None
            2 letter country code
        limit : int, default=20
            Maximum number of items to return
        offset : int, default=0
            Index of the first item to return

        Returns
        -------
        list[SavedAlbum]

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-users-saved-albums
        """
        required_scopes = [Scope.USER_LIBRARY_READ]
        self.check_scopes(required_scopes)
        self.check_access_token()

        params = {
            "limit": 50 if limit is None else min(limit, 50),
            "offset": offset,
        }
        if market:
            params["market"] = market
        url = f"{self.base_url}/me/albums"

        response = self.client.get(f"{url}?{urlencode(params)}")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        albums = UserSavedAlbums(**data)
        result = albums.items

        if (limit is None or limit > 50) and albums.total > 50:
            futures: list[Future[Response]] = []
            with ThreadPoolExecutor() as executor:
                for offset in range(50, albums.total, 50):
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

                albums = UserSavedAlbums(**data)
                result.extend(albums.items)

        return result

    def save_albums_for_user(self, ids: list[str]) -> None:
        """Save one or more albums to the current user's 'Your Music'
        library.

        Parameters
        ----------
        ids : list[str]
            List of Spotify IDs for the albums

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/save-albums-user
        """
        required_scopes = [Scope.USER_LIBRARY_MODIFY]
        self.check_scopes(required_scopes)
        self.check_access_token()

        futures: list[Future[Response]] = []
        with ThreadPoolExecutor() as executor:
            for index in range(0, len(ids), 20):
                body = {"ids": ids[index : index + 20]}
                url = f"{self.base_url}/me/albums"
                future = executor.submit(self.client.put, url, **{"json": body})
                futures.append(future)

        for future in as_completed(futures):
            response = future.result()
            if response.status_code != 200:
                data = response.json()
                error = data.get("error", "unknown")
                raise ResponseError(error)

    def remove_users_saved_albums(self, ids: list[str]) -> None:
        """Remove one or more albums from the current user's 'Your Music'
        library.

        Parameters
        ----------
        ids : list[str]
            List of Spotify IDs for the albums

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/remove-albums-user
        """
        required_scopes = [Scope.USER_LIBRARY_MODIFY]
        self.check_scopes(required_scopes)
        self.check_access_token()

        futures: list[Future[Response]] = []
        with ThreadPoolExecutor() as executor:
            for index in range(0, len(ids), 20):
                body = {"ids": ids[index : index + 20]}
                url = f"{self.base_url}/me/albums"
                future = executor.submit(self.client.delete, url, **{"json": body})
                futures.append(future)

        for future in as_completed(futures):
            response = future.result()
            if response.status_code != 200:
                data = response.json()
                error = data.get("error", "unknown")
                raise ResponseError(error)

    def check_users_saved_albums(self, ids: list[str]) -> dict[str, bool]:
        """Check if one or more albums is already saved in the user's
        'Your Music' library.

        Parameters
        ----------
        ids : list[str]
            List of Spotify IDs for the albums

        Returns
        -------
        dict[str, bool]
            Dictionary with key as album ID and a boolean value whether
            it is saved or not

        Raises
        ------
        ResponseError
            Error while fetching response from API endpoint

        References
        ----------
        .. [1] https://developer.spotify.com/documentation/web-api/reference/check-users-saved-albums
        """
        required_scopes = [Scope.USER_LIBRARY_READ]
        self.check_scopes(required_scopes)
        self.check_access_token()

        result: dict[str, bool] = {}

        futures: list[Future[Response]] = []
        with ThreadPoolExecutor() as executor:
            for index in range(0, len(ids), 20):
                params = {"ids": ",".join(ids[index : index + 20])}
                url = f"{self.base_url}/me/albums/contains?{urlencode(params)}"
                future = executor.submit(self.client.get, url)
                futures.append(future)

        result: dict[str, bool] = {}
        for future in as_completed(futures):
            response = future.result()
            data = response.json()
            if response.status_code != 200:
                error = data.get("error", "unknown")
                raise ResponseError(error)

            for id, exists in zip(ids, data):
                result[id] = exists

        return result

    def get_new_releases(
        self, *, limit: int | None = 20, offset: int = 0
    ) -> list[SimplifiedAlbum]:
        """Get a list of new album releases featured in Spotify.

        Parameters
        ----------
        limit : int or None, default=20
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
        .. [1] https://developer.spotify.com/documentation/web-api/reference/get-new-releases
        """
        self.check_access_token()

        params = {
            "limit": 50 if limit is None else min(limit, 50),
            "offset": offset,
        }
        url = f"{self.base_url}/browse/new-releases"

        response = self.client.get(f"{url}?{urlencode(params)}")
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", "unknown")
            raise ResponseError(error)

        albums = Albums(**data["albums"])
        result = albums.items

        if (limit is None or limit > 50) and albums.total > 50:
            futures: list[Future[Response]] = []
            with ThreadPoolExecutor() as executor:
                for offset in range(50, albums.total, 50):
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

                albums = Albums(**data["albums"])
                result.extend(albums.items)

        return result
