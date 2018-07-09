from dlhub_toolbox.models import Dataset

import unittest


class TestModels(unittest.TestCase):

    def test_dataset(self):
        m = Dataset().set_authors(["Ward, Logan"], ["University of Chicago"])\
            .set_title("Example dataset")
        self.assertEqual(m.to_dict(), {"datacite":
                                       {"creators": [{"givenName": "Logan", "familyName": "Ward",
                                                      "affiliations": "University of Chicago"}],
                                        "title": "Example dataset"
                                        }})


if __name__ == "__main__":
    unittest.main()
