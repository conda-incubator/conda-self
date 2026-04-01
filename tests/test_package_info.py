from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
from conda.models.records import PrefixRecord

from conda_self.exceptions import NoDistInfoDirFound
from conda_self.package_info import PackageInfo


@dataclass
class FakeCacheRecord:
    name: str
    extracted_package_dir: str
    files: list[str] | None = field(default=None)


@pytest.fixture()
def cache_record(tmp_path):
    def _make(files=None):
        return FakeCacheRecord(
            name="some-plugin",
            extracted_package_dir=str(tmp_path),
            files=files,
        )

    return _make


def test_finds_dist_info_via_record_files(tmp_path, cache_record):
    dist_info = tmp_path / "site-packages/pkg-1.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "entry_points.txt").write_text("[conda]\nplugin = pkg.plugin\n")

    record = cache_record(
        files=[
            "site-packages/pkg-1.0.dist-info/entry_points.txt",
            "site-packages/pkg/__init__.py",
        ]
    )
    infos = PackageInfo.from_record(record)

    assert len(infos) == 1
    assert infos[0].dist_info_path == dist_info
    assert "conda" in infos[0].entry_points()


@pytest.mark.parametrize("manifest", ["info_files", "paths_json"])
def test_finds_dist_info_via_manifest(tmp_path, cache_record, manifest):
    dist_info = tmp_path / "site-packages/pkg-1.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "entry_points.txt").write_text("[conda]\nplugin = pkg.plugin\n")

    info_dir = tmp_path / "info"
    info_dir.mkdir()

    file_paths = [
        "site-packages/pkg-1.0.dist-info/entry_points.txt",
        "site-packages/pkg/__init__.py",
    ]
    if manifest == "paths_json":
        (info_dir / "paths.json").write_text(
            json.dumps(
                {
                    "paths_version": 1,
                    "paths": [
                        {
                            "_path": p,
                            "path_type": "hardlink",
                            "sha256": "x",
                            "size_in_bytes": 1,
                        }
                        for p in file_paths
                    ],
                }
            )
        )
    else:
        (info_dir / "files").write_text("\n".join(file_paths) + "\n")

    infos = PackageInfo.from_record(cache_record())

    assert len(infos) == 1
    assert infos[0].dist_info_path == dist_info
    assert "conda" in infos[0].entry_points()


def test_paths_json_takes_precedence_over_info_files(tmp_path, cache_record):
    """info/paths.json is the canonical source per the conda package CEP."""
    dist_info = tmp_path / "site-packages/real-1.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "entry_points.txt").write_text("[conda]\nplugin = real.p\n")

    info_dir = tmp_path / "info"
    info_dir.mkdir()

    # paths.json points to the real dist-info
    (info_dir / "paths.json").write_text(
        json.dumps(
            {
                "paths_version": 1,
                "paths": [
                    {
                        "_path": "site-packages/real-1.0.dist-info/entry_points.txt",
                        "path_type": "hardlink",
                        "sha256": "abc",
                        "size_in_bytes": 1,
                    },
                ],
            }
        )
    )

    # info/files points to a stale/wrong dist-info
    (info_dir / "files").write_text(
        "site-packages/stale-1.0.dist-info/entry_points.txt\n"
    )

    infos = PackageInfo.from_record(cache_record())

    assert len(infos) == 1
    assert infos[0].dist_info_path == dist_info


@pytest.mark.parametrize(
    "dist_info_relpath",
    [
        "pkg-1.0.dist-info",
        "site-packages/pkg-1.0.dist-info",
    ],
)
def test_filesystem_fallback_finds_dist_info(tmp_path, cache_record, dist_info_relpath):
    dist_info = tmp_path / dist_info_relpath
    dist_info.mkdir(parents=True)
    (dist_info / "entry_points.txt").write_text("[conda]\nplugin = pkg.plugin\n")

    infos = PackageInfo.from_record(cache_record())

    assert len(infos) == 1
    assert infos[0].dist_info_path == dist_info
    assert "conda" in infos[0].entry_points()


def test_no_dist_info_raises(tmp_path, cache_record):
    (tmp_path / "some_file.py").write_text("pass")

    with pytest.raises(NoDistInfoDirFound):
        PackageInfo.from_record(cache_record())


def test_no_fallback_when_manifest_exists(tmp_path, cache_record):
    """rglob must not scan the filesystem when a file manifest was present."""
    dist_info = tmp_path / "unrelated-1.0.dist-info"
    dist_info.mkdir()
    (dist_info / "entry_points.txt").write_text("[conda]\nplugin = x\n")

    info_dir = tmp_path / "info"
    info_dir.mkdir()
    (info_dir / "files").write_text("lib/somefile.py\n")

    with pytest.raises(NoDistInfoDirFound):
        PackageInfo.from_record(cache_record())


def test_no_filesystem_fallback_for_prefix_record(tmp_path):
    """PrefixRecord must never trigger the rglob scan because basedir would
    be the entire prefix, picking up .dist-info dirs from other packages."""
    record = PrefixRecord(
        name="some-clib",
        version="1.0",
        build="0",
        build_number=0,
        extracted_package_dir=str(tmp_path),
    )

    with pytest.raises(NoDistInfoDirFound):
        PackageInfo.from_record(record)


def test_entry_points_missing_file(tmp_path):
    dist_info = tmp_path / "pkg-1.0.dist-info"
    dist_info.mkdir()

    assert PackageInfo(dist_info).entry_points() == {}


def test_entry_points_non_conda(tmp_path):
    dist_info = tmp_path / "pkg-1.0.dist-info"
    dist_info.mkdir()
    (dist_info / "entry_points.txt").write_text(
        "[console_scripts]\npkg = pkg.cli:main\n"
    )

    ep = PackageInfo(dist_info).entry_points()
    assert "conda" not in ep
    assert "console_scripts" in ep
