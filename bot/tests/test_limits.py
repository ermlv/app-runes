"""Тесты чистой логики лимитов — bot/limits.py (Task 1)."""

NOW = 1_700_000_000


def test_can_draw_free_quota():
    import limits
    assert limits.can_draw(0, 0, NOW) is True
    assert limits.can_draw(1, 0, NOW) is True
    assert limits.can_draw(2, 0, NOW) is False


def test_premium_overrides_limit():
    import limits
    assert limits.can_draw(99, NOW + 100, NOW) is True   # премиум снят с лимита
    assert limits.can_draw(2, NOW - 1, NOW) is False      # премиум истёк
    assert limits.can_draw(2, NOW, NOW) is False          # граница: now < until


def test_is_premium_boundary():
    import limits
    assert limits.is_premium(NOW, NOW) is False
    assert limits.is_premium(NOW + 1, NOW) is True


def test_remaining():
    import limits
    assert limits.remaining(0) == 2
    assert limits.remaining(1) == 1
    assert limits.remaining(5) == 0


def test_extend_premium_stacks_from_current_until():
    import limits
    assert limits.extend_premium(0, NOW) == NOW + 7 * 86400
    # стак: активный премиум продлевается от его срока, а не от now
    assert limits.extend_premium(NOW + 3 * 86400, NOW) == NOW + 10 * 86400
    # истёкший — от now
    assert limits.extend_premium(NOW - 100, NOW) == NOW + 7 * 86400
