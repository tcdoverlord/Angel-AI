from __future__ import annotations

from angel.attachments import attachment_context, format_size, prepare_attachments


def test_arbitrary_files_are_accepted_and_text_is_bounded(tmp_path):
    text_file = tmp_path / "notes.txt"
    text_file.write_text("Angel can read this note.", encoding="utf-8")
    image_file = tmp_path / "photo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\nmock")
    unknown_file = tmp_path / "media.customtype"
    unknown_file.write_bytes(b"\x00\x01\x02")

    attachments = prepare_attachments(
        [text_file, image_file, unknown_file, tmp_path / "missing.mp4"]
    )

    assert [item["name"] for item in attachments] == [
        "notes.txt",
        "photo.png",
        "media.customtype",
    ]
    assert attachments[0]["parse_status"] == "text_extracted"
    assert "Angel can read this note" in attachments[0]["text_excerpt"]
    assert attachments[1]["media_kind"] == "image"
    assert attachments[1]["parse_status"] == "metadata_only"
    assert attachments[2]["media_kind"] == "file"

    context = attachment_context(attachments)
    assert "Angel can read this note" in context
    assert "content not parsed" in context
    assert str(tmp_path) not in context


def test_duplicate_files_are_attached_once(tmp_path):
    file_path = tmp_path / "clip.mp4"
    file_path.write_bytes(b"video")
    assert len(prepare_attachments([file_path, file_path])) == 1


def test_human_readable_file_sizes():
    assert format_size(42) == "42 B"
    assert format_size(1536) == "1.5 KB"
