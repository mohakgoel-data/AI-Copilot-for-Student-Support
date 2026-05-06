from database.models import ChatMessage


def save_message(
    session,
    user_id,
    role,
    content,
    source_metadata=None
):

    message = ChatMessage(
        user_id=user_id,
        role=role,
        content=content,
        source_metadata=source_metadata
    )

    session.add(message)
    session.commit()

    return message