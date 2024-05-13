from wspotify import Artist


def test_get_artist(auth_flow):
    artist = Artist(auth_flow)
    result = artist.get_artist("2oBG74gAocPMFv6Ij9ykdo")

    assert result.name == "Seedhe Maut"


def test_get_artists(auth_flow):
    artist = Artist(auth_flow)
    result = artist.get_artists(
        ["6qtADmCOQ6a9NlpMULzJj9", "1OVeQPd27s1MkICbzBfZTV"],
    )

    assert result[0].name == "Arpit Bala"
    assert result[1].name == "Dhanji"


def test_get_artist_albums(auth_flow):
    artist = Artist(auth_flow)
    result = artist.get_artist_albums("7FvX2e6CgYllzgZ9uempWF", limit=None)

    assert "Qabool Hai (Deluxe)" in [album.name for album in result]


def test_get_artist_top_tracks(auth_flow):
    artist = Artist(auth_flow)
    result = artist.get_artist_top_tracks("7FvX2e6CgYllzgZ9uempWF")

    assert "Maharani" in [track.name for track in result]


def test_get_artist_related_artists(auth_flow):
    artist = Artist(auth_flow)
    result = artist.get_artist_related_artists("23wbNK1vHjiDSUXnJFWoSu")

    assert "Foosie Gang" in [artist.name for artist in result]
