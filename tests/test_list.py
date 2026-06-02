"""Unit tests for reversec.common.list."""

from reversec.common.list import chunk, flatten


class TestChunk:

    def test_splits_into_even_chunks(self):
        assert list(chunk([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]

    def test_final_chunk_may_be_short(self):
        assert list(chunk([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]

    def test_empty_list_yields_nothing(self):
        assert list(chunk([], 2)) == []

    def test_chunk_larger_than_list(self):
        assert list(chunk([1, 2], 10)) == [[1, 2]]


class TestFlatten:

    def test_flattens_nested_lists(self):
        assert list(flatten([1, [2, 3], [4, [5, 6]]])) == [1, 2, 3, 4, 5, 6]

    def test_flattens_tuples(self):
        assert list(flatten([1, (2, 3)])) == [1, 2, 3]

    def test_strings_are_not_flattened(self):
        # Strings are iterable but must be treated as scalar values, otherwise
        # they would be exploded into individual characters.
        assert list(flatten(["ab", ["cd"]])) == ["ab", "cd"]

    def test_empty_list(self):
        assert list(flatten([])) == []
