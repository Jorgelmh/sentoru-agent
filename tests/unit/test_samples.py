from pathlib import Path

import pytest
from unidiff import PatchSet

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


@pytest.mark.parametrize("sample", ["sample.diff", "sample_clean.diff"])
def test_sample_is_a_parseable_diff_with_added_lines(sample: str) -> None:
    """Each sample fed to the integration tests is a unified diff that adds code."""
    patch_set = PatchSet((SAMPLES_DIR / sample).read_text())

    assert len(patch_set) > 0
    assert sum(patched_file.added for patched_file in patch_set) > 0
