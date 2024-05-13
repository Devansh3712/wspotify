from pydantic import BaseModel


class ExternalURLs(BaseModel):
    spotify: str


class Image(BaseModel):
    url: str
    height: int | None = None
    width: int | None = None


class Restrictions(BaseModel):
    reason: str


class SimplifiedArtist(BaseModel):
    external_urls: ExternalURLs
    href: str
    id: str
    name: str
    type: str
    uri: str


class Followers(BaseModel):
    href: str | None = None
    total: int


class ArtistData(SimplifiedArtist):
    followers: Followers
    genres: list[str]
    images: list[Image]
    popularity: int


class LinkedFrom(BaseModel):
    external_urls: ExternalURLs
    href: str
    id: str
    type: str
    uri: str


class SimplifiedTrack(BaseModel):
    artists: list[SimplifiedArtist]
    available_markets: list[str] = []
    disc_number: int
    duration_ms: int
    explicit: bool
    external_urls: ExternalURLs
    href: str
    id: str
    is_playable: bool = False
    linked_from: LinkedFrom | None = None
    restrictions: Restrictions | None = None
    name: str
    preview_url: str | None = None
    track_number: int
    type: str
    uri: str
    is_local: bool


class Page(BaseModel):
    href: str
    limit: int
    next: str | None = None
    offset: int
    previous: str | None = None
    total: int


class Tracks(Page):
    items: list[SimplifiedTrack]


class Copyright(BaseModel):
    text: str
    type: str


class ExternalIDs(BaseModel):
    isrc: str | None = None
    ean: str | None = None
    upc: str | None = None


class SimplifiedAlbum(BaseModel):
    album_type: str
    total_tracks: int
    available_markets: list[str] = []
    external_urls: ExternalURLs
    href: str
    id: str
    images: list[Image]
    name: str
    release_date: str
    release_date_precision: str
    restrictions: Restrictions | None = None
    type: str
    uri: str
    artists: list[SimplifiedArtist]


class AlbumData(SimplifiedAlbum):
    tracks: Tracks | list[SimplifiedTrack]
    copyrights: list[Copyright]
    external_ids: ExternalIDs
    genres: list[str]
    label: str
    popularity: int


class SavedAlbum(BaseModel):
    added_at: str
    album: AlbumData


class UserSavedAlbums(Page):
    items: list[SavedAlbum]


class Albums(Page):
    items: list[SimplifiedAlbum]


class Track(SimplifiedTrack):
    album: SimplifiedAlbum
    external_ids: ExternalIDs
    popularity: int
