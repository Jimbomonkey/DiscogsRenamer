from discogs_client import Client, Release, Track, Artist
from discogs_client.exceptions import HTTPError, AuthorizationError

from discogsrenamer.gui.widgets.release_list_item import ReleaseListItem
from discogsrenamer.core.models.release_data import ReleaseData
from discogsrenamer.core.models.track_data import TrackData
from discogsrenamer.core.constants import APP_NAME, APP_VERSION

import re


class DiscogsManager:
    def __init__(self) -> None:
        self._client = Client(
            f"{APP_NAME}/{APP_VERSION} +https://github.com/Jimbomonkey/DiscogsRenamer"
        )

    def get_release(self, release_id: int) -> Release | None:
        release = None
        try:
            release = self._client.release(release_id)
            # A Release object is always returned even if empty
            # To capture a failed fetch, the exception needs to
            # be forced by calling for non-existent data
            _ = release.title
        except AuthorizationError:
            # Subclass of HTTPError, so must be handled first
            return None
        except HTTPError:
            return None
        return release

    def get_release_artists(self, release: Release) -> list[Artist]:
        return list(release.artists)

    def get_release_title(self, release: Release) -> str:
        return release.title

    def get_tracklist(self, release: Release) -> list[Track]:
        return list(release.tracklist)

    def get_track_artists(self, track: Track) -> list[Artist]:
        return list(track.artists)

    def remove_artist_numerical_suffix(self, track_artists: str) -> str:
        return re.sub(r"\s*\(\d+\)", "", track_artists)

    def contains_sub_tracks(self, tracklist: list[Track]) -> bool:
        return any(track.data.get("sub_tracks") for track in tracklist)

    def format_artists(self, track_artists: list[Artist]) -> str:
        track_artists_parts: list[str] = []
        for artist in track_artists:
            artist_without_suffix = self.remove_artist_numerical_suffix(
                str(artist.name)
            )
            # Include join only if it's non-empty
            if artist.join:
                track_artists_parts.append(f"{artist_without_suffix} {artist.join}")
            else:
                track_artists_parts.append(f"{artist_without_suffix}")
        return " ".join(track_artists_parts)

    def get_track_artists_and_titles(
        self, release: Release, tracklist: list[Track]
    ) -> list[ReleaseListItem]:
        artists_and_titles: list[ReleaseListItem] = []
        unformatted_release_artists = self.get_release_artists(release)
        formatted_release_artists = self.format_artists(unformatted_release_artists)

        release_data = ReleaseData(
            release_artists=formatted_release_artists,
            release_title=self.get_release_title(release),
            sub_tracks=self.contains_sub_tracks(tracklist),
        )
        for track in tracklist:
            track_position = str(track.position)
            if track_position:
                track_title = str(track.title)
                unformatted_track_artists = self.get_track_artists(track)
                formatted_track_artists = self.format_artists(unformatted_track_artists)
                if not formatted_track_artists:
                    formatted_track_artists = release_data.release_artists

                track_data = TrackData(
                    release=release_data,
                    track_position=track_position,
                    track_artists=formatted_track_artists,
                    track_title=track_title,
                )

                release_list_item = ReleaseListItem(track_data)
                artists_and_titles.append(release_list_item)

        return artists_and_titles
