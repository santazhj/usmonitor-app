from app.services.x_client import is_substantive_original


def test_original_text_is_substantive():
    tweet = {"text": "$NVDA actively pushing to 800V, big signal today."}

    assert is_substantive_original(tweet)


def test_empty_text_is_not_substantive():
    assert not is_substantive_original({"text": ""})


def test_quote_only_url_is_not_substantive():
    tweet = {
        "text": "https://t.co/example",
        "referenced_tweets": [{"type": "quoted", "id": "1"}],
    }

    assert not is_substantive_original(tweet)


def test_quote_with_original_comment_is_substantive():
    tweet = {
        "text": "This changes the near-term setup for optical suppliers. https://t.co/example",
        "referenced_tweets": [{"type": "quoted", "id": "1"}],
    }

    assert is_substantive_original(tweet)
