from unidiff import PatchSet

from app.utils.util import format_patch_for_display

# Tests for format_patch_for_display function


def test_format_patch_with_added_lines():
    """Test formatting a patch with added lines shows correct markdown and line numbers."""
    git_diff = """diff --git a/main.py b/main.py
index 062670c..eac224e 100644
--- a/main.py
+++ b/main.py
@@ -1,3 +1,6 @@
 from fastapi import FastAPI
+import aiosqlite
+import logging

 app = FastAPI()
+logger = logging.getLogger(__name__)"""

    patch_set = PatchSet(git_diff)
    result = format_patch_for_display(patch_set)

    # Check that markdown formatting is applied
    assert "### `main.py`" in result
    assert "```diff" in result
    assert result.endswith("```\n")

    # Check that added lines are included with correct line numbers
    assert "2    import aiosqlite" in result
    assert "3    import logging" in result
    assert "6    logger = logging.getLogger(__name__)" in result


def test_format_patch_multiple_files():
    """Test formatting patches with multiple files includes both files."""
    git_diff = """diff --git a/main.py b/main.py
index 062670c..eac224e 100644
--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 from fastapi import FastAPI
+import asyncio

 app = FastAPI()
diff --git a/config.py b/config.py
index 1234567..abcdefg 100644
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
 DEBUG = True
+LOG_LEVEL = "INFO"
 PORT = 8000"""

    patch_set = PatchSet(git_diff)
    result = format_patch_for_display(patch_set)

    # Check that both files are included with proper headers
    assert "### `main.py`" in result
    assert "### `config.py`" in result

    # Check content from both files
    assert "2    import asyncio" in result
    assert '2    LOG_LEVEL = "INFO"' in result


def test_format_patch_security_vulnerability_example():
    """Test formatting the actual vulnerable code sample to ensure SQL injection line is captured."""
    git_diff = """diff --git a/main.py b/main.py
index 062670c..eac224e 100644
--- a/main.py
+++ b/main.py
@@ -3,5 +3,6 @@ async def get_user(username: str):
     db = await aiosqlite.connect('users.db')
     cursor = await db.cursor()
+    query = f"SELECT * FROM users WHERE username = '{username}'"
     await cursor.execute(query)
     user = await cursor.fetchone()
     await db.close()"""

    patch_set = PatchSet(git_diff)
    result = format_patch_for_display(patch_set)

    # Check that the vulnerable line is captured with correct line number
    assert "### `main.py`" in result
    assert (
        "5        query = f\"SELECT * FROM users WHERE username = '{username}'"
        in result
    )

    # Verify markdown structure
    assert "```diff" in result
    assert result.count("```") == 2  # Opening and closing
