from __future__ import annotations

import hashlib
import io
import json
import tarfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from conda import CondaError
from conda.core.link import UnlinkLinkTransaction
from conda.core.package_cache_data import PackageCacheData
from conda.core.prefix_data import PrefixData
from conda.misc import get_package_records_from_explicit
from conda.models.channel import Channel
from conda.models.enums import NoarchType
from conda.models.records import PackageRecord, PrefixRecord

from conda_self.reset import reset

if TYPE_CHECKING:
    from conda.core.link import PrefixSetup
    from pytest import MonkeyPatch


@pytest.fixture(autouse=True)
def isolated_transactions(tmp_path: Path, tmp_pkgs_dir: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(
        "conda_self.reset.context", SimpleNamespace(quiet=True, json=False)
    )
    monkeypatch.setattr(
        "conda.core.envs_manager.get_user_environments_txt_file",
        lambda *args: str(tmp_path / "environments.txt"),
    )


@pytest.fixture
def package_server(tmp_path: Path):
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Handler, directory=str(tmp_path))
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def make_package(
    root: Path,
    name: str,
    *,
    version: str = "1.0",
    noarch: NoarchType | None = None,
    depends: tuple[str, ...] = (),
    index_name: str | None = None,
) -> tuple[Path, PackageRecord]:
    """Create a small real archive that Conda can extract and link."""
    package_dir = root / "channel" / "noarch"
    package_dir.mkdir(parents=True, exist_ok=True)
    archive = package_dir / f"{name}-{version}-0.tar.bz2"
    index = {
        "name": name,
        "version": version,
        "build": "0",
        "build_number": 0,
        "subdir": "noarch",
        "depends": depends,
    }
    if noarch is not None:
        index["noarch"] = noarch.value
    payload = f"share/{name}.txt"
    members = {
        "info/index.json": json.dumps({**index, "name": index_name or name}).encode(),
        "info/files": f"{payload}\n".encode(),
        payload: b"from snapshot\n",
    }
    with tarfile.open(archive, "w:bz2") as output:
        for name, content in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            output.addfile(member, io.BytesIO(content))
    data = archive.read_bytes()
    return archive, PackageRecord(
        **index,
        channel=Channel(package_dir.parent.as_uri()),
        fn=archive.name,
        url=archive.as_uri(),
        md5=hashlib.md5(data).hexdigest(),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def seed_prefix(prefix: Path, *records: PackageRecord) -> None:
    conda_meta = prefix / "conda-meta"
    conda_meta.mkdir(parents=True)
    (conda_meta / "history").touch()
    for record in records:
        payload = f"share/{record.name}.txt"
        path = prefix / payload
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("already installed\n")
        installed = PrefixRecord.from_objects(record, files=(payload,))
        metadata = conda_meta / f"{record.name}-{record.version}-{record.build}.json"
        metadata.write_text(json.dumps(installed.dump()))


def write_snapshot(
    path: Path, *records: PackageRecord, checksum: str = "sha256"
) -> Path:
    checksum_prefix = "sha256:" if checksum == "sha256" else ""
    entries = (
        f"{record.url}#{checksum_prefix}{getattr(record, checksum)}"
        for record in records
    )
    path.write_text("@EXPLICIT\n" + "\n".join(entries) + "\n")
    return path


def capture_transactions(monkeypatch: MonkeyPatch) -> list[PrefixSetup]:
    setups = []

    def transaction(setup):
        setups.append(setup)
        return UnlinkLinkTransaction(setup)

    monkeypatch.setattr("conda_self.reset.UnlinkLinkTransaction", transaction)
    return setups


def test_unavailable_installed_package_survives_extra_package_removal(
    tmp_path: Path, monkeypatch: MonkeyPatch, tmp_pkgs_dir: Path
):
    archive, retained = make_package(tmp_path, "removed-upstream")
    _, extra = make_package(tmp_path, "extra")
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, retained, extra)
    snapshot = write_snapshot(tmp_path / "snapshot.txt", retained)
    retained_metadata = prefix / "conda-meta" / "removed-upstream-1.0-0.json"
    original_metadata = retained_metadata.read_bytes()
    archive.unlink()
    assert not (tmp_pkgs_dir / retained.fn).exists()
    setups = capture_transactions(monkeypatch)

    def fail_fetch(entries):
        pytest.fail("An unchanged installed package must not be fetched")

    monkeypatch.setattr(
        "conda_self.reset.get_package_records_from_explicit", fail_fetch
    )

    reset(prefix=str(prefix), snapshot=snapshot)

    assert len(setups) == 1
    assert tuple(record.name for record in setups[0].unlink_precs) == ("extra",)
    assert setups[0].link_precs == ()
    assert retained_metadata.read_bytes() == original_metadata
    assert (prefix / "share" / "removed-upstream.txt").read_text() == (
        "already installed\n"
    )
    assert not (prefix / "share" / "extra.txt").exists()
    assert tuple(record.name for record in PrefixData(prefix).iter_records()) == (
        "removed-upstream",
    )


@pytest.mark.parametrize("mismatch", ["url", "md5", "sha256"])
def test_equal_package_identity_is_reinstalled_when_snapshot_does_not_match(
    mismatch: str, tmp_path: Path, monkeypatch: MonkeyPatch
):
    _, target = make_package(tmp_path, "demo")
    different_value = (
        "https://removed.example.test/noarch/demo-1.0-0.tar.bz2"
        if mismatch == "url"
        else "0" * (32 if mismatch == "md5" else 64)
    )
    installed = PackageRecord.from_objects(target, **{mismatch: different_value})
    assert installed == target
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, installed)
    checksum = "md5" if mismatch == "md5" else "sha256"
    snapshot = write_snapshot(tmp_path / "snapshot.txt", target, checksum=checksum)
    setups = capture_transactions(monkeypatch)

    reset(prefix=str(prefix), snapshot=snapshot)

    assert len(setups) == 1
    assert tuple(record.name for record in setups[0].unlink_precs) == ("demo",)
    assert tuple(record.name for record in setups[0].link_precs) == ("demo",)
    assert (prefix / "share" / "demo.txt").read_text() == "from snapshot\n"
    actual = PrefixData(prefix).get("demo")
    assert actual.url == target.url
    assert getattr(actual, checksum) == getattr(target, checksum)


@pytest.mark.parametrize(
    "target_version, relink", [("3.13.2", True), ("3.12.10", False)]
)
def test_python_version_change_prepares_only_packages_that_need_linking(
    target_version: str,
    relink: bool,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    _, installed_python = make_package(tmp_path, "python", version="3.12.9")
    _, target_python = make_package(tmp_path, "python", version=target_version)
    _, noarch_python = make_package(
        tmp_path, "python-tool", noarch=NoarchType.python, depends=("python",)
    )
    _, retained = make_package(tmp_path, "retained")
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, installed_python, noarch_python, retained)
    snapshot = write_snapshot(
        tmp_path / "snapshot.txt", target_python, noarch_python, retained
    )
    setups = []

    class PlannedTransaction:
        def __init__(self, setup):
            setups.append(setup)

        def execute(self):
            pass

    monkeypatch.setattr("conda_self.reset.UnlinkLinkTransaction", PlannedTransaction)

    reset(prefix=str(prefix), snapshot=snapshot)

    assert len(setups) == 1
    expected = {"python", "python-tool"} if relink else {"python"}
    assert {record.name for record in setups[0].unlink_precs} == expected
    assert {record.name for record in setups[0].link_precs} == expected
    for record in setups[0].link_precs:
        assert (Path(record.extracted_package_dir) / "info" / "index.json").is_file()


@pytest.mark.parametrize(
    "transport, failure",
    [
        ("http", "missing"),
        ("http", "md5"),
        ("http", "sha256"),
        ("file", "md5"),
        ("file", "sha256"),
        ("http", "corrupt"),
        ("http", "index"),
    ],
)
def test_package_preparation_failure_does_not_start_a_transaction(
    transport: str,
    failure: str,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    package_server: str,
):
    archive, required = make_package(
        tmp_path, "required", index_name="different" if failure == "index" else None
    )
    if transport == "http":
        required = PackageRecord.from_objects(
            required,
            url=f"{package_server}/channel/noarch/{archive.name}",
            channel=Channel(f"{package_server}/channel"),
        )
    _, extra = make_package(tmp_path, "extra")
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, extra)
    if failure == "missing":
        archive.unlink()
    elif failure in ("md5", "sha256"):
        required = PackageRecord.from_objects(
            required, **{failure: "0" * (32 if failure == "md5" else 64)}
        )
    elif failure == "corrupt":
        archive.write_bytes(b"not a package archive")
        required = PackageRecord.from_objects(
            required, sha256=hashlib.sha256(archive.read_bytes()).hexdigest()
        )
    snapshot = write_snapshot(
        tmp_path / "snapshot.txt",
        required,
        checksum="md5" if failure == "md5" else "sha256",
    )
    before = {
        path.relative_to(prefix): path.read_bytes()
        for path in prefix.rglob("*")
        if path.is_file()
    }

    def fail_transaction(setup):
        pytest.fail("Package preparation failed before transaction creation")

    monkeypatch.setattr("conda_self.reset.UnlinkLinkTransaction", fail_transaction)

    with pytest.raises(CondaError, match="target environment was not changed"):
        reset(prefix=str(prefix), snapshot=snapshot)

    assert {
        path.relative_to(prefix): path.read_bytes()
        for path in prefix.rglob("*")
        if path.is_file()
    } == before


def test_extracted_package_cache_can_supply_an_unavailable_archive(tmp_path: Path):
    archive, required = make_package(tmp_path, "required")
    _, extra = make_package(tmp_path, "extra")
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, extra)
    snapshot = write_snapshot(tmp_path / "snapshot.txt", required)
    (cached,) = get_package_records_from_explicit(snapshot.read_text().splitlines())
    archive.unlink()
    Path(cached.package_tarball_full_path).unlink()

    reset(prefix=str(prefix), snapshot=snapshot)

    assert (prefix / "share" / "required.txt").read_text() == "from snapshot\n"
    assert not (prefix / "share" / "extra.txt").exists()
    assert tuple(record.name for record in PrefixData(prefix).iter_records()) == (
        "required",
    )


@pytest.mark.parametrize("checksum", ["md5", "sha256"])
def test_rejected_local_checksums_remain_rejected_after_archive_removal(
    checksum: str,
    tmp_path: Path,
    tmp_pkgs_dir: Path,
    monkeypatch: MonkeyPatch,
):
    packages = [make_package(tmp_path, name) for name in ("first", "second")]
    _, extra = make_package(tmp_path, "extra")
    prefix = tmp_path / "prefix"
    seed_prefix(prefix, extra)
    incorrect_records = [
        PackageRecord.from_objects(
            record, **{checksum: "0" * (32 if checksum == "md5" else 64)}
        )
        for _, record in packages
    ]
    snapshot = write_snapshot(
        tmp_path / "snapshot.txt", *incorrect_records, checksum=checksum
    )
    before = {
        path.relative_to(prefix): path.read_bytes()
        for path in prefix.rglob("*")
        if path.is_file()
    }
    setups = capture_transactions(monkeypatch)

    with pytest.raises(CondaError, match="target environment was not changed"):
        reset(prefix=str(prefix), snapshot=snapshot)

    cached_records = {
        record.name: record for record in PackageCacheData(tmp_pkgs_dir).iter_records()
    }
    for archive, record in packages:
        cached = cached_records[record.name]
        assert getattr(cached, checksum) == getattr(record, checksum)
        metadata = Path(cached.extracted_package_dir) / "info" / "repodata_record.json"
        assert json.loads(metadata.read_text())[checksum] == getattr(record, checksum)
        archive.unlink()
        Path(cached.package_tarball_full_path).unlink()
    PackageCacheData._cache_.pop(str(tmp_pkgs_dir), None)

    with pytest.raises(CondaError, match="target environment was not changed"):
        reset(prefix=str(prefix), snapshot=snapshot)

    assert setups == []
    assert {
        path.relative_to(prefix): path.read_bytes()
        for path in prefix.rglob("*")
        if path.is_file()
    } == before

    write_snapshot(snapshot, *(record for _, record in packages), checksum=checksum)
    reset(prefix=str(prefix), snapshot=snapshot)

    assert len(setups) == 1
    assert {record.name for record in PrefixData(prefix).iter_records()} == {
        "first",
        "second",
    }
    for _, record in packages:
        assert (prefix / "share" / f"{record.name}.txt").read_text() == (
            "from snapshot\n"
        )
    assert not (prefix / "share" / "extra.txt").exists()
