import logging
from pathlib import Path

from garminconnect import Garmin, GarminConnectConnectionError

logger = logging.getLogger(__name__)

_DUPLICATE_MARKER = "already exists (duplicate)"


def _prompt_mfa() -> str:
    return input("Enter the Garmin MFA code sent to you: ").strip()


class GarminClient:
    def __init__(self, username: str, password: str, tokenstore: Path):
        self._client = Garmin(username, password, prompt_mfa=_prompt_mfa)
        self._tokenstore = tokenstore

    def login(self) -> None:
        # login(tokenstore) resumes from saved tokens when possible, otherwise
        # does a full login (prompting for MFA) and persists the new tokens
        # to the same directory automatically.
        self._tokenstore.mkdir(parents=True, exist_ok=True)
        self._client.login(str(self._tokenstore))
        logger.info("Garmin login OK (tokens cached in %s)", self._tokenstore)

    def import_fit(self, filepath: Path) -> bool:
        """Upload a FIT file as an import.

        Uses import_activity() instead of upload_activity() so Garmin does not
        re-export the activity to connected third parties (e.g. Strava).

        Returns True on success, False if Garmin reports a duplicate (409).
        """
        try:
            self._client.import_activity(str(filepath))
            return True
        except GarminConnectConnectionError as exc:
            if _DUPLICATE_MARKER in str(exc):
                logger.info("Activity already exists in Garmin, skipping: %s", filepath.stem)
                return False
            raise
