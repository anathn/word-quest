# Testing Traps

Known pitfalls in this codebase's test setup and how to avoid them.

---

## `pygame.quit()` in test teardowns kills the xdist worker

**What broke:** Tests ran fine on `main` (serial), but after adding `-n 2 --dist=loadfile` to `pytest.ini`, the CI job hung for 6 hours until GitHub Actions timed it out. One pytest-xdist worker (`gw0`) was dying with "Not properly terminated."

**Why:** Each xdist worker is a separate process. `conftest.py` initializes pygame once when the worker starts. Any test teardown that calls `pygame.quit()` shuts down SDL for that entire worker process. When the next test in that worker calls `pygame.init()` against the headless SDL dummy drivers in CI, the process hangs or segfaults — and the pytest master waits forever for it to finish.

**Rule:** Never call `pygame.quit()` in a test teardown, fixture cleanup, or inline at the end of a test method. `conftest.py` owns the pygame lifecycle for the session.

```python
# BAD
def teardown_method(self):
    reset_theme()
    pygame.quit()  # kills the worker

# GOOD
def teardown_method(self):
    reset_theme()
```

Calling `pygame.init()` inside a test method is harmless (it's a no-op if pygame is already initialized), but `pygame.quit()` anywhere in test code is not safe with xdist.

---

## Replacing `sys.modules['pygame']` without restoring it

**What broke:** The `TestSoundManager` fixture in `tests/test_audio_sfx.py` swapped the real `pygame` module for a `MagicMock`, then did `del sys.modules['pygame']` on cleanup. This left the worker without `pygame` in `sys.modules`, so any later `import pygame` in the same worker would re-import a fresh, uninitialized copy.

**Rule:** When patching a module in `sys.modules`, always save and restore the original.

```python
# BAD
sys.modules['pygame'] = mock_pygame
yield manager
del sys.modules['pygame']

# GOOD
original = sys.modules.get('pygame')
sys.modules['pygame'] = mock_pygame
yield manager
if original is not None:
    sys.modules['pygame'] = original
else:
    sys.modules.pop('pygame', None)
```

Prefer `unittest.mock.patch` or `pytest-mock`'s `mocker.patch` when possible — they handle save/restore automatically.
