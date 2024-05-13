from wspotify import Album


def test_get_album(auth_flow):
    album = Album(auth_flow)
    result = album.get_album("78bpIziExqiI9qztvNFlQu")

    assert result.name == "AM"
    assert result.artists[0].name == "Arctic Monkeys"
    assert len(result.tracks) == result.total_tracks


def test_get_albums(auth_flow):
    album = Album(auth_flow)
    result = album.get_albums(["78bpIziExqiI9qztvNFlQu", "4qApTp9557qYZzRLEih4uP"])

    assert len(result) == 2
    assert result[0].name == "AM"
    assert result[0].total_tracks == 12
    assert result[1].name == "Your Name."
    assert result[1].total_tracks == 27


def test_get_album_tracks(auth_flow):
    album = Album(auth_flow)
    result = album.get_album_tracks("70hX7IYqmUGV97OXs2v848", limit=None)

    assert len(result) == 199
    assert result[0].artists[0].name == "Mac DeMarco"
