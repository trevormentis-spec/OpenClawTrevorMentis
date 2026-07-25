from prosebench.rubric import RubricLoader


def test_all_profiles_load_and_total_100() -> None:
    loader = RubricLoader()
    assert loader.available_profiles() == [
        "academic_argument",
        "narrative_nonfiction",
        "professional_prose",
    ]
    for name in loader.available_profiles():
        profile = loader.load(name)
        assert len(profile.criteria) == 12
        assert sum(item.weight for item in profile.criteria) == 100
        assert len({item.criterion_id for item in profile.criteria}) == 12
