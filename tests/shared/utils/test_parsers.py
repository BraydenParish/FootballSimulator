from pathlib import Path

from shared.utils.parsers import parse_ratings


def test_parse_ratings_handles_non_ascii(tmp_path: Path) -> None:
    fixture_src = Path(__file__).parent / "fixtures" / "ratings_non_ascii.txt"
    fixture_dst = tmp_path / "ratings.txt"
    fixture_dst.write_bytes(fixture_src.read_bytes())

    players = parse_ratings(fixture_dst)

    assert players == [
        {
            "id": 1,
            "name": "José Pérez",
            "position": "QB",
            "overall_rating": 90,
            "team_abbr": "MEX",
            "age": 29,
        }
    ]
