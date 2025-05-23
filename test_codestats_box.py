import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add the parent directory to sys.path to allow importing codestats_box
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codestats_box import update_gist, GIST_TITLE, DEFAULT_STATS_TYPE
from github.InputFileContent import InputFileContent # Import for type checking

class TestUpdateGist(unittest.TestCase):

    def setUp(self):
        # Set dummy environment variables
        os.environ['GIST_ID'] = 'dummy_gist_id'
        os.environ['GH_TOKEN'] = 'dummy_gh_token'

        # Patch 'codestats_box.Github'
        self.github_patcher = patch('codestats_box.Github')
        self.MockGithub = self.github_patcher.start()
        self.addCleanup(self.github_patcher.stop) # Ensure the patch is stopped after the test

        # Configure the mock Github object
        self.mock_github_instance = self.MockGithub.return_value
        self.mock_gist = MagicMock()
        self.mock_github_instance.get_gist.return_value = self.mock_gist
        
        # Define a mock old_title and initialize gist.files correctly
        self.old_filename = "mock_old_file.md"
        # Initialize gist.files as a dictionary with a mock file object
        # The content here will be the "initial_content" for tests.
        self.mock_gist.files = {self.old_filename: MagicMock(content="initial_content")}

    def test_update_gist_content_different(self):
        # self.mock_gist is already configured by setUp with "initial_content"
        # self.mock_gist.files[self.old_filename].content is already "initial_content"

        new_title = GIST_TITLE[DEFAULT_STATS_TYPE]
        new_content = "new_content" # This is different from "initial_content"

        update_gist(new_title, new_content)

        self.mock_gist.edit.assert_called_once()
        args, kwargs = self.mock_gist.edit.call_args
        self.assertEqual(args[0], new_title)
        self.assertTrue(self.old_filename in args[1])
        file_content_obj = args[1][self.old_filename]
        self.assertIsInstance(file_content_obj, InputFileContent)
        # Try accessing with the name-mangled version based on dir() output
        self.assertEqual(file_content_obj._InputFileContent__content, new_content)

    @patch('builtins.print')
    def test_update_gist_content_same(self, mock_print):
        # self.mock_gist is already configured by setUp with "initial_content"
        # self.mock_gist.files[self.old_filename].content is already "initial_content"

        title = GIST_TITLE[DEFAULT_STATS_TYPE]
        # Call update_gist with the same content as in mock_gist.files
        update_gist(title, "initial_content")

        self.mock_gist.edit.assert_not_called()
        mock_print.assert_any_call("Gist content is already up-to-date. Skipping update.")

if __name__ == '__main__':
    unittest.main()
