import tempfile
import unittest
from pathlib import Path

from memory_agent.models import Memory
from memory_agent.storage import MemoryStore


class MemoryStoreTest(unittest.TestCase):
    def test_save_search_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            store = MemoryStore(Path(folder) / "memory.db")
            item = store.save(Memory("用户喜欢中文回答", kind="preference", importance=5))
            self.assertEqual(store.search("中文")[0].id, item.id)
            output = Path(folder) / "export.json"
            store.export_json(output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
