import unittest
from types import SimpleNamespace

from app_core.regulatory.anatel_basic import build_basic_form
from app_core.models import Project

class DummyProjectsQuery:
    def __init__(self, size):
        self._size = size
    def count(self):
        return self._size

class DummyUser:
    def __init__(self):
        self.servico = 'FM'
        self.frequencia = 99.5
        self.transmission_power = 10
        self.antenna_gain = 6
        self.total_loss = 1
        self.polarization = 'horizontal'
        self.latitude = -22.9
        self.longitude = -47.0
        self.tower_height = 50
        self.projects = DummyProjectsQuery(2)

class DummyProject(SimpleNamespace):
    pass

class AnatelBasicFormTest(unittest.TestCase):
    def setUp(self):
        self.project = DummyProject(
            name='Projeto Demo',
            description='Teste',
            slug='projeto-demo',
            settings={
                'serviceType': 'FM',
                'frequency': 99.5,
                'towerHeight': 45,
                'tx_location_name': 'Campinas',
            },
            user=DummyUser(),
            created_at=None,
        )

    def test_form_has_19_sections(self):
        sections = build_basic_form(self.project)
        self.assertEqual(len(sections), 19)
        codes = [entry['code'] for entry in sections]
        self.assertIn('01', codes)
        self.assertIn('19', codes)

if __name__ == '__main__':
    unittest.main()
