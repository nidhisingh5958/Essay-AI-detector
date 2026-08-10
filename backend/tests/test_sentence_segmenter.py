from app.services.sentence_segmenter import segment_sentences


def test_empty_input_returns_no_sentences():
    assert segment_sentences("") == []


def test_whitespace_only_input_returns_no_sentences():
    assert segment_sentences("   \n\t  ") == []


def test_single_short_sentence():
    sentences = segment_sentences("I love writing.")
    assert len(sentences) == 1
    assert sentences[0].text == "I love writing."
    assert sentences[0].index == 0


def test_multiple_sentences_are_split_and_indexed_in_order():
    text = "First sentence. Second sentence. Third sentence."
    sentences = segment_sentences(text)
    assert [s.text for s in sentences] == [
        "First sentence.",
        "Second sentence.",
        "Third sentence.",
    ]
    assert [s.index for s in sentences] == [0, 1, 2]


def test_sentence_offsets_correctly_slice_the_original_text():
    text = "First sentence. Second sentence."
    sentences = segment_sentences(text)
    for sentence in sentences:
        assert text[sentence.start_char : sentence.end_char] == sentence.text


def test_abbreviations_do_not_cause_false_sentence_breaks():
    text = "Dr. Smith argued that the U.S. economy would recover. She was right."
    sentences = segment_sentences(text)
    assert len(sentences) == 2
    assert sentences[0].text.startswith("Dr. Smith")
    assert sentences[1].text == "She was right."


def test_punctuation_heavy_text():
    text = "Wait... really?! Yes!!! Or is it?"
    sentences = segment_sentences(text)
    assert len(sentences) >= 3
    joined = " ".join(s.text for s in sentences)
    assert "really" in joined and "Yes" in joined


def test_unicode_text_with_accents_and_emoji():
    text = "Café society fascinated her. She smiled 😊 and kept writing résumés."
    sentences = segment_sentences(text)
    assert len(sentences) == 2
    assert "Café" in sentences[0].text
    assert "😊" in sentences[1].text


def test_duplicate_sentences_are_each_segmented_separately():
    text = "I worked hard. I worked hard. I worked hard."
    sentences = segment_sentences(text)
    assert len(sentences) == 3
    assert all(s.text == "I worked hard." for s in sentences)
    assert [s.index for s in sentences] == [0, 1, 2]


def test_repeated_phrases_across_different_sentences():
    text = (
        "In conclusion, I learned resilience. "
        "In conclusion, I learned patience. "
        "In conclusion, I learned humility."
    )
    sentences = segment_sentences(text)
    assert len(sentences) == 3
    assert all(s.text.startswith("In conclusion,") for s in sentences)


def test_long_essay_segments_without_error():
    paragraph = "This is a sentence about my experience. It taught me a lot. "
    text = paragraph * 200  # ~2,800 words
    sentences = segment_sentences(text)
    assert len(sentences) == 400
