from app.bot.keyboards import (
    commercial_content_keyboard,
    interactions_keyboard,
    privacy_keyboard,
)


def test_privacy_keyboard_contains_only_tiktok_options() -> None:
    keyboard = privacy_keyboard(["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS"])

    callbacks = [row[0].callback_data for row in keyboard.inline_keyboard]
    assert callbacks == ["privacy:SELF_ONLY", "privacy:MUTUAL_FOLLOW_FRIENDS"]


def test_unavailable_interaction_cannot_be_toggled() -> None:
    keyboard = interactions_keyboard(
        allow_comment=False,
        allow_duet=False,
        allow_stitch=False,
        comment_available=True,
        duet_available=False,
        stitch_available=True,
    )

    assert keyboard.inline_keyboard[1][0].callback_data == "interaction:unavailable"


def test_branded_content_is_hidden_for_private_post() -> None:
    keyboard = commercial_content_keyboard(allow_branded_content=False)

    callbacks = [row[0].callback_data for row in keyboard.inline_keyboard]
    assert callbacks == ["commercial:none", "commercial:organic"]
