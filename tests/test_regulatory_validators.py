import unittest

from app_core.regulatory.validators.decea_validator import DECEAValidator
from app_core.regulatory.validators.rni_validator import RNIValidator
from app_core.regulatory.validators.servico_validator import ServiceValidator
from app_core.regulatory.validators.sarc_validator import SARCValidator


class RegulatoryValidatorsTest(unittest.TestCase):
    def setUp(self):
        self.payload = {
            'estacao': {'servico': 'FM', 'classe': 'B1', 'canal': '200'},
            'sistema_irradiante': {
                'potencia_w': 10,
                'ganho_tx_dbi': 6,
                'perdas_db': 1,
                'polarizacao': 'horizontal',
            },
            'pilar_decea': {'coordenadas': {'lat': -22.9, 'lon': -47.0}, 'altura': 80, 'pbzpa': {'classe': 'PBZPA', 'protocolo': '123'}},
            'pilar_rni': {'classificacao': 'ocupacional', 'distancia_m': 5},
            'sarc': [{'identificacao': 'Link 1', 'frequencia_mhz': 6000, 'distancia_km': 12, 'potencia_dbm': 30, 'ganho_tx_dbi': 20, 'ganho_rx_dbi': 20}],
        }

    def test_decea_validator(self):
        result = DECEAValidator().validate(self.payload)
        self.assertEqual(result.pillar, 'decea')
        self.assertIn(result.status, {'approved', 'attention'})
        self.assertIn('pbzpa', result.metrics)

    def test_rni_validator(self):
        result = RNIValidator().validate(self.payload)
        self.assertEqual(result.pillar, 'rni')
        self.assertIn('density_w_m2', result.metrics)

    def test_servico_validator(self):
        result = ServiceValidator().validate(self.payload)
        self.assertEqual(result.pillar, 'servico')
        self.assertIn('erp_kw', result.metrics)

    def test_sarc_validator(self):
        result = SARCValidator().validate(self.payload)
        self.assertEqual(result.pillar, 'sarc')
        self.assertIn('links', result.metrics)


if __name__ == '__main__':
    unittest.main()
